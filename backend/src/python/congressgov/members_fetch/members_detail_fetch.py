import os
import json
import requests
import psycopg2
import logging
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Any, Optional
from glob import glob

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='member_detail_fetch.log'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key and endpoints from environment variables
API_KEY = os.getenv('CONGRESSGOV_API_KEY')
MEMBER_DETAIL_ENDPOINT = os.getenv('CONGRESSGOV_MEMBER_DETAIL_ENDPOINT', 'https://api.congress.gov/v3/member/{bioguideId}')
DATABASE_URL = os.getenv('DATABASE_URL')

def fetch_member_detail(bioguide_id: str) -> Dict[str, Any]:
    """
    Fetch detailed information for a specific member from the Congress.gov API
    """
    # Replace the placeholder with the actual bioguide_id
    url = MEMBER_DETAIL_ENDPOINT.replace('{bioguideId}', bioguide_id)
    params = {
        'api_key': API_KEY,
        'format': 'json'
    }
    
    logger.info(f"Fetching details for member {bioguide_id}")
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if response.status_code == 404:
            logger.warning(f"Member {bioguide_id} not found in Congress.gov API")
        else:
            logger.error(f"Error fetching member {bioguide_id}: {str(e)}")
        raise

def ensure_raw_directory(timestamp: str) -> str:
    """
    Ensure that the timestamped 'raw/details' directory exists
    Returns the path to the directory
    """
    raw_dir = os.path.join(os.path.dirname(__file__), 'raw', timestamp, 'details')
    os.makedirs(raw_dir, exist_ok=True)
    return raw_dir

def save_to_json(data: Dict[str, Any], timestamp: str, bioguide_id: str) -> str:
    """
    Save member detail data to a JSON file in the timestamped directory
    """
    raw_dir = ensure_raw_directory(timestamp)
    filename = f"member_detail_{bioguide_id}.json"
    file_path = os.path.join(raw_dir, filename)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved member detail data to {file_path}")
    return file_path

def get_latest_data_directory() -> Optional[str]:
    """
    Get the path to the most recent data directory
    """
    base_dir = os.path.join(os.path.dirname(__file__), 'raw')
    if not os.path.exists(base_dir):
        return None
    
    dirs = glob(os.path.join(base_dir, '*'))
    if not dirs:
        return None
    
    # Get the most recent directory by timestamp
    latest_dir = max(dirs, key=os.path.getctime)
    return latest_dir

def update_database_with_details(member_data: Dict[str, Any]):
    """
    Update the database with detailed member information
    """
    if 'member' not in member_data:
        logger.warning("No member data found in response")
        return

    member = member_data['member']
    bioguide_id = member.get('bioguideId')
    
    if not bioguide_id:
        logger.warning("No bioguide ID found in member data")
        return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Update the members table with additional details
        cur.execute("""
            UPDATE members SET
                birth_year = %s,
                direct_order_name = %s,
                honorific_name = %s,
                inverted_order_name = %s,
                update_date = %s
            WHERE bioguide_id = %s
        """, (
            member.get('birthYear'),
            member.get('directOrderName'),
            member.get('honorificName'),
            member.get('invertedOrderName'),
            member.get('updateDate'),
            bioguide_id
        ))

        # Handle leadership positions
        leadership = member.get('leadership', [])
        for position in leadership:
            cur.execute("""
                INSERT INTO member_leadership (
                    member_id, congress, leadership_type
                ) VALUES (
                    (SELECT id FROM members WHERE bioguide_id = %s),
                    %s, %s
                ) ON CONFLICT (member_id, congress) DO UPDATE SET
                    leadership_type = EXCLUDED.leadership_type
            """, (
                bioguide_id,
                position.get('congress'),
                position.get('type')
            ))

        # Handle party history
        party_history = member.get('partyHistory', [])
        for party in party_history:
            cur.execute("""
                INSERT INTO member_party_history (
                    member_id, party_name, party_code, start_year
                ) VALUES (
                    (SELECT id FROM members WHERE bioguide_id = %s),
                    %s, %s, %s
                ) ON CONFLICT (member_id, start_year) DO UPDATE SET
                    party_name = EXCLUDED.party_name,
                    party_code = EXCLUDED.party_code
            """, (
                bioguide_id,
                party.get('partyName'),
                party.get('partyAbbreviation'),
                party.get('startYear')
            ))

        conn.commit()
        logger.info(f"Successfully updated database with details for member {bioguide_id}")

    except Exception as e:
        logger.error(f"Error updating database with member details: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

def get_all_bioguide_ids() -> list:
    """
    Get all bioguide IDs from the database
    """
    bioguide_ids = []
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("SELECT bioguide_id FROM members")
        bioguide_ids = [row[0] for row in cur.fetchall()]
        
    except Exception as e:
        logger.error(f"Error fetching bioguide IDs: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()
    
    return bioguide_ids

def main():
    try:
        # Create timestamp for this run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get all bioguide IDs from the database
        bioguide_ids = get_all_bioguide_ids()
        
        if not bioguide_ids:
            logger.warning("No bioguide IDs found in database")
            return
        
        logger.info(f"Found {len(bioguide_ids)} members to fetch details for")
        
        # Fetch and process details for each member
        for bioguide_id in bioguide_ids:
            try:
                member_data = fetch_member_detail(bioguide_id)
                save_to_json(member_data, timestamp, bioguide_id)
                update_database_with_details(member_data)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    # Skip 404 errors but log them at warning level
                    logger.warning(f"Member {bioguide_id} not found in Congress.gov API")
                    continue
                else:
                    logger.error(f"HTTP error processing member {bioguide_id}: {str(e)}")
                    continue
            except Exception as e:
                logger.error(f"Error processing member {bioguide_id}: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()
