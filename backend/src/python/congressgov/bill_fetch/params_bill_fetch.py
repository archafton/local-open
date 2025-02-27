# parameterized_bill_fetch.py
import os
import json
import requests
import psycopg2
import logging
import argparse
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Import the tag utilities
from tag_utils import get_or_create_policy_area_tag, update_bill_tags

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key and endpoint from environment variables
API_KEY = os.getenv('CONGRESSGOV_API_KEY')
BILLS_LIST_ENDPOINT = os.getenv('CONGRESSGOV_BILLS_LIST_ENDPOINT')
DATABASE_URL = os.getenv('DATABASE_URL')

def fetch_bills(start_date=None, end_date=None, offset=0, limit=250):
    """
    Fetch bills from the Congress.gov API with optional date filtering
    """
    params = {
        'api_key': API_KEY,
        'format': 'json',
        'limit': limit,
        'offset': offset,
        'sort': 'updateDate desc'
    }
    
    # Add date filtering if provided
    if start_date:
        params['fromDateTime'] = start_date.strftime("%Y-%m-%dT00:00:00Z")
    if end_date:
        params['toDateTime'] = end_date.strftime("%Y-%m-%dT23:59:59Z")
    
    response = requests.get(BILLS_LIST_ENDPOINT, params=params)
    response.raise_for_status()
    return response.json()

def fetch_all_bills(start_date=None, end_date=None, limit=250):
    """
    Fetch all bills using pagination with optional date filtering
    """
    all_bills = {'bills': []}
    offset = 0
    total_count = None
    
    while True:
        data = fetch_bills(start_date, end_date, offset, limit)
        
        if 'bills' in data:
            all_bills['bills'].extend(data['bills'])
        
        # Get total count from first response
        if total_count is None and 'pagination' in data:
            total_count = data['pagination'].get('count')
            logger.info(f"Total bills to fetch: {total_count}")
        
        # Check if we need to continue
        if 'pagination' not in data or 'next' not in data['pagination']:
            break
            
        offset += limit
        
        # Safety check
        if offset >= (total_count or float('inf')):
            break
    
    return all_bills

def normalize_status(action_text):
    """
    Map action text to a normalized status value
    """
    # Same implementation as original
    # ... [code omitted for brevity]

def ensure_raw_directory():
    """
    Ensure that the 'raw' directory exists
    """
    raw_dir = os.path.join(os.path.dirname(__file__), 'raw')
    if not os.path.exists(raw_dir):
        os.makedirs(raw_dir)
    return raw_dir

def save_to_json(data, filename):
    """
    Save data to a JSON file in the 'raw' directory
    """
    raw_dir = ensure_raw_directory()
    file_path = os.path.join(raw_dir, filename)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    return file_path

def update_database(bills):
    """
    Update the database with bill information
    """
    # Same implementation as original with imported tag utilities
    # ... [code omitted for brevity]

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Fetch bills from Congress.gov API with optional date filtering')
    parser.add_argument('--start_date', help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end_date', help='End date in YYYY-MM-DD format')
    parser.add_argument('--days', type=int, help='Number of days to look back from today')
    parser.add_argument('--congress', type=int, help='Congress number to fetch (e.g., 117)')
    args = parser.parse_args()
    
    # Process date arguments
    start_date = None
    end_date = None
    
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    
    if args.days and not start_date:
        start_date = datetime.now() - timedelta(days=args.days)
    
    # Congress filter would need to be added to the API call if supported
    
    # Log the parameters
    if start_date:
        logger.info(f"Fetching bills from {start_date.strftime('%Y-%m-%d')}")
    if end_date:
        logger.info(f"Fetching bills to {end_date.strftime('%Y-%m-%d')}")
    
    try:
        # Fetch bills with parameters
        bills_data = fetch_all_bills(start_date, end_date)
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bills_{timestamp}.json"
        file_path = save_to_json(bills_data, filename)
        logger.info(f"Bills data saved to {file_path}")

        # Update database
        update_database(bills_data)

    except requests.RequestException as e:
        logger.error(f"An error occurred while fetching data: {str(e)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()