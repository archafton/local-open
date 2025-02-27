import os
import json
import requests
import psycopg2
import logging
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Any, List, Optional
from bill_storage import BillStorage  # Changed from relative to absolute import

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('bill_enrichment.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Load environment variables
load_dotenv()

# Get API key and endpoint from environment variables
API_KEY = os.getenv('CONGRESSGOV_API_KEY')
BILL_DETAIL_ENDPOINT = os.getenv('CONGRESSGOV_BILL_DETAIL_ENDPOINT')
DATABASE_URL = os.getenv('DATABASE_URL')

def fetch_text_versions(text_versions_url: str) -> Dict[str, Any]:
    """
    Fetch text versions from the provided URL
    """
    params = {
        'api_key': API_KEY,
        'format': 'json'
    }
    
    logger.info(f"Fetching text versions from: {text_versions_url}")
    response = requests.get(text_versions_url, params=params)
    response.raise_for_status()
    return response.json()

def process_text_versions(versions: List[Dict[str, Any]], introduced_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Process text versions to handle special cases
    """
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

def update_bill_info(cur, bill_data: Dict[str, Any], text_versions_data: Optional[Dict[str, Any]] = None):
    """
    Update the bills table with enriched information
    """
    bill = bill_data['bill']
    bill_number = f"{bill['type']}{bill['number']}"
    
    logger.info(f"Processing bill: {bill_number}")
    logger.debug(f"Bill data: {json.dumps(bill, indent=2)}")

    # Handle relatedBills - convert to text array
    related_bills = []
    if 'relatedBills' in bill:
        if isinstance(bill['relatedBills'], dict) and 'item' in bill['relatedBills']:
            related_bills = [f"{rb.get('type', '')}{rb.get('number', '')}" for rb in bill['relatedBills']['item']]
        elif isinstance(bill['relatedBills'], list):
            related_bills = [f"{rb.get('type', '')}{rb.get('number', '')}" for rb in bill['relatedBills']]

    # Process text versions with introduced date
    text_versions = []
    if text_versions_data and 'textVersions' in text_versions_data:
        text_versions = process_text_versions(
            text_versions_data['textVersions'],
            bill.get('introducedDate')
        )

    text_versions_json = json.dumps(text_versions)

    cur.execute("""
        UPDATE bills SET
            related_bills = %s,
            text_versions = %s::jsonb
        WHERE bill_number = %s
    """, (related_bills, text_versions_json, bill_number))
    logger.info(f"Updated bill info for {bill_number}")

def fetch_bill_details(congress: str, bill_type: str, bill_number: str) -> Dict[str, Any]:
    """
    Fetch detailed bill information from the Congress.gov API
    """
    params = {
        'api_key': API_KEY,
        'format': 'json'
    }
    
    endpoint = BILL_DETAIL_ENDPOINT.format(congress=congress, billType=bill_type, billNumber=bill_number)
    logger.info(f"Fetching bill details from: {endpoint}")
    response = requests.get(endpoint, params=params)
    response.raise_for_status()
    return response.json()

def fetch_bill_actions(actions_url: str) -> Dict[str, Any]:
    """
    Fetch bill actions from the Congress.gov API using the provided URL
    """
    params = {
        'api_key': API_KEY,
        'format': 'json'
    }
    
    logger.info(f"Fetching bill actions from: {actions_url}")
    response = requests.get(actions_url, params=params)
    response.raise_for_status()
    return response.json()

def insert_bill_actions(cur, bill_number: str, actions_data: Dict[str, Any]):
    """
    Insert bill actions into the bill_actions table
    """
    if not actions_data or 'actions' not in actions_data:
        logger.warning(f"No actions found for bill {bill_number}")
        return

    actions = actions_data['actions']
    for action in actions:
        cur.execute("""
            INSERT INTO bill_actions (bill_number, action_date, action_text, action_type)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (bill_number, action_date, action_text) DO NOTHING
        """, (
            bill_number,
            action.get('actionDate'),
            action.get('text'),
            action.get('type')
        ))
    logger.info(f"Inserted {len(actions)} actions for bill {bill_number}")

def insert_bill_cosponsors(cur, bill_number: str, cosponsors: List[Dict[str, Any]]):
    """
    Insert bill cosponsors into the bill_cosponsors table
    """
    for cosponsor in cosponsors:
        cur.execute("""
            INSERT INTO bill_cosponsors (bill_number, cosponsor_id, cosponsor_name, cosponsor_party, cosponsor_state)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (bill_number, cosponsor_id) DO NOTHING
        """, (bill_number, cosponsor.get('bioguideId'), cosponsor.get('fullName'), cosponsor.get('party'), cosponsor.get('state')))
    logger.info(f"Inserted {len(cosponsors)} cosponsors for bill {bill_number}")

def insert_bill_subjects(cur, bill_number: str, subjects: List[Dict[str, Any]]):
    """
    Insert bill subjects into the bill_subjects table
    """
    for subject in subjects:
        cur.execute("""
            INSERT INTO bill_subjects (bill_number, subject_name)
            VALUES (%s, %s)
            ON CONFLICT (bill_number, subject_name) DO NOTHING
        """, (bill_number, subject.get('name')))
    logger.info(f"Inserted {len(subjects)} subjects for bill {bill_number}")

def main():
    storage = BillStorage()
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Fetch all bill numbers from the database
        cur.execute("SELECT bill_number, congress FROM bills")
        bills = cur.fetchall()
        logger.info(f"Found {len(bills)} bills to process")

        for bill_number, congress in bills:
            bill_type = ''.join(filter(str.isalpha, bill_number))
            bill_num = ''.join(filter(str.isdigit, bill_number))

            logger.info(f"Processing bill: {bill_number}, Congress: {congress}")

            try:
                # Fetch and save bill details
                logger.info("Fetching bill details...")
                bill_data = fetch_bill_details(congress, bill_type, bill_num)
                storage.save_bill_data(congress, bill_type, bill_num, 'details', bill_data)

                # Fetch text versions if available
                text_versions_data = None
                if 'textVersions' in bill_data['bill'] and 'url' in bill_data['bill']['textVersions']:
                    try:
                        text_versions_url = bill_data['bill']['textVersions']['url']
                        text_versions_data = fetch_text_versions(text_versions_url)
                        storage.save_bill_data(congress, bill_type, bill_num, 'text', text_versions_data)
                    except Exception as e:
                        logger.error(f"Error fetching text versions for bill {bill_number}: {str(e)}")
                
                # Get actions URL from bill details
                actions_url = bill_data['bill'].get('actions', {}).get('url')
                if actions_url:
                    logger.info("Fetching bill actions...")
                    actions_data = fetch_bill_actions(actions_url)
                    storage.save_bill_data(congress, bill_type, bill_num, 'actions', actions_data)
                else:
                    logger.warning(f"No actions URL found for bill {bill_number}")
                    actions_data = {'actions': []}
                
                logger.info("Updating bill info...")
                update_bill_info(cur, bill_data, text_versions_data)

                logger.info("Inserting bill actions...")
                insert_bill_actions(cur, bill_number, actions_data)

                logger.info("Inserting bill cosponsors...")
                insert_bill_cosponsors(cur, bill_number, bill_data['bill'].get('cosponsors', {}).get('item', []))

                logger.info("Inserting bill subjects...")
                insert_bill_subjects(cur, bill_number, bill_data['bill'].get('subjects', {}).get('item', []))

                conn.commit()
                logger.info(f"Successfully updated information for bill {bill_number}")
            except requests.RequestException as e:
                logger.error(f"Error fetching data for bill {bill_number}: {str(e)}")
                conn.rollback()
            except Exception as e:
                logger.error(f"Unexpected error processing bill {bill_number}: {str(e)}", exc_info=True)
                conn.rollback()

    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error while connecting to PostgreSQL or updating database: {error}", exc_info=True)
    finally:
        if conn:
            cur.close()
            conn.close()
        logger.info("Bill enrichment process completed")

if __name__ == "__main__":
    main()
