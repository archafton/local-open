#!/usr/bin/env python3
"""
Member enrichment script - associates members with bills they've sponsored or cosponsored.
Only processes bills that already exist in the database.
"""

import os
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set

# Import utilities
from congressgov.utils.logging_config import setup_logging
from congressgov.utils.api import APIClient, RetryStrategy
from congressgov.utils.database import get_db_connection, with_db_transaction
from congressgov.utils.file_storage import ensure_directory, save_json, cleanup_old_files

# Set up logging
logger = setup_logging(__name__)

# API configuration
BASE_API_URL = "https://api.congress.gov/v3"
SPONSORED_ENDPOINT = "member/{bioguideId}/sponsored-legislation"
COSPONSORED_ENDPOINT = "member/{bioguideId}/cosponsored-legislation"
SYNC_STATUS_TABLE = "api_sync_status"
API_CALL_DELAY = 1  # Seconds to wait between API calls
SYNC_STATUS_SUCCESS = 'success'
SYNC_STATUS_FAILED = 'failed'
SYNC_STATUS_IN_PROGRESS = 'in_progress'
RAW_DATA_RETENTION_DAYS = 30

class MemberEnrichment:
    """Handles enriching member data with sponsored and cosponsored legislation."""
    
    def __init__(self, api_client: APIClient):
        """Initialize with API client."""
        self.api_client = api_client
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.raw_dir = ensure_directory(os.path.dirname(__file__), 'raw', self.timestamp)
        
        # Cache of bill IDs from database
        self.existing_bills = self._get_existing_bills()
        logger.info(f"Loaded {len(self.existing_bills)} existing bills from database")
        
    def _get_existing_bills(self) -> Dict[str, int]:
        """Get dictionary of existing bill numbers mapped to their IDs."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, bill_number FROM bills")
                return {row[1]: row[0] for row in cur.fetchall()}
                
    def fetch_sponsored_legislation(self, bioguide_id: str, from_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch sponsored legislation for a member."""
        endpoint = SPONSORED_ENDPOINT.format(bioguideId=bioguide_id)
        params = {
            'sort': 'updateDate desc'
        }
        
        if from_date:
            params['fromDateTime'] = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            
        logger.info(f"Fetching sponsored legislation for member {bioguide_id}")
        return self.api_client.get_paginated(endpoint, params, 'sponsoredLegislation')
        
    def fetch_cosponsored_legislation(self, bioguide_id: str, from_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch cosponsored legislation for a member."""
        endpoint = COSPONSORED_ENDPOINT.format(bioguideId=bioguide_id)
        params = {
            'sort': 'updateDate desc'
        }
        
        if from_date:
            params['fromDateTime'] = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            
        logger.info(f"Fetching cosponsored legislation for member {bioguide_id}")
        return self.api_client.get_paginated(endpoint, params, 'cosponsoredLegislation')
        
    def save_legislation_data(self, data: List[Dict[str, Any]], bioguide_id: str, data_type: str) -> str:
        """Save legislation data to a JSON file."""
        dir_path = ensure_directory(self.raw_dir, bioguide_id)
        filename = f"{data_type}_{bioguide_id}.json"
        
        return save_json({data_type: data}, dir_path, filename)
        
    @with_db_transaction
    def update_sponsored_legislation(self, cursor, member_id: int, data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Update sponsored legislation relationships for a member."""
        stats = {"processed": 0, "associated": 0, "skipped": 0}
        
        for item in data:
            stats["processed"] += 1
            
            # Skip amendments for now as they require different handling
            if 'amendmentNumber' in item:
                continue
                
            # Create the bill number
            bill_type = item.get('type', '')
            bill_number = f"{bill_type}{item.get('number', '')}"
            
            # Skip if bill not in database
            if bill_number not in self.existing_bills:
                logger.debug(f"Skipping bill {bill_number} - not in database")
                stats["skipped"] += 1
                continue
                
            bill_id = self.existing_bills[bill_number]
            introduced_date = item.get('introducedDate')
            
            # Insert sponsored legislation relationship
            cursor.execute("""
                INSERT INTO sponsored_legislation (
                    member_id, bill_id, introduced_date
                ) VALUES (%s, %s, %s)
                ON CONFLICT (member_id, bill_id) DO NOTHING
            """, (
                member_id,
                bill_id,
                introduced_date
            ))
            
            stats["associated"] += 1
            
        return stats
        
    @with_db_transaction
    def update_cosponsored_legislation(self, cursor, member_id: int, data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Update cosponsored legislation relationships for a member."""
        stats = {"processed": 0, "associated": 0, "skipped": 0}
        
        for item in data:
            stats["processed"] += 1
            
            # Create the bill number
            bill_type = item.get('type', '')
            bill_number = f"{bill_type}{item.get('number', '')}"
            
            # Skip if bill not in database
            if bill_number not in self.existing_bills:
                logger.debug(f"Skipping bill {bill_number} - not in database")
                stats["skipped"] += 1
                continue
                
            bill_id = self.existing_bills[bill_number]
            cosponsored_date = item.get('cosponsorDate') or datetime.now().strftime('%Y-%m-%d')
            
            # Insert cosponsored legislation relationship
            cursor.execute("""
                INSERT INTO cosponsored_legislation (
                    member_id, bill_id, cosponsored_date
                ) VALUES (%s, %s, %s)
                ON CONFLICT (member_id, bill_id) DO NOTHING
            """, (
                member_id,
                bill_id,
                cosponsored_date
            ))
            
            # Get member info for cosponsor record
            cursor.execute("""
                SELECT bioguide_id, full_name, party, state, chamber, district
                FROM members WHERE id = %s
            """, (member_id,))
            member_info = cursor.fetchone()
            
            if member_info:
                # Update bill_cosponsors table
                cursor.execute("""
                    INSERT INTO bill_cosponsors (
                        bill_number, cosponsor_id, cosponsor_name,
                        cosponsor_party, cosponsor_state, cosponsor_chamber,
                        cosponsor_district, cosponsor_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (bill_number, cosponsor_id) DO UPDATE SET
                        cosponsor_name = EXCLUDED.cosponsor_name,
                        cosponsor_party = EXCLUDED.cosponsor_party,
                        cosponsor_state = EXCLUDED.cosponsor_state,
                        cosponsor_chamber = EXCLUDED.cosponsor_chamber,
                        cosponsor_district = EXCLUDED.cosponsor_district,
                        cosponsor_date = EXCLUDED.cosponsor_date
                """, (
                    bill_number,
                    member_info[0],  # bioguide_id
                    member_info[1],  # full_name
                    member_info[2],  # party
                    member_info[3],  # state
                    member_info[4],  # chamber
                    member_info[5],  # district
                    cosponsored_date
                ))
            
            stats["associated"] += 1
            
        return stats
        
    def process_member(self, bioguide_id: str, from_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Process a single member, enriching with sponsored and cosponsored legislation."""
        results = {
            "bioguide_id": bioguide_id,
            "status": "success",
            "sponsored": {"processed": 0, "associated": 0, "skipped": 0},
            "cosponsored": {"processed": 0, "associated": 0, "skipped": 0}
        }
        
        try:
            # Get member ID
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM members WHERE bioguide_id = %s", (bioguide_id,))
                    result = cur.fetchone()
                    if not result:
                        logger.warning(f"Member {bioguide_id} not found in database")
                        results["status"] = "failed"
                        results["error"] = "Member not found in database"
                        return results
                    member_id = result[0]
                    
            # Fetch and process sponsored legislation
            sponsored_data = self.fetch_sponsored_legislation(bioguide_id, from_date)
            if sponsored_data:
                self.save_legislation_data(sponsored_data, bioguide_id, 'sponsored')
                results["sponsored"] = self.update_sponsored_legislation(member_id, sponsored_data)
                logger.info(f"Processed {len(sponsored_data)} sponsored bills for {bioguide_id}")
                
            # Fetch and process cosponsored legislation
            cosponsored_data = self.fetch_cosponsored_legislation(bioguide_id, from_date)
            if cosponsored_data:
                self.save_legislation_data(cosponsored_data, bioguide_id, 'cosponsored')
                results["cosponsored"] = self.update_cosponsored_legislation(member_id, cosponsored_data)
                logger.info(f"Processed {len(cosponsored_data)} cosponsored bills for {bioguide_id}")
                
            # Update member's last_updated timestamp
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE members 
                        SET last_updated = CURRENT_TIMESTAMP 
                        WHERE id = %s
                    """, (member_id,))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error processing member {bioguide_id}: {str(e)}", exc_info=True)
            results["status"] = "failed"
            results["error"] = str(e)
            
        return results

def get_members_for_processing(recent_only: bool = True, days: int = 7, limit: int = 100) -> List[str]:
    """Get members to process, either recently updated or all."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if recent_only:
                # Get members updated in the last N days
                cutoff_date = datetime.now() - timedelta(days=days)
                cur.execute("""
                    SELECT bioguide_id 
                    FROM members 
                    WHERE last_updated >= %s AND current_member = true
                    ORDER BY last_updated ASC
                    LIMIT %s
                """, (cutoff_date, limit))
            else:
                # Get oldest updated members that are current
                cur.execute("""
                    SELECT bioguide_id 
                    FROM members 
                    WHERE current_member = true
                    ORDER BY last_updated ASC NULLS FIRST
                    LIMIT %s
                """, (limit,))
            
            return [row[0] for row in cur.fetchall()]

def update_sync_status(status: str, processed: int = 0, errors: int = 0, error: str = None):
    """Update sync status in the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {SYNC_STATUS_TABLE} (
                    endpoint, last_sync_timestamp, last_successful_offset,
                    status, last_error
                ) VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s)
                ON CONFLICT (endpoint) DO UPDATE SET
                    last_sync_timestamp = CURRENT_TIMESTAMP,
                    last_successful_offset = EXCLUDED.last_successful_offset,
                    status = EXCLUDED.status,
                    last_error = EXCLUDED.last_error
            """, (SPONSORED_ENDPOINT, processed, status, error))
            conn.commit()

def main():
    parser = argparse.ArgumentParser(description='Enrich member data with sponsored and cosponsored legislation')
    parser.add_argument('--member', help='Process specific member by bioguide ID')
    parser.add_argument('--all', action='store_true', help='Process all current members instead of just recent ones')
    parser.add_argument('--days', type=int, default=7, help='For recent mode, how many days back to consider')
    parser.add_argument('--limit', type=int, default=100, help='Maximum number of members to process')
    parser.add_argument('--refresh', action='store_true', help='Refresh bill cache before processing')
    args = parser.parse_args()
    
    try:
        # Initialize API client
        api_client = APIClient(BASE_API_URL)
        
        # Initialize processor
        processor = MemberEnrichment(api_client)
        
        # Update status to in-progress
        update_sync_status(SYNC_STATUS_IN_PROGRESS)
        
        # Determine which members to process
        if args.member:
            # Process single specified member
            members_to_process = [args.member]
            logger.info(f"Processing single member: {args.member}")
        else:
            # Get members from database
            recent_only = not args.all
            members_to_process = get_members_for_processing(recent_only, args.days, args.limit)
            logger.info(f"Processing {len(members_to_process)} members")
        
        # Process each member
        results = []
        processed_count = 0
        error_count = 0
        
        for bioguide_id in members_to_process:
            try:
                # For incremental processing, determine from_date
                from_date = None
                if not args.all and not args.member:
                    # Look back N days for recent changes
                    from_date = datetime.now() - timedelta(days=args.days)
                
                result = processor.process_member(bioguide_id, from_date)
                results.append(result)
                
                if result['status'] == 'success':
                    processed_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing member {bioguide_id}: {str(e)}", exc_info=True)
                error_count += 1
        
        # Clean up old files
        cleanup_old_files(os.path.join(os.path.dirname(__file__), 'raw'), 
                         pattern='*', days=RAW_DATA_RETENTION_DAYS)
        
        # Update sync status to success
        if error_count == 0:
            update_sync_status(SYNC_STATUS_SUCCESS, processed_count)
        else:
            update_sync_status(f"{SYNC_STATUS_SUCCESS}_with_errors", processed_count, error_count)
        
        logger.info(f"Process completed. {processed_count} members processed successfully, {error_count} errors.")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        update_sync_status(SYNC_STATUS_FAILED, error=str(e))
        raise

if __name__ == "__main__":
    main()