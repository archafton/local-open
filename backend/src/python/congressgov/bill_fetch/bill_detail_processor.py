#!/usr/bin/env python3
"""
Bill detail processor - consolidated functionality from detail_fetch and enrichment.
Fetches detailed bill information, actions, text versions, and related data.
"""

import os
import json
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set

# Import utilities
from congressgov.utils.logging_config import setup_logging
from congressgov.utils.api import APIClient
from congressgov.utils.database import get_db_connection, with_db_transaction
from congressgov.utils.file_storage import ensure_directory, save_json, cleanup_old_files
from congressgov.utils.tag_utils import get_or_create_policy_area_tag, update_bill_tags
from congressgov.utils.bill_utils import parse_bill_number

# Set up logging
logger = setup_logging(__name__)

# API configuration
BASE_API_URL = "https://api.congress.gov/v3"
BILL_DETAIL_ENDPOINT = "bill/{congress}/{bill_type}/{bill_number}"
SYNC_STATUS_TABLE = "api_sync_status"
RAW_DATA_RETENTION_DAYS = 30

class BillProcessor:
    """Class for processing bill details and enrichments."""
    
    def __init__(self, api_client: APIClient):
        """Initialize with API client."""
        self.api_client = api_client
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.raw_dir = ensure_directory(os.path.dirname(__file__), 'raw', 'details', self.timestamp)
    
    def fetch_bill_detail(self, congress: str, bill_type: str, bill_number: str) -> Dict[str, Any]:
        """Fetch detailed bill information."""
        endpoint = BILL_DETAIL_ENDPOINT.format(
            congress=congress, bill_type=bill_type, bill_number=bill_number
        )
        
        logger.info(f"Fetching details for bill {congress} {bill_type}{bill_number}")
        return self.api_client.get(endpoint)
    
    def fetch_text_versions(self, url: str) -> Dict[str, Any]:
        """Fetch text versions for a bill using the provided URL."""
        logger.info(f"Fetching text versions from: {url}")
        return self.api_client.get(url.replace(BASE_API_URL + '/', ''))
    
    def fetch_bill_actions(self, url: str) -> Dict[str, Any]:
        """Fetch bill actions using the provided URL."""
        logger.info(f"Fetching actions from: {url}")
        return self.api_client.get(url.replace(BASE_API_URL + '/', ''))
    
    def fetch_bill_summaries(self, url: str) -> Dict[str, Any]:
        """Fetch bill summaries using the provided URL."""
        logger.info(f"Fetching summaries from: {url}")
        return self.api_client.get(url.replace(BASE_API_URL + '/', ''))
    
    def fetch_bill_cosponsors(self, url: str) -> Dict[str, Any]:
        """Fetch bill cosponsors using the provided URL."""
        logger.info(f"Fetching cosponsors from: {url}")
        return self.api_client.get(url.replace(BASE_API_URL + '/', ''))
    
    def fetch_bill_subjects(self, url: str) -> Dict[str, Any]:
        """Fetch bill subjects using the provided URL."""
        logger.info(f"Fetching subjects from: {url}")
        return self.api_client.get(url.replace(BASE_API_URL + '/', ''))
    
    def process_text_versions(self, versions: List[Dict[str, Any]], introduced_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Process text versions with consistent formatting."""
        if not versions:
            return []

        # Handle null dates using introduced_date
        for version in versions:
            if version.get('date') is None and introduced_date:
                version['date'] = introduced_date
                version['is_initial_version'] = True

        # Sort versions by date and type importance
        type_importance = {
            'Public Law': 1,
            'Enrolled Bill': 2,
            'Engrossed in Senate': 3,
            'Engrossed in House': 3,
            'Placed on Calendar Senate': 4,
            'Placed on Calendar House': 4
        }

        def version_sort_key(version):
            date = version.get('date') or ''
            type_priority = type_importance.get(version.get('type', ''), 999)
            return (date, type_priority)

        versions.sort(key=version_sort_key, reverse=True)

        # Normalize format types
        format_display_names = {
            'Formatted Text': 'HTML',
            'Formatted XML': 'XML',
            'PDF': 'PDF'
        }

        for version in versions:
            if 'formats' in version:
                for fmt in version['formats']:
                    fmt['display_type'] = format_display_names.get(fmt.get('type', ''), fmt.get('type', ''))

        return versions
    
    def save_bill_data(self, data: Dict[str, Any], congress: str, bill_type: str, 
                     bill_number: str, data_type: str) -> str:
        """Save bill data to a JSON file."""
        dir_path = ensure_directory(self.raw_dir, congress, bill_type, bill_number)
        filename = f"{data_type}.json"
        
        return save_json(data, dir_path, filename, create_backup=True)
    
    @with_db_transaction
    def update_bill_details(cursor, self, bill_data: Dict[str, Any], 
                          text_versions_data: Optional[Dict[str, Any]] = None,
                          summaries_data: Optional[Dict[str, Any]] = None) -> bool:
        """Update bill details in the database."""
        # The decorator injects 'cursor' as the first parameter, shifting 'self' to second position
        
        # Check if bill_data has the expected structure
        if 'bill' not in bill_data:
            logger.warning("Bill data missing 'bill' field")
            return False
            
        # Handle different bill structures
        if isinstance(bill_data['bill'], list):
            # For older bills (array structure)
            if not bill_data['bill']:  # Empty array
                logger.warning("Bill data contains empty bill array")
                return False
                
            # Sort by updateDate (descending) and use the most recently updated entry
            sorted_bills = sorted(bill_data['bill'], 
                                key=lambda x: x.get('updateDate', ''), 
                                reverse=True)
            bill = sorted_bills[0]
            
            # Log that we found multiple entries
            if len(bill_data['bill']) > 1:
                logger.info(f"Multiple bill entries found for {bill.get('type', '')}{bill.get('number', '')}. "
                          f"Using most recently updated entry from {bill.get('updateDate', 'unknown date')}")
        else:
            # For newer bills (dictionary structure)
            bill = bill_data['bill']
        
        # Now proceed with the bill object
        if 'type' not in bill or 'number' not in bill:
            logger.warning(f"Bill missing required fields: {bill.keys()}")
            return False
            
        bill_number = f"{bill['type']}{bill['number']}".upper()
        
        # Process summaries
        summaries = []
        if summaries_data and 'summaries' in summaries_data:
            summaries = [{
                'version_code': s.get('versionCode'),
                'action_date': s.get('actionDate'),
                'action_desc': s.get('actionDesc'),
                'text': s.get('text')
            } for s in summaries_data['summaries']]
        
        # Process text versions
        text_versions = []
        if text_versions_data and 'textVersions' in text_versions_data:
            text_versions = self.process_text_versions(  # Use self to call instance methods
                text_versions_data['textVersions'],
                bill.get('introducedDate')
            )
        
        # Update the bill
        cursor.execute("""
            UPDATE bills SET
                bill_title = %s,
                sponsor_id = %s,
                introduced_date = %s,
                summary = %s,
                congress = %s,
                status = %s,
                text_versions = %s::jsonb,
                policy_area = %s,
                official_title = %s,
                short_title = %s,
                api_url = %s,
                last_updated = CURRENT_TIMESTAMP
            WHERE bill_number = %s
            RETURNING id
        """, (
            bill.get('title', ''),
            bill.get('sponsors', [{}])[0].get('bioguideId') if bill.get('sponsors') else None,
            bill.get('introducedDate'),
            json.dumps(summaries) if summaries else None,
            bill.get('congress'),
            bill.get('latestAction', {}).get('text', ''),
            json.dumps(text_versions) if text_versions else None,
            bill.get('policyArea', {}).get('name'),
            bill.get('titles', {}).get('item', [{}])[0].get('title') if bill.get('titles', {}).get('item') else None,
            bill.get('titles', {}).get('item', [{}])[1].get('title') if bill.get('titles', {}).get('item', []) and len(bill.get('titles', {}).get('item', [])) > 1 else None,
            bill.get('url'),
            bill_number
        ))
        
        result = cursor.fetchone()
        if not result:
            logger.warning(f"No bill record found for {bill_number}")
            return False
        
        bill_id = result[0]
        
        # Handle policy area tag
        policy_area_name = bill.get('policyArea', {}).get('name')
        if policy_area_name:
            tag_id = get_or_create_policy_area_tag(cursor, policy_area_name)
            if tag_id:
                update_bill_tags(cursor, bill_id, tag_id)
        
        return True
    
    @with_db_transaction
    def update_bill_actions(cursor, self, bill_number: str, actions_data: Dict[str, Any]) -> int:
        """Update bill actions in the database."""
        # The decorator injects 'cursor' as the first parameter, shifting 'self' to second position
        
        if not actions_data or 'actions' not in actions_data:
            logger.warning(f"No actions found for bill {bill_number}")
            return 0
        
        # Check if the bill exists in the database with this exact bill_number
        cursor.execute("SELECT 1 FROM bills WHERE bill_number = %s", (bill_number,))
        if not cursor.fetchone():
            # Try uppercase version
            uppercase_bill_number = bill_number.upper()
            cursor.execute("SELECT 1 FROM bills WHERE bill_number = %s", (uppercase_bill_number,))
            if cursor.fetchone():
                bill_number = uppercase_bill_number
            else:
                logger.warning(f"Bill {bill_number} not found in database, cannot update actions")
                return 0
        
        actions = actions_data['actions']
        count = 0
        
        for action in actions:
            cursor.execute("""
                INSERT INTO bill_actions (
                    bill_number, action_date, action_text, action_type, action_time
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (bill_number, action_date, action_text) DO UPDATE SET
                    action_type = EXCLUDED.action_type,
                    action_time = EXCLUDED.action_time
            """, (
                bill_number,
                action.get('actionDate'),
                action.get('text'),
                action.get('type'),
                action.get('actionTime')
            ))
            count += 1
        
        return count
    
    @with_db_transaction
    def update_bill_cosponsors(cursor, self, bill_number: str, cosponsors: List[Dict[str, Any]]) -> int:
        """Update bill cosponsors in the database."""
        # The decorator injects 'cursor' as the first parameter, shifting 'self' to second position
        
        if not cosponsors:
            return 0
        
        # Check if the bill exists in the database with this exact bill_number
        cursor.execute("SELECT 1 FROM bills WHERE bill_number = %s", (bill_number,))
        if not cursor.fetchone():
            # Try uppercase version
            uppercase_bill_number = bill_number.upper()
            cursor.execute("SELECT 1 FROM bills WHERE bill_number = %s", (uppercase_bill_number,))
            if cursor.fetchone():
                bill_number = uppercase_bill_number
            else:
                logger.warning(f"Bill {bill_number} not found in database, cannot update cosponsors")
                return 0
        
        count = 0
        for cosponsor in cosponsors:
            cursor.execute("""
                INSERT INTO bill_cosponsors (
                    bill_number, cosponsor_id, cosponsor_name, 
                    cosponsor_party, cosponsor_state, cosponsor_date
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (bill_number, cosponsor_id) DO UPDATE SET
                    cosponsor_name = EXCLUDED.cosponsor_name,
                    cosponsor_party = EXCLUDED.cosponsor_party,
                    cosponsor_state = EXCLUDED.cosponsor_state,
                    cosponsor_date = EXCLUDED.cosponsor_date
            """, (
                bill_number,
                cosponsor.get('bioguideId'),
                cosponsor.get('fullName'),
                cosponsor.get('party'),
                cosponsor.get('state'),
                cosponsor.get('sponsorshipDate')
            ))
            count += 1
        
        return count
    
    @with_db_transaction
    def update_bill_subjects(cursor, self, bill_number: str, subjects: List[Dict[str, Any]]) -> int:
        """Update bill subjects in the database."""
        # The decorator injects 'cursor' as the first parameter, shifting 'self' to second position
        
        if not subjects:
            return 0
        
        # Check if the bill exists in the database with this exact bill_number
        cursor.execute("SELECT 1 FROM bills WHERE bill_number = %s", (bill_number,))
        if not cursor.fetchone():
            # Try uppercase version
            uppercase_bill_number = bill_number.upper()
            cursor.execute("SELECT 1 FROM bills WHERE bill_number = %s", (uppercase_bill_number,))
            if cursor.fetchone():
                bill_number = uppercase_bill_number
            else:
                logger.warning(f"Bill {bill_number} not found in database, cannot update subjects")
                return 0
        
        count = 0
        for subject in subjects:
            cursor.execute("""
                INSERT INTO bill_subjects (bill_number, subject_name)
                VALUES (%s, %s)
                ON CONFLICT (bill_number, subject_name) DO NOTHING
            """, (
                bill_number,
                subject.get('name')
            ))
            count += 1
        
        return count
    
    @with_db_transaction
    def update_bill_related_bills(cursor, self, bill_number: str, related_bills: List[Dict[str, Any]]) -> int:
        """Update related bills in the database."""
        # The decorator injects 'cursor' as the first parameter, shifting 'self' to second position
        
        if not related_bills:
            return 0
        
        # Check if the bill exists in the database with this exact bill_number
        cursor.execute("SELECT 1 FROM bills WHERE bill_number = %s", (bill_number,))
        if not cursor.fetchone():
            # Try uppercase version
            uppercase_bill_number = bill_number.upper()
            cursor.execute("SELECT 1 FROM bills WHERE bill_number = %s", (uppercase_bill_number,))
            if cursor.fetchone():
                bill_number = uppercase_bill_number
            else:
                logger.warning(f"Bill {bill_number} not found in database, cannot update related bills")
                return 0
            
        # Convert to array of bill numbers
        related_bill_numbers = [f"{rb.get('type', '')}{rb.get('number', '')}" 
                              for rb in related_bills if rb.get('type') and rb.get('number')]
        
        if not related_bill_numbers:
            return 0
        
        # Update the related_bills array in the bills table
        cursor.execute("""
            UPDATE bills
            SET related_bills = %s::text[]
            WHERE bill_number = %s
        """, (related_bill_numbers, bill_number))
        
        return len(related_bill_numbers)
    
    def process_bill(self, congress: str, bill_type: str, bill_number: str) -> Dict[str, Any]:
        """Process a single bill, fetching and updating all related data."""
        results = {
            "bill_number": f"{bill_type}{bill_number}",
            "congress": congress,
            "status": "success",
            "details_updated": False,
            "actions_updated": 0,
            "cosponsors_updated": 0,
            "subjects_updated": 0,
            "related_bills_updated": 0,
        }
        
        try:
            # Fetch bill details
            bill_data = self.fetch_bill_detail(congress, bill_type, bill_number)
            
            # Ensure congress is a string before passing to save_bill_data
            congress_str = str(congress)
            self.save_bill_data(bill_data, congress_str, bill_type, bill_number, 'details')
            
            # Handle different bill structures
            if isinstance(bill_data['bill'], list):
                # For older bills (array structure)
                if not bill_data['bill']:  # Empty array
                    logger.warning(f"Bill data contains empty bill array for {bill_type}{bill_number}")
                    results["status"] = "failed"
                    results["error"] = "Empty bill array"
                    return results
                    
                # Sort by updateDate (descending) and use the most recently updated entry
                sorted_bills = sorted(bill_data['bill'], 
                                    key=lambda x: x.get('updateDate', ''), 
                                    reverse=True)
                bill = sorted_bills[0]
                
                # Log that we found multiple entries
                if len(bill_data['bill']) > 1:
                    logger.info(f"Multiple bill entries found for {bill_type}{bill_number}. "
                              f"Using most recently updated entry from {bill.get('updateDate', 'unknown date')}")
            else:
                # For newer bills (dictionary structure)
                bill = bill_data['bill']
                
            full_bill_number = f"{bill_type}{bill_number}".upper()
            
            # Fetch text versions if available
            text_versions_data = None
            if 'textVersions' in bill and 'url' in bill['textVersions']:
                try:
                    text_versions_url = bill['textVersions']['url']
                    text_versions_data = self.fetch_text_versions(text_versions_url)
                    self.save_bill_data(text_versions_data, congress_str, bill_type, bill_number, 'text')
                except Exception as e:
                    logger.error(f"Error fetching text versions for bill {full_bill_number}: {str(e)}")
            
            # Fetch summaries if available
            summaries_data = None
            if 'summaries' in bill and 'url' in bill['summaries']:
                try:
                    summaries_url = bill['summaries']['url']
                    summaries_data = self.fetch_bill_summaries(summaries_url)
                    self.save_bill_data(summaries_data, congress_str, bill_type, bill_number, 'summaries')
                except Exception as e:
                    logger.error(f"Error fetching summaries for bill {full_bill_number}: {str(e)}")
            
            # Update bill details
            results["details_updated"] = self.update_bill_details(
                bill_data=bill_data, 
                text_versions_data=text_versions_data, 
                summaries_data=summaries_data
            )
            
            # Fetch and update actions
            actions_data = None
            if 'actions' in bill and 'url' in bill['actions']:
                try:
                    actions_url = bill['actions']['url']
                    actions_data = self.fetch_bill_actions(actions_url)
                    self.save_bill_data(actions_data, congress_str, bill_type, bill_number, 'actions')
                    results["actions_updated"] = self.update_bill_actions(
                        bill_number=full_bill_number, 
                        actions_data=actions_data
                    )
                except Exception as e:
                    logger.error(f"Error processing actions for bill {full_bill_number}: {str(e)}")
            
            # Fetch and update cosponsors
            if 'cosponsors' in bill and 'url' in bill['cosponsors']:
                try:
                    cosponsors_url = bill['cosponsors']['url']
                    cosponsors_data = self.fetch_bill_cosponsors(cosponsors_url)
                    self.save_bill_data(cosponsors_data, congress_str, bill_type, bill_number, 'cosponsors')
                    
                    if 'cosponsors' in cosponsors_data:
                        results["cosponsors_updated"] = self.update_bill_cosponsors(
                            bill_number=full_bill_number, 
                            cosponsors=cosponsors_data['cosponsors']
                        )
                except Exception as e:
                    logger.error(f"Error processing cosponsors for bill {full_bill_number}: {str(e)}")
            
            # Fetch and update subjects
            if 'subjects' in bill and 'url' in bill['subjects']:
                try:
                    subjects_url = bill['subjects']['url']
                    subjects_data = self.fetch_bill_subjects(subjects_url)
                    self.save_bill_data(subjects_data, congress_str, bill_type, bill_number, 'subjects')
                    
                    if 'subjects' in subjects_data and 'legislativeSubjects' in subjects_data['subjects']:
                        legislative_subjects = subjects_data['subjects']['legislativeSubjects']
                        if legislative_subjects:
                            results["subjects_updated"] = self.update_bill_subjects(
                                bill_number=full_bill_number, 
                                subjects=legislative_subjects
                            )
                except Exception as e:
                    logger.error(f"Error processing subjects for bill {full_bill_number}: {str(e)}")
            
            # Update related bills
            if 'relatedBills' in bill:
                related_bills_items = []
                if isinstance(bill['relatedBills'], dict) and 'item' in bill['relatedBills']:
                    related_bills_items = bill['relatedBills']['item']
                elif isinstance(bill['relatedBills'], list):
                    related_bills_items = bill['relatedBills']
                
                if related_bills_items:
                    try:
                        results["related_bills_updated"] = self.update_bill_related_bills(
                            bill_number=full_bill_number, 
                            related_bills=related_bills_items
                        )
                    except Exception as e:
                        logger.error(f"Error processing related bills for bill {full_bill_number}: {str(e)}")
            
            logger.info(f"Successfully processed bill {full_bill_number}")
            
        except Exception as e:
            logger.error(f"Error processing bill {bill_type}{bill_number}: {str(e)}", exc_info=True)
            results["status"] = "failed"
            results["error"] = str(e)
        
        return results

def get_bills_for_processing(only_recent: bool = True, limit: int = 100) -> List[Tuple[str, str, str]]:
    """Get bills from the database for processing."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if only_recent:
                # Get recently updated bills
                cur.execute("""
                    SELECT bill_number, congress
                    FROM bills
                    ORDER BY last_updated DESC
                    LIMIT %s
                """, (limit,))
            else:
                # Get bills with missing details or enrichment
                cur.execute("""
                    SELECT bill_number, congress
                    FROM bills
                    WHERE text_versions IS NULL
                       OR NOT EXISTS (SELECT 1 FROM bill_actions WHERE bill_actions.bill_number = bills.bill_number)
                       OR NOT EXISTS (SELECT 1 FROM bill_subjects WHERE bill_subjects.bill_number = bills.bill_number)
                       OR (
                           bills.sponsor_id IS NOT NULL
                           AND NOT EXISTS (SELECT 1 FROM bill_cosponsors WHERE bill_cosponsors.bill_number = bills.bill_number)
                       )
                    ORDER BY introduced_date DESC
                    LIMIT %s
                """, (limit,))
            
            bills = []
            for bill_number, congress in cur.fetchall():
                bill_type, bill_num = parse_bill_number(bill_number)
                bills.append((congress, bill_type, bill_num))
            
            return bills

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
            """, (BILL_DETAIL_ENDPOINT, processed, status, error))
            conn.commit()

def main():
    parser = argparse.ArgumentParser(description='Process bill details and enrichments')
    parser.add_argument('--bill', help='Process specific bill (format: HR1234)')
    parser.add_argument('--congress', help='Congress number for specific bill')
    parser.add_argument('--limit', type=int, default=100, help='Maximum bills to process')
    parser.add_argument('--all', action='store_true', help='Process all bills that need details')
    parser.add_argument('--recent', action='store_true', help='Process only recently updated bills')
    args = parser.parse_args()
    
    try:
        # Initialize API client
        api_client = APIClient(BASE_API_URL)
        processor = BillProcessor(api_client)
        
        # Update status to in-progress
        update_sync_status('in_progress')
        
        # Determine which bills to process
        if args.bill and args.congress:
            # Process single specified bill
            bill_type, bill_number = parse_bill_number(args.bill)
            bills_to_process = [(args.congress, bill_type, bill_number)]
            logger.info(f"Processing single bill: {args.congress} {bill_type}{bill_number}")
        else:
            # Get bills from database
            only_recent = not args.all
            bills_to_process = get_bills_for_processing(only_recent, args.limit)
            logger.info(f"Processing {len(bills_to_process)} bills")
        
        # Process each bill
        results = []
        processed_count = 0
        error_count = 0
        
        for congress, bill_type, bill_number in bills_to_process:
            try:
                result = processor.process_bill(congress, bill_type, bill_number)
                results.append(result)
                
                if result['status'] == 'success':
                    processed_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing bill {bill_type}{bill_number}: {str(e)}", exc_info=True)
                error_count += 1
        
        # Clean up old files
        cleanup_old_files(os.path.join(os.path.dirname(__file__), 'raw', 'details'), 
                         pattern='*', days=RAW_DATA_RETENTION_DAYS)
        
        # Update sync status to success
        if error_count == 0:
            update_sync_status('success', processed_count)
        else:
            update_sync_status('completed_with_errors', processed_count, error_count)
        
        logger.info(f"Process completed. {processed_count} bills processed successfully, {error_count} errors.")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        update_sync_status('failed', error=str(e))
        raise

if __name__ == "__main__":
    main()
