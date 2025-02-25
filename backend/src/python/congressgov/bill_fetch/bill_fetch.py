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

def normalize_status(action_text):
    """
    Map action text to a normalized status value
    """
    if not action_text:
        return None
        
    action_text = action_text.lower()
    
    # Direct matches first
    if any(term in action_text for term in ['became public law', 'became law']):
        return 'Became Law'
    elif any(term in action_text for term in ['enacted', 'approved by president']):
        return 'Enacted'
    elif 'passed' in action_text:
        if 'house' in action_text:
            return 'Passed House'
        elif 'senate' in action_text:
            return 'Passed Senate'
    
    # Calendar placements indicate progress beyond committee
    if 'placed on' in action_text and 'calendar' in action_text:
        if 'senate' in action_text:
            return 'Reported'  # Senate calendar placement typically follows committee reporting
        elif 'union calendar' in action_text:
            return 'Reported'  # House Union Calendar is for reported bills
        
    # Committee actions
    if any(term in action_text for term in ['reported', 'ordered to be reported']):
        return 'Reported'
    elif any(term in action_text for term in ['referred to', 'committee']):
        return 'In Committee'
    elif 'held at the desk' in action_text:
        return 'In Committee'  # Bills held at the desk are awaiting committee referral
        
    # Introduction status
    if any(term in action_text for term in ['introduced', 'introduction']):
        return 'Introduced'
    
    # Motion outcomes often indicate passage
    if 'motion to reconsider laid on the table agreed to' in action_text:
        if 'house' in action_text:
            return 'Passed House'
        elif 'senate' in action_text:
            return 'Passed Senate'
    
    return None

def normalize_tag_name(name):
    """Convert a tag name to its normalized form"""
    if not name:
        return None
    return name.lower().replace(' ', '_').replace(',', '_').replace('&', 'and').replace('-', '_')

def get_or_create_policy_area_tag(cur, policy_area_name):
    """
    Get or create a policy area tag, ensuring it exists in the hierarchical tag system
    """
    if not policy_area_name:
        return None

    # First, get the Policy Area tag type ID
    cur.execute("SELECT id FROM tag_types WHERE name = 'Policy Area'")
    result = cur.fetchone()
    if not result:
        logging.error("Policy Area tag type not found")
        return None
    
    type_id = result[0]
    normalized_name = normalize_tag_name(policy_area_name)

    # Try to find existing tag
    cur.execute("""
        SELECT id FROM tags 
        WHERE type_id = %s AND normalized_name = %s
    """, (type_id, normalized_name))
    result = cur.fetchone()
    
    if result:
        return result[0]

    # Create new tag if it doesn't exist
    cur.execute("""
        INSERT INTO tags (type_id, name, normalized_name, description)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (
        type_id,
        policy_area_name,
        normalized_name,
        f'Bills related to {policy_area_name}'
    ))
    return cur.fetchone()[0]

def update_bill_tags(cur, bill_id, tag_id):
    """
    Update bill-tag relationships in the bill_tags table
    """
    if not tag_id:
        return

    cur.execute("""
        INSERT INTO bill_tags (bill_id, tag_id)
        VALUES (%s, %s)
        ON CONFLICT (bill_id, tag_id) DO NOTHING
    """, (bill_id, tag_id))

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
            congress = bill.get('congress')
            action_text = bill.get('latestAction', {}).get('text', '')
            status = action_text
            normalized_status = normalize_status(action_text)
            bill_text = None  # bill_text will be fetched separately

            # Insert or update bill and get its ID
            cur.execute("""
                INSERT INTO bills (
                    bill_number, bill_title, sponsor_id, introduced_date, 
                    summary, congress, status, bill_text, normalized_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (bill_number) DO UPDATE SET
                    bill_title = EXCLUDED.bill_title,
                    sponsor_id = EXCLUDED.sponsor_id,
                    introduced_date = EXCLUDED.introduced_date,
                    summary = EXCLUDED.summary,
                    congress = EXCLUDED.congress,
                    status = EXCLUDED.status,
                    bill_text = EXCLUDED.bill_text,
                    normalized_status = EXCLUDED.normalized_status
                RETURNING id
            """, (
                bill_number, bill_title, sponsor_id, introduced_date,
                summary, congress, status, bill_text, normalized_status
            ))
            bill_id = cur.fetchone()[0]

            # Handle policy area tag
            policy_area_name = bill.get('policyArea', {}).get('name')
            if policy_area_name:
                tag_id = get_or_create_policy_area_tag(cur, policy_area_name)
                if tag_id:
                    update_bill_tags(cur, bill_id, tag_id)

        conn.commit()
        logging.info("Database updated successfully")
    except (Exception, psycopg2.Error) as error:
        logging.error(f"Error while connecting to PostgreSQL or updating database: {error}")
        if conn:
            conn.rollback()
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
