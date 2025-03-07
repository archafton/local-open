#!/usr/bin/env python3
"""
Core member fetching functionality with incremental processing.
Retrieves members from Congress.gov API and stores them in the database.
"""

import os
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set

# Import utilities
from congressgov.utils.logging_config import setup_logging
from congressgov.utils.api import APIClient
from congressgov.utils.database import get_db_connection, with_db_transaction
from congressgov.utils.file_storage import ensure_directory, save_json, cleanup_old_files
from congressgov.utils.member_utils import (
    parse_member_name, format_full_name, normalize_state_code, 
    parse_party_name, year_to_date, get_current_congress
)

# Set up logging
logger = setup_logging(__name__)

# API configuration
BASE_API_URL = "https://api.congress.gov/v3"
MEMBERS_LIST_ENDPOINT = "member"
SYNC_STATUS_TABLE = "api_sync_status"
DEFAULT_LIMIT = 250
RAW_DATA_RETENTION_DAYS = 30

def get_last_sync_timestamp() -> Optional[datetime]:
    """Get the last successful sync timestamp from the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT last_sync_timestamp 
                FROM {SYNC_STATUS_TABLE} 
                WHERE endpoint = %s AND status = 'success'
                ORDER BY last_sync_timestamp DESC 
                LIMIT 1
            """, (MEMBERS_LIST_ENDPOINT,))
            result = cur.fetchone()
            return result[0] if result else None

