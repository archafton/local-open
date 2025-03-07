#!/usr/bin/env python3
"""
Member detail processor - fetches detailed information for members.
Handles member details, leadership positions, party history, and related data.
"""

import os
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Import utilities
from congressgov.utils.logging_config import setup_logging
from congressgov.utils.api import APIClient
from congressgov.utils.database import get_db_connection, with_db_transaction
from congressgov.utils.file_storage import ensure_directory, save_json, cleanup_old_files
from congressgov.utils.member_utils import (
    get_leadership_title, year_to_date, parse_party_name
)

# Set up logging
logger = setup_logging(__name__)

# API configuration
BASE_API_URL = "https://api.congress.gov/v3"
MEMBER_DETAIL_ENDPOINT = "member/{bioguideId}"
SYNC_STATUS_TABLE = "api_sync_status"
RAW_DATA_RETENTION_DAYS = 30

class MemberDetailProcessor:
    """Class for processing member details."""
    
    def __init__(self, api_client: APIClient):
        """Initialize with API client."""
        self.api_client = api_client
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.raw_dir = ensure_directory(os.path.dirname(__file__), 'raw', 'details', self.timestamp)
    
    def fetch_member_detail(self, bioguide_id: str) -> Dict[str, Any]:
        """Fetch detailed member information."""
        endpoint = MEMBER_DETAIL_ENDPOINT.format(bioguideId=bioguide_id)
        
        logger.info(f"Fetching details for member {bioguide_id}")
        return self.api_client.get(endpoint)
    
    def save_member_data(self, data: Dict[str, Any], bioguide_id: str, data_type: str = 'details') -> str:
        """Save member data to a JSON file."""
        dir_path = ensure_directory(self.raw_dir, bioguide_id)
        filename = f"{data_type}.json"
        
        return save_json(data, dir_path, filename)
    
    @with_db_transaction
    def update_member_details(cursor, self, member_data: Dict[str, Any]) -> bool:
        """Update member details in the database."""
        # The decorator injects 'cursor' as the first parameter, shifting 'self' to second position
        if 'member' not in member_data:
            logger.warning("No member data found in response")
            return False
            
        member = member_data['member']
        bioguide_id = member.get('bioguideId')
        
        if not bioguide_id:
            logger.warning("No bioguide ID found in member data")
            return False
            
        # Extract detailed member information
        birth_year = member.get('birthYear')
        death_year = member.get('deathYear')
        direct_order_name = member.get('directOrderName')
        honorific_name = member.get('honorificName')
        inverted_order_name = member.get('invertedOrderName')
        update_date = member.get('updateDate')
        
        # Additional fields that might be present in detailed data
        office_address = None
        phone = None
        url = None
        
        # Contact information
        if 'contactInformation' in member:
            contact_info = member['contactInformation']
            if isinstance(contact_info, dict):
                office_address = contact_info.get('address')
                phone = contact_info.get('phone')
                url = contact_info.get('url')
                
        # Update the members table with additional details
        cursor.execute("""
            UPDATE members SET
                birth_year = %s,
                death_year = %s,
                direct_order_name = %s,
                honorific_name = %s,
                inverted_order_name = %s,
                office_address = %s,
                phone = %s,
                url = %s,
                update_date = %s,
                last_updated = CURRENT_TIMESTAMP
            WHERE bioguide_id = %s
            RETURNING id
        """, (
            birth_year,
            death_year,
            direct_order_name,
            honorific_name,
            inverted_order_name,
            office_address,
            phone,
            url,
            update_date,
            bioguide_id
        ))
        
        result = cursor.fetchone()
        if not result:
            logger.warning(f"No member record found for {bioguide_id}")
            return False
            
        member_id = result[0]
        
        # Handle leadership positions
        if 'leadership' in member:
            leadership_items = []
            if isinstance(member['leadership'], dict) and 'item' in member['leadership']:
                leadership_items = member['leadership']['item']
            elif isinstance(member['leadership'], list):
                leadership_items = member['leadership']
                
            for position in leadership_items:
                cursor.execute("""
                    INSERT INTO member_leadership (
                        member_id, congress, leadership_type
                    ) VALUES (
                        %s, %s, %s
                    ) ON CONFLICT (member_id, congress) DO UPDATE SET
                        leadership_type = EXCLUDED.leadership_type
                """, (
                    member_id,
                    position.get('congress'),
                    position.get('type')
                ))
        
        # Handle party history
        if 'partyHistory' in member:
            party_history_items = []
            if isinstance(member['partyHistory'], dict) and 'item' in member['partyHistory']:
                party_history_items = member['partyHistory']['item']
            elif isinstance(member['partyHistory'], list):
                party_history_items = member['partyHistory']
                
            for party in party_history_items:
                party_name, party_code = parse_party_name(party.get('partyName', ''))
                start_year = party.get('startYear')
                
                if start_year:
                    cursor.execute("""
                        INSERT INTO member_party_history (
                            member_id, party_name, party_code, start_year
                        ) VALUES (
                            %s, %s, %s, %s
                        ) ON CONFLICT (member_id, start_year) DO UPDATE SET
                            party_name = EXCLUDED.party_name,
                            party_code = EXCLUDED.party_code
                    """, (
                        member_id,
                        party_name,
                        party_code or party.get('partyAbbreviation'),
                        start_year
                    ))
        
        return True
    
    def process_member(self, bioguide_id: str) -> Dict[str, Any]:
        """Process a single member, fetching and updating detailed information."""
        results = {
            "bioguide_id": bioguide_id,
            "status": "success",
            "details_updated": False
        }
        
        try:
            # Fetch member details
            member_data = self.fetch_member_detail(bioguide_id)
            self.save_member_data(member_data, bioguide_id, 'details')
            
            # Update member details
            results["details_updated"] = self.update_member_details(member_data=member_data)
            
            logger.info(f"Successfully processed member {bioguide_id}")
            
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
                    WHERE last_updated >= %s
                    ORDER BY last_updated ASC
                    LIMIT %s
                """, (cutoff_date, limit))
            else:
                # Get members with missing details or oldest updated
                cur.execute("""
                    SELECT bioguide_id 
                    FROM members 
                    WHERE direct_order_name IS NULL
                       OR birth_year IS NULL
                    UNION
                    SELECT bioguide_id 
                    FROM members 
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
            """, (MEMBER_DETAIL_ENDPOINT, processed, status, error))
            conn.commit()

def main():
    parser = argparse.ArgumentParser(description='Process member details')
    parser.add_argument('--member', help='Process specific member by bioguide ID')
    parser.add_argument('--all', action='store_true', help='Process all members instead of just recent ones')
    parser.add_argument('--days', type=int, default=7, help='For recent mode, how many days back to consider')
    parser.add_argument('--limit', type=int, default=100, help='Maximum number of members to process')
    parser.add_argument('--missing', action='store_true', help='Focus on members with missing details')
    args = parser.parse_args()
    
    try:
        # Initialize API client
        api_client = APIClient(BASE_API_URL)
        
        # Initialize processor
        processor = MemberDetailProcessor(api_client)
        
        # Update status to in-progress
        update_sync_status('in_progress')
        
        # Determine which members to process
        if args.member:
            # Process single specified member
            members_to_process = [args.member]
            logger.info(f"Processing single member: {args.member}")
        else:
            # Get members from database
            recent_only = not args.all and not args.missing
            members_to_process = get_members_for_processing(recent_only, args.days, args.limit)
            logger.info(f"Processing {len(members_to_process)} members")
        
        # Process each member
        results = []
        processed_count = 0
        error_count = 0
        
        for bioguide_id in members_to_process:
            try:
                result = processor.process_member(bioguide_id)
                results.append(result)
                
                if result['status'] == 'success':
                    processed_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing member {bioguide_id}: {str(e)}", exc_info=True)
                error_count += 1
        
        # Clean up old files
        cleanup_old_files(os.path.join(os.path.dirname(__file__), 'raw', 'details'), 
                         pattern='*', days=RAW_DATA_RETENTION_DAYS)
        
        # Update sync status to success
        if error_count == 0:
            update_sync_status('success', processed_count)
        else:
            update_sync_status('completed_with_errors', processed_count, error_count)
        
        logger.info(f"Process completed. {processed_count} members processed successfully, {error_count} errors.")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        update_sync_status('failed', error=str(e))
        raise

if __name__ == "__main__":
    main()
