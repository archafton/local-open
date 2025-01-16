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

# Load environment variables
load_dotenv()

# Get API key and endpoints from environment variables
API_KEY = os.getenv('CONGRESSGOV_API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
API_BASE_URL = "https://api.congress.gov/v3/bill"

def parse_bill_number(bill_number: str) -> tuple[str, str]:
    """
    Parse a bill number into its components
    Example: 'SJRES33' -> ('sjres', '33')
    """
    for i, c in enumerate(bill_number):
        if c.isdigit():
            return bill_number[:i].lower(), bill_number[i:]
    return bill_number.lower(), ''

def fetch_bill_detail(congress: str, bill_type: str, bill_number: str) -> Dict[str, Any]:
    """
    Fetch detailed information for a specific bill from the Congress.gov API
    """
    url = f"{API_BASE_URL}/{congress}/{bill_type}/{bill_number}"
    params = {
        'api_key': API_KEY,
        'format': 'json'
    }
    
    logger.info(f"Fetching bill details from: {url}")
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def fetch_text_versions(congress: str, bill_type: str, bill_number: str) -> Dict[str, Any]:
    """
    Fetch text versions for a specific bill
    """
    url = f"{API_BASE_URL}/{congress}/{bill_type}/{bill_number}/text"
    params = {
        'api_key': API_KEY,
        'format': 'json'
    }
    
    logger.info(f"Fetching text versions from: {url}")
    response = requests.get(url, params=params)
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

def update_database(bill_detail: Dict[str, Any], text_versions_data: Optional[Dict[str, Any]] = None):
    """
    Update the database with detailed bill information
    """
    logger.info(f"Starting update_database function for bill: {bill_detail['bill']['type']}{bill_detail['bill']['number']}")
    conn = None
    try:
        logger.info(f"Attempting to connect to database: {DATABASE_URL}")
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("Database connection successful")
        cur = conn.cursor()

        bill = bill_detail['bill']
        bill_number = f"{bill['type']}{bill['number']}"
        
        # Process text versions with introduced date
        text_versions = []
        if text_versions_data and 'textVersions' in text_versions_data:
            text_versions = process_text_versions(
                text_versions_data['textVersions'],
                bill.get('introducedDate')
            )
            logger.info(f"Processed {len(text_versions)} text versions")

        # Handle summaries
        summaries = []
        if 'summaries' in bill:
            if isinstance(bill['summaries'], dict) and bill['summaries'].get('count', 0) > 0:
                summary_url = bill['summaries']['url']
                summary_response = requests.get(summary_url, params={'api_key': API_KEY, 'format': 'json'})
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    if 'summaries' in summary_data:
                        summaries = [{
                            'version_code': s.get('versionCode'),
                            'action_date': s.get('actionDate'),
                            'action_desc': s.get('actionDesc'),
                            'text': s.get('text')
                        } for s in summary_data['summaries']]

        update_query = """
            UPDATE bills SET
                bill_title = %s,
                sponsor_id = %s,
                introduced_date = %s,
                summary = %s,
                tags = %s,
                congress = %s,
                status = %s,
                text_versions = %s::jsonb
            WHERE bill_number = %s
        """
        
        update_values = (
            bill.get('title', ''),
            bill.get('sponsors', [{}])[0].get('bioguideId') if bill.get('sponsors') else None,
            bill.get('introducedDate'),
            json.dumps(summaries) if summaries else None,
            [bill.get('policyArea', {}).get('name')] if bill.get('policyArea') else None,
            bill.get('congress'),
            bill.get('latestAction', {}).get('text', ''),
            json.dumps(text_versions) if text_versions else None,
            bill_number
        )
        
        logger.info(f"Executing update query for bill {bill_number}")
        cur.execute(update_query, update_values)
        rows_affected = cur.rowcount
        
        if rows_affected == 0:
            logger.warning(f"No rows updated for bill {bill_number}. Bill may not exist in the database.")
        else:
            conn.commit()
            logger.info(f"Database updated successfully for bill {bill_number}. Rows affected: {rows_affected}")
    except Exception as error:
        logger.error(f"Unexpected error while updating database for bill {bill_number}: {error}")
        logger.error(f"Error type: {type(error)}")
        logger.error(f"Error args: {error.args}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cur.close()
            conn.close()
            logger.info("Database connection closed.")

def get_bills_from_database() -> List[tuple[str, str]]:
    """
    Retrieve all bill numbers from the database
    """
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT bill_number, congress FROM bills")
        return cur.fetchall()
    except Exception as error:
        logger.error(f"Error while fetching bills from database: {error}")
        raise
    finally:
        if conn:
            cur.close()
            conn.close()

def main():
    logger.info("Starting bill detail fetch process")
    storage = BillStorage()
    bills = get_bills_from_database()
    logger.info(f"Retrieved {len(bills)} bills from database")
    
    for bill_number, congress in bills:
        try:
            # Parse bill number into type and number
            bill_type, bill_num = parse_bill_number(bill_number)
            logger.info(f"Processing bill: {bill_number}, Congress: {congress}, Type: {bill_type}, Number: {bill_num}")
            
            # Fetch and save bill details
            logger.info("Fetching bill details...")
            bill_data = fetch_bill_detail(congress, bill_type, bill_num)
            storage.save_bill_data(congress, bill_type, bill_num, 'details', bill_data)

            # Fetch and save text versions
            logger.info("Fetching text versions...")
            text_versions_data = fetch_text_versions(congress, bill_type, bill_num)
            storage.save_bill_data(congress, bill_type, bill_num, 'text', text_versions_data)

            # Update database with processed data
            update_database(bill_data, text_versions_data)

        except requests.RequestException as e:
            logger.error(f"API request failed for bill {bill_number}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing bill {bill_number}: {str(e)}")
            logger.exception(e)

    logger.info("Bill detail fetch process completed")

if __name__ == "__main__":
    main()