def update_sync_status(status: str, offset: int = 0, error: str = None):
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
            """, (MEMBERS_LIST_ENDPOINT, offset, status, error))
            conn.commit()

def save_members_to_json(members_data: Dict[str, Any], timestamp: str = None) -> str:
    """Save members data to a JSON file."""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    raw_dir = ensure_directory(os.path.dirname(__file__), 'raw', timestamp)
    filename = f"members_{timestamp}.json"
    
    return save_json(members_data, raw_dir, filename)

@with_db_transaction
def update_database(cursor, members: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Update database with member information.
    
    Args:
        cursor: Database cursor
        members: List of member data dictionaries
        
    Returns:
        Dictionary with counts of inserted, updated, and skipped members
    """
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "error": 0}
    current_year = datetime.now().year
    
    for member in members:
        try:
            # Extract member data
            bioguide_id = member.get('bioguideId')
            if not bioguide_id:
                logger.warning(f"Member missing bioguide ID: {member}")
                stats["skipped"] += 1
                continue
                
            # Parse name
            name_parts = parse_member_name(member.get('name', ''))
            first_name = name_parts['first_name']
            last_name = name_parts['last_name']
            
            # Full name (either from API or constructed)
            if 'directOrderName' in member and member['directOrderName']:
                full_name = member['directOrderName']
            else:
                full_name = format_full_name(first_name, name_parts['middle_name'], last_name)
            
            # Other fields
            state = member.get('state')
            district = member.get('district')
            
            # Parse party
            party_name, party_code = parse_party_name(member.get('partyName', ''))
            
            # Get chamber from latest term
            terms = member.get('terms', {}).get('item', [])
            current_term = terms[-1] if terms else {}
            chamber = current_term.get('chamber')
            
            # Determine if member is current
            end_year = current_term.get('endYear')
            current_member = end_year is None or int(end_year) >= current_year
            
            # Photo URL
            depiction = member.get('depiction', {})
            photo_url = depiction.get('imageUrl')
            
            # Update date
            update_date = member.get('updateDate')
            
            # Check if member already exists
            cursor.execute("SELECT id, last_updated FROM members WHERE bioguide_id = %s", (bioguide_id,))
            existing_member = cursor.fetchone()
            
            # For incremental processing: if member exists and hasn't been modified since our data,
            # we can skip it
            if existing_member and member.get('updateDate'):
                try:
                    member_update_date = datetime.fromisoformat(member.get('updateDate').replace('Z', '+00:00'))
                    db_update_date = existing_member[1]
                    
                    if db_update_date and db_update_date >= member_update_date:
                        logger.debug(f"Skipping member {bioguide_id} - no updates")
                        stats["skipped"] += 1
                        continue
                except ValueError:
                    # If date parsing fails, proceed with update
                    pass
            
            # Insert or update member
            cursor.execute("""
                INSERT INTO members (
                    bioguide_id, first_name, last_name, full_name, 
                    state, district, party, chamber, photo_url, 
                    current_member, last_updated
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (bioguide_id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    full_name = EXCLUDED.full_name,
                    state = EXCLUDED.state,
                    district = EXCLUDED.district,
                    party = EXCLUDED.party,
                    chamber = EXCLUDED.chamber,
                    photo_url = EXCLUDED.photo_url,
                    current_member = EXCLUDED.current_member,
                    last_updated = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                bioguide_id, first_name, last_name, full_name,
                state, district, party_name, chamber, photo_url,
                current_member
            ))
            
            member_id = cursor.fetchone()[0]
            
            # Insert member terms
            for term in terms:
                start_year = term.get('startYear')
                end_year = term.get('endYear')
                term_chamber = term.get('chamber', chamber)
                term_state = term.get('state', state)
                term_district = term.get('district', district)
                
                # Try to determine congress for the term
                congress = None
                if start_year:
                    try:
                        # Rough calculation: 
                        # 1st Congress started in 1789, add 1 every two years
                        start_year_int = int(start_year)
                        congress = ((start_year_int - 1789) // 2) + 1
                    except ValueError:
                        pass
                
                cursor.execute("""
                    INSERT INTO member_terms (
                        member_id, congress, chamber, party, state, district,
                        start_date, end_date
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (member_id, congress, chamber) DO UPDATE SET
                        party = EXCLUDED.party,
                        state = EXCLUDED.state,
                        district = EXCLUDED.district,
                        start_date = EXCLUDED.start_date,
                        end_date = EXCLUDED.end_date
                """, (
                    member_id,
                    congress,
                    term_chamber,
                    party_name,
                    term_state,
                    term_district,
                    year_to_date(start_year),
                    year_to_date(end_year)
                ))
            
            # Record type of operation for stats
            if existing_member:
                stats["updated"] += 1
            else:
                stats["inserted"] += 1
                
        except Exception as e:
            logger.error(f"Error processing member {member.get('bioguideId', 'unknown')}: {str(e)}")
            stats["error"] += 1
    
    return stats

def fetch_members(api_client: APIClient, from_date: Optional[datetime] = None, 
                 to_date: Optional[datetime] = None, limit: int = DEFAULT_LIMIT) -> Dict[str, Any]:
    """
    Fetch members from Congress.gov API.
    
    Args:
        api_client: API client
        from_date: Start date filter
        to_date: End date filter
        limit: Maximum members per page
        
    Returns:
        Dictionary with fetched members data
    """
    params = {
        'limit': limit,
        'sort': 'updateDate desc'
    }
    
    # Add date filtering if provided
    if from_date:
        params['fromUpdateDate'] = from_date.strftime("%Y-%m-%dT00:00:00Z")
    if to_date:
        params['toUpdateDate'] = to_date.strftime("%Y-%m-%dT23:59:59Z")
    
    # Get all members using pagination
    members = api_client.get_paginated(MEMBERS_LIST_ENDPOINT, params, 'members')
    
    return {'members': members, 'fetchDate': datetime.now().isoformat()}

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Fetch members from Congress.gov API')
    parser.add_argument('--force-full', action='store_true', help='Force full sync instead of incremental')
    parser.add_argument('--start-date', help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', help='End date in YYYY-MM-DD format')
    parser.add_argument('--days', type=int, default=7, help='Number of days to look back for incremental sync')
    parser.add_argument('--current-only', action='store_true', help='Only fetch current members')
    args = parser.parse_args()
    
    try:
        # Initialize API client
        api_client = APIClient(BASE_API_URL)
        
        # Start incremental sync by default
        from_date = None
        to_date = None
        
        # Use command line date filters if provided
        if args.start_date:
            from_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        
        if args.end_date:
            to_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        
        # If not forced and no explicit dates, get last sync date
        if not args.force_full and not args.start_date:
            last_sync = get_last_sync_timestamp()
            if last_sync:
                # Look back a few days before last sync to ensure no gaps
                from_date = last_sync - timedelta(days=args.days)
                logger.info(f"Running incremental sync from {from_date.isoformat()}")
            else:
                logger.info("No previous sync found, running full sync")
        
        # Update status to in-progress
        update_sync_status('in_progress')
        
        # Fetch members
        logger.info("Fetching members from Congress.gov API")
        members_data = fetch_members(api_client, from_date, to_date)
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = save_members_to_json(members_data, timestamp)
        logger.info(f"Members data saved to {file_path}")
        
        # Clean up old files
        cleanup_old_files(os.path.join(os.path.dirname(__file__), 'raw'), 
                         pattern='*', days=RAW_DATA_RETENTION_DAYS)
        
        # Update database
        if members_data['members']:
            # Filter for current members if requested
            if args.current_only:
                current_year = datetime.now().year
                members = []
                for member in members_data['members']:
                    terms = member.get('terms', {}).get('item', [])
                    if terms:
                        last_term = terms[-1]
                        end_year = last_term.get('endYear')
                        if end_year is None or int(end_year) >= current_year:
                            members.append(member)
                logger.info(f"Filtered to {len(members)} current members from {len(members_data['members'])} total")
            else:
                members = members_data['members']
                
            logger.info(f"Updating database with {len(members)} members")
            stats = update_database(members=members)
            logger.info(f"Database updated: {stats['inserted']} inserted, {stats['updated']} updated, "
                       f"{stats['skipped']} skipped, {stats['error']} errors")
        else:
            logger.info("No members to update")
        
        # Update sync status to success
        update_sync_status('success')
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        update_sync_status('failed', error=str(e))
        raise

if __name__ == "__main__":
    main()
