#!/usr/bin/env python3
"""
Core bill fetching functionality with incremental processing.
Retrieves bills from Congress.gov API and stores them in the database.
Handles both modern and historical bill structures.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union

# Fix imports for both local development and Lambda
try:
    # Try the direct import first (works when package is installed)
    from congressgov.utils.logging_config import setup_logging
    from congressgov.utils.api import APIClient
    from congressgov.utils.database import get_db_connection, with_db_transaction
    from congressgov.utils.file_storage import ensure_directory, save_json, cleanup_old_files
    from congressgov.utils.tag_utils import get_or_create_policy_area_tag, update_bill_tags
    from congressgov.utils.bill_utils import normalize_bill_status, parse_bill_number
    from bill_validation import is_historical_bill
except ImportError:
    # If that fails, add the parent directory to the path
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from utils.logging_config import setup_logging
    from utils.api import APIClient
    from utils.database import get_db_connection, with_db_transaction
    from utils.file_storage import ensure_directory, save_json, cleanup_old_files
    from utils.tag_utils import get_or_create_policy_area_tag, update_bill_tags
    from utils.bill_utils import normalize_bill_status, parse_bill_number
    from bill_validation import is_historical_bill

# Set up logging
logger = setup_logging(__name__)

# API configuration
BASE_API_URL = "https://api.congress.gov/v3"
BILLS_LIST_ENDPOINT = "bill"
SYNC_STATUS_TABLE = "api_sync_status"
DEFAULT_LIMIT = 250
RAW_DATA_RETENTION_DAYS = 30
HISTORICAL_CONGRESS_RANGE = range(6, 43)  # 6th-42nd Congresses (1799-1873)

def get_bill_data(bill: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
    """
    Extract bill data handling both dictionary and list structures.
    
    Args:
        bill: Bill data from API, either a dictionary (modern bills) or a list (historical bills)
        
    Returns:
        Extracted bill data dictionary, or None if invalid
    """
    if isinstance(bill, list):
        if not bill:  # Empty array
            return None
        
        # Sort by updateDate (descending) and use the most recently updated entry
        sorted_bills = sorted(bill, key=lambda x: x.get('updateDate', ''), reverse=True)
        
        # Log that we found multiple entries
        if len(bill) > 1:
            logger.info(f"Multiple bill entries found for {sorted_bills[0].get('type', '')}{sorted_bills[0].get('number', '')}. "
                      f"Using most recently updated entry from {sorted_bills[0].get('updateDate', 'unknown date')}")
        
        return sorted_bills[0]
    else:
        return bill

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
            """, (BILLS_LIST_ENDPOINT,))
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
            """, (BILLS_LIST_ENDPOINT, offset, status, error))
            conn.commit()

def save_bills_to_json(bills_data: Dict[str, Any], timestamp: str = None) -> str:
    """Save bills data to a JSON file."""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    raw_dir = ensure_directory(os.path.dirname(__file__), 'raw', timestamp)
    filename = f"bills_{timestamp}.json"
    
    return save_json(bills_data, raw_dir, filename)

@with_db_transaction
def update_database(cursor, bills: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Update database with bill information.
    
    Args:
        cursor: Database cursor
        bills: List of bill data dictionaries
        
    Returns:
        Dictionary with counts of inserted, updated, and skipped bills
    """
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "error": 0, "historical": 0}
    
    for bill_data in bills:
        try:
            # Extract bill data handling both structures
            bill = get_bill_data(bill_data.get('bill'))
            if not bill:
                logger.warning("Empty bill data")
                stats["skipped"] += 1
                continue
            
            # Extract bill data
            bill_type = bill.get('type', '')
            bill_number = f"{bill_type}{bill.get('number', '')}"
            bill_title = bill.get('title', '')
            sponsor_id = bill.get('sponsors', [{}])[0].get('bioguideId') if bill.get('sponsors') else None
            introduced_date = bill.get('introducedDate')
            congress = bill.get('congress')
            action_text = bill.get('latestAction', {}).get('text', '')
            action_date = bill.get('latestAction', {}).get('actionDate')
            normalized_status = normalize_bill_status(action_text)
            policy_area = bill.get('policyArea', {}).get('name')
            
            # Check if this is a historical bill
            bill_is_historical = is_historical_bill(congress)
            if bill_is_historical:
                stats["historical"] += 1
            
            # Check if bill already exists
            cursor.execute("SELECT id, last_updated FROM bills WHERE bill_number = %s", (bill_number,))
            existing_bill = cursor.fetchone()
            
            # For incremental processing: if bill exists and hasn't been modified since our data,
            # we can skip it (add more conditions as needed)
            if existing_bill and bill.get('updateDate'):
                # Parse the API's datetime string into an offset-aware datetime
                bill_update_date = datetime.fromisoformat(bill.get('updateDate').replace('Z', '+00:00'))
    
                # Strip the timezone information to make it offset-naive
                bill_update_date = bill_update_date.replace(tzinfo=None)
    
                # Get the database update timestamp
                db_update_date = existing_bill[1]
    
                # If the database datetime is offset-aware, make it offset-naive too
                if db_update_date and db_update_date.tzinfo is not None:
                    db_update_date = db_update_date.replace(tzinfo=None)
    
                # Now both are offset-naive and can be compared
                if db_update_date and db_update_date >= bill_update_date:
                    if bill_is_historical:
                        logger.debug(f"Skipping historical bill {bill_number} (Congress: {congress}) - no updates")
                    else:
                        logger.debug(f"Skipping bill {bill_number} - no updates")
                    stats["skipped"] += 1
                    continue
            
            # Insert or update bill
            cursor.execute("""
                INSERT INTO bills (
                    bill_number, bill_title, sponsor_id, introduced_date, 
                    congress, status, normalized_status, latest_action,
                    latest_action_date, bill_type, policy_area, last_updated
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (bill_number) DO UPDATE SET
                    bill_title = EXCLUDED.bill_title,
                    sponsor_id = EXCLUDED.sponsor_id,
                    introduced_date = EXCLUDED.introduced_date,
                    congress = EXCLUDED.congress,
                    status = EXCLUDED.status,
                    normalized_status = EXCLUDED.normalized_status,
                    latest_action = EXCLUDED.latest_action,
                    latest_action_date = EXCLUDED.latest_action_date,
                    bill_type = EXCLUDED.bill_type,
                    policy_area = EXCLUDED.policy_area,
                    last_updated = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                bill_number, bill_title, sponsor_id, introduced_date,
                congress, action_text, normalized_status, action_text,
                action_date, bill_type, policy_area
            ))
            
            bill_id = cursor.fetchone()[0]
            
            # Handle policy area tag
            if policy_area:
                tag_id = get_or_create_policy_area_tag(cursor, policy_area)
                if tag_id:
                    update_bill_tags(cursor, bill_id, tag_id)
            
            # Record type of operation for stats
            if existing_bill:
                if bill_is_historical:
                    logger.info(f"Updated historical bill {bill_number} (Congress: {congress})")
                stats["updated"] += 1
            else:
                if bill_is_historical:
                    logger.info(f"Inserted historical bill {bill_number} (Congress: {congress})")
                stats["inserted"] += 1
                
        except Exception as e:
            logger.error(f"Error processing bill: {str(e)}")
            stats["error"] += 1
    
    return stats

def fetch_bills(api_client: APIClient, from_date: Optional[datetime] = None, 
                to_date: Optional[datetime] = None, limit: int = DEFAULT_LIMIT) -> Dict[str, Any]:
    """
    Fetch bills from Congress.gov API.
    
    Args:
        api_client: API client
        from_date: Start date filter
        to_date: End date filter
        limit: Maximum bills per page
        
    Returns:
        Dictionary with fetched bills data
    """
    params = {
        'limit': limit,
        'sort': 'updateDate desc'
    }
    
    # Add date filtering if provided
    if from_date:
        params['fromDateTime'] = from_date.strftime("%Y-%m-%dT00:00:00Z")
    if to_date:
        params['toDateTime'] = to_date.strftime("%Y-%m-%dT23:59:59Z")
    
    # Get all bills using pagination
    bills = api_client.get_paginated(BILLS_LIST_ENDPOINT, params, 'bills')
    
    return {'bills': bills, 'fetchDate': datetime.now().isoformat()}

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Fetch bills from Congress.gov API')
    parser.add_argument('--force-full', action='store_true', help='Force full sync instead of incremental')
    parser.add_argument('--start-date', help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', help='End date in YYYY-MM-DD format')
    parser.add_argument('--days', type=int, default=7, help='Number of days to look back for incremental sync')
    parser.add_argument('--historical', action='store_true', help='Enable specialized processing for historical bills')
    parser.add_argument('--congress', type=int, help='Fetch bills from a specific Congress')
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
        
        # If specific Congress is requested
        if args.congress:
            try:
                congress_num = int(args.congress)
                is_historical = 6 <= congress_num <= 42
                if is_historical:
                    logger.info(f"Fetching bills from historical Congress: {args.congress} ({1799 + (congress_num - 6) * 2}-{1801 + (congress_num - 6) * 2})")
                    if args.historical:
                        logger.info("Historical bill processing mode enabled")
            except ValueError:
                logger.warning(f"Invalid Congress number: {args.congress}")
        
        # If not forced and no explicit dates or Congress, get last sync date
        if not args.force_full and not args.start_date and not args.congress:
            last_sync = get_last_sync_timestamp()
            if last_sync:
                # Look back a few days before last sync to ensure no gaps
                from_date = last_sync - timedelta(days=args.days)
                logger.info(f"Running incremental sync from {from_date.isoformat()}")
            else:
                logger.info("No previous sync found, running full sync")
        
        # Update status to in-progress
        update_sync_status('in_progress')
        
        # Fetch bills
        logger.info("Fetching bills from Congress.gov API")
        bills_data = fetch_bills(api_client, from_date, to_date)
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = save_bills_to_json(bills_data, timestamp)
        logger.info(f"Bills data saved to {file_path}")
        
        # Clean up old files
        cleanup_old_files(os.path.join(os.path.dirname(__file__), 'raw'), 
                         pattern='*', days=RAW_DATA_RETENTION_DAYS)
        
        # Update database
        if bills_data['bills']:
            logger.info(f"Updating database with {len(bills_data['bills'])} bills")
            
            # Debug: Print the structure of the first bill to understand the data format
            if bills_data['bills']:
                first_bill = bills_data['bills'][0]
                logger.info(f"First bill structure: {json.dumps(first_bill, indent=2)}")
                logger.info(f"First bill keys: {list(first_bill.keys())}")
                
                # Check if 'bill' key exists
                if 'bill' in first_bill:
                    logger.info("'bill' key exists in the data")
                else:
                    logger.info("'bill' key does NOT exist in the data")
                    
                    # If 'bill' key doesn't exist, the bill data might be directly in the item
                    # Let's modify how we process the bills
                    logger.info("Modifying bill processing to handle direct bill data")
                    
                    # Create a new list with the correct structure
                    modified_bills = []
                    for bill_item in bills_data['bills']:
                        # Wrap the bill data in a dictionary with a 'bill' key
                        modified_bills.append({'bill': bill_item})
                    
                    # Use the modified bills list instead
                    bills_data['bills'] = modified_bills
                    logger.info(f"Modified {len(modified_bills)} bills to have 'bill' key")
            
            stats = update_database(bills_data['bills'])
            logger.info(f"Database updated: {stats['inserted']} inserted, {stats['updated']} updated, "
                       f"{stats['skipped']} skipped, {stats['error']} errors, {stats['historical']} historical")
        else:
            logger.info("No bills to update")
        
        # Update sync status to success
        update_sync_status('success')
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        update_sync_status('failed', error=str(e))
        raise

if __name__ == "__main__":
    main()

def lambda_handler(event, context):
    """AWS Lambda handler for bill fetching.
    
    Args:
        event: Lambda event containing parameters
        context: Lambda context
        
    Returns:
        Dictionary with execution results
    """
    # Set up argument parser similar to main()
    parser = argparse.ArgumentParser()
    args = parser.parse_args([])  # Empty list to avoid reading sys.argv
    
    # Override args with event parameters
    if 'force_full' in event:
        args.force_full = event['force_full']
    else:
        args.force_full = False
        
    if 'start_date' in event:
        args.start_date = event['start_date']
    else:
        args.start_date = None
        
    if 'end_date' in event:
        args.end_date = event['end_date']
    else:
        args.end_date = None
        
    if 'days' in event:
        args.days = event['days']
    else:
        args.days = 7
    
    if 'historical' in event:
        args.historical = event['historical']
    else:
        args.historical = False
        
    if 'congress' in event:
        args.congress = event['congress']
    else:
        args.congress = None
    
    # Initialize result
    result = {
        'status': 'success',
        'stats': {
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'error': 0,
            'historical': 0
        }
    }
    
    try:
        # Initialize API client
        api_client = APIClient(BASE_API_URL)
        
        # Start incremental sync by default
        from_date = None
        to_date = None
        
        # Use event date filters if provided
        if args.start_date:
            from_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        
        if args.end_date:
            to_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        
        # If specific Congress is requested
        if args.congress:
            try:
                congress_num = int(args.congress)
                is_historical = 6 <= congress_num <= 42
                if is_historical:
                    logger.info(f"Fetching bills from historical Congress: {args.congress}")
                    result['historical_congress'] = True
            except ValueError:
                logger.warning(f"Invalid Congress number: {args.congress}")
        
        # If not forced and no explicit dates or Congress, get last sync date
        if not args.force_full and not args.start_date and not args.congress:
            last_sync = get_last_sync_timestamp()
            if last_sync:
                # Look back a few days before last sync to ensure no gaps
                from_date = last_sync - timedelta(days=args.days)
                logger.info(f"Running incremental sync from {from_date.isoformat()}")
                result['from_date'] = from_date.isoformat()
            else:
                logger.info("No previous sync found, running full sync")
                result['full_sync'] = True
        
        # Update status to in-progress
        update_sync_status('in_progress')
        
        # Fetch bills
        logger.info("Fetching bills from Congress.gov API")
        bills_data = fetch_bills(api_client, from_date, to_date)
        result['bills_count'] = len(bills_data['bills'])
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = save_bills_to_json(bills_data, timestamp)
        logger.info(f"Bills data saved to {file_path}")
        result['file_path'] = file_path
        
        # Clean up old files
        cleanup_old_files(os.path.join(os.path.dirname(__file__), 'raw'), 
                         pattern='*', days=RAW_DATA_RETENTION_DAYS)
        
        # Update database
        if bills_data['bills']:
            logger.info(f"Updating database with {len(bills_data['bills'])} bills")
            
            # Debug: Print the structure of the first bill to understand the data format
            if bills_data['bills']:
                first_bill = bills_data['bills'][0]
                logger.info(f"First bill structure: {json.dumps(first_bill, indent=2)}")
                logger.info(f"First bill keys: {list(first_bill.keys())}")
                
                # Check if 'bill' key exists
                if 'bill' in first_bill:
                    logger.info("'bill' key exists in the data")
                else:
                    logger.info("'bill' key does NOT exist in the data")
                    
                    # If 'bill' key doesn't exist, the bill data might be directly in the item
                    # Let's modify how we process the bills
                    logger.info("Modifying bill processing to handle direct bill data")
                    
                    # Create a new list with the correct structure
                    modified_bills = []
                    for bill_item in bills_data['bills']:
                        # Wrap the bill data in a dictionary with a 'bill' key
                        modified_bills.append({'bill': bill_item})
                    
                    # Use the modified bills list instead
                    bills_data['bills'] = modified_bills
                    logger.info(f"Modified {len(modified_bills)} bills to have 'bill' key")
            
            stats = update_database(bills_data['bills'])
            logger.info(f"Database updated: {stats['inserted']} inserted, {stats['updated']} updated, "
                       f"{stats['skipped']} skipped, {stats['error']} errors, {stats['historical']} historical")
            result['stats'] = stats
        else:
            logger.info("No bills to update")
        
        # Update sync status to success
        update_sync_status('success')
        
        return {
            'statusCode': 200,
            'body': result
        }
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        update_sync_status('failed', error=str(e))
        
        return {
            'statusCode': 500,
            'body': {
                'status': 'error',
                'message': str(e)
            }
        }
