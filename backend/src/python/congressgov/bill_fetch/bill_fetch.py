import os
import json
import requests
import psycopg2
import logging
from dotenv import load_dotenv
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Get API key and endpoint from environment variables
API_KEY = os.getenv('CONGRESSGOV_API_KEY')
BILLS_LIST_ENDPOINT = os.getenv('CONGRESSGOV_BILLS_LIST_ENDPOINT')
DATABASE_URL = os.getenv('DATABASE_URL')

def fetch_bills():
    """
    Fetch bills from the Congress.gov API
    """
    params = {
        'api_key': API_KEY,
        'format': 'json',
        'limit': 250,
        'sort': 'updateDate desc'
    }
    
    response = requests.get(BILLS_LIST_ENDPOINT, params=params)
    response.raise_for_status()
    return response.json()

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
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        for bill in bills.get('bills', []):
            # Safely get values with default fallbacks
            bill_number = f"{bill.get('type', '')}{bill.get('number', '')}"
            bill_title = bill.get('title', '')
            sponsor_id = bill.get('sponsors', [{}])[0].get('bioguideId') if bill.get('sponsors') else None
            introduced_date = bill.get('introducedDate')
            summary = None  # summary will be fetched separately
            tags = [bill.get('policyArea', {}).get('name')] if bill.get('policyArea') else None
            congress = bill.get('congress')
            status = bill.get('latestAction', {}).get('text', '')
            bill_text = None  # bill_text will be fetched separately

            cur.execute("""
                INSERT INTO bills (
                    bill_number, bill_title, sponsor_id, introduced_date, 
                    summary, tags, congress, status, bill_text
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (bill_number) DO UPDATE SET
                    bill_title = EXCLUDED.bill_title,
                    sponsor_id = EXCLUDED.sponsor_id,
                    introduced_date = EXCLUDED.introduced_date,
                    summary = EXCLUDED.summary,
                    tags = EXCLUDED.tags,
                    congress = EXCLUDED.congress,
                    status = EXCLUDED.status,
                    bill_text = EXCLUDED.bill_text
            """, (
                bill_number, bill_title, sponsor_id, introduced_date,
                summary, tags, congress, status, bill_text
            ))

        conn.commit()
        logging.info("Database updated successfully")
    except (Exception, psycopg2.Error) as error:
        logging.error(f"Error while connecting to PostgreSQL or updating database: {error}")
    finally:
        if conn:
            cur.close()
            conn.close()

def main():
    try:
        bills_data = fetch_bills()
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bills_{timestamp}.json"
        file_path = save_to_json(bills_data, filename)
        logging.info(f"Bills data saved to {file_path}")

        # Update database
        update_database(bills_data)

    except requests.RequestException as e:
        logging.error(f"An error occurred while fetching data: {str(e)}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
