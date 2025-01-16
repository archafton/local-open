import os
import json
import requests
import psycopg2
import logging
from dotenv import load_dotenv
from datetime import datetime, date
from typing import Optional, Dict, Any
from glob import glob

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key and endpoint from environment variables
API_KEY = os.getenv('CONGRESSGOV_API_KEY')
MEMBERS_LIST_ENDPOINT = os.getenv('CONGRESSGOV_MEMBER_LIST_ENDPOINT')
DATABASE_URL = os.getenv('DATABASE_URL')

# Constants
RECORDS_PER_PAGE = 250

def fetch_members_page(offset: int = 0) -> Dict[str, Any]:
    """
    Fetch a single page of members from the Congress.gov API
    """
    params = {
        'api_key': API_KEY,
        'format': 'json',
        'limit': RECORDS_PER_PAGE,
        'offset': offset,
        'sort': 'updateDate desc'
    }
    
    logger.info(f"Fetching members with offset {offset}")
    response = requests.get(MEMBERS_LIST_ENDPOINT, params=params)
    response.raise_for_status()
    return response.json()

def ensure_raw_directory(timestamp: str) -> str:
    """
    Ensure that the timestamped 'raw' directory exists
    Returns the path to the directory
    """
    raw_dir = os.path.join(os.path.dirname(__file__), 'raw', timestamp)
    os.makedirs(raw_dir, exist_ok=True)
    return raw_dir

def save_to_json(data: Dict[str, Any], timestamp: str, offset: int) -> str:
    """
    Save data to a JSON file in the timestamped directory
    """
    raw_dir = ensure_raw_directory(timestamp)
    filename = f"members_offset_{offset:04d}.json"
    file_path = os.path.join(raw_dir, filename)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved members data to {file_path}")
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

def load_latest_data() -> list:
    """
    Load all member data from the most recent data directory
    """
    latest_dir = get_latest_data_directory()
    if not latest_dir:
        logger.warning("No data directories found")
        return []

    all_members = []
    json_files = sorted(glob(os.path.join(latest_dir, 'members_offset_*.json')))
    
    for file_path in json_files:
        logger.info(f"Loading data from {file_path}")
        with open(file_path, 'r') as f:
            data = json.load(f)
            if 'members' in data:
                all_members.extend(data['members'])
    
    return all_members

def year_to_date(year: Optional[str]) -> Optional[date]:
    """
    Convert a year to a date object (January 1st of that year)
    """
    if year is None:
        return None
    try:
        return date(int(year), 1, 1)
    except ValueError:
        return None

def update_database(members: list):
    """
    Update the database with member information
    """
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        for member in members:
            bioguide_id = member.get('bioguideId')
            name_parts = member.get('name', '').split(', ')
            last_name = name_parts[0] if len(name_parts) > 0 else ''
            first_name = name_parts[1] if len(name_parts) > 1 else ''
            full_name = member.get('name', '').replace(', ', ' ') or f"{first_name} {last_name}".strip()
            state = member.get('state')
            district = member.get('district')
            party = member.get('partyName')
            terms = member.get('terms', {}).get('item', [])
            current_term = terms[-1] if terms else {}
            chamber = current_term.get('chamber')
            start_year = current_term.get('startYear')
            end_year = current_term.get('endYear')
            depiction = member.get('depiction', {})
            photo_url = depiction.get('imageUrl')
            update_date = member.get('updateDate')
            
            # Determine if the member is current based on the end_year of their latest term
            current_year = datetime.now().year
            current_member = end_year is None or int(end_year) >= current_year

            cur.execute("""
                INSERT INTO members (
                    bioguide_id, first_name, last_name, full_name, state, district, party, 
                    chamber, photo_url, last_updated, current_member
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (bioguide_id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    full_name = EXCLUDED.full_name,
                    state = EXCLUDED.state,
                    district = EXCLUDED.district,
                    party = EXCLUDED.party,
                    chamber = EXCLUDED.chamber,
                    photo_url = EXCLUDED.photo_url,
                    last_updated = EXCLUDED.last_updated,
                    current_member = EXCLUDED.current_member
            """, (
                bioguide_id, first_name, last_name, full_name, state, district, party,
                chamber, photo_url, update_date, current_member
            ))

            # Insert member terms
            for term in terms:
                cur.execute("""
                    INSERT INTO member_terms (
                        member_id, congress, chamber, party, state, start_date, end_date
                    ) VALUES (
                        (SELECT id FROM members WHERE bioguide_id = %s),
                        %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (member_id, congress, chamber) DO UPDATE SET
                        party = EXCLUDED.party,
                        state = EXCLUDED.state,
                        start_date = EXCLUDED.start_date,
                        end_date = EXCLUDED.end_date
                """, (
                    bioguide_id,
                    None,  # Congress information is not provided in the current data
                    term.get('chamber'),
                    party,
                    state,
                    year_to_date(term.get('startYear')),
                    year_to_date(term.get('endYear'))
                ))

        conn.commit()
        logger.info("Database updated successfully")
    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error while connecting to PostgreSQL or updating database: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

def fetch_all_members(timestamp: str):
    """
    Fetch all members using pagination
    """
    offset = 0
    total_count = None
    
    while True:
        try:
            data = fetch_members_page(offset)
            save_to_json(data, timestamp, offset)
            
            # Get total count from first response
            if total_count is None and 'pagination' in data:
                total_count = data['pagination'].get('count')
                logger.info(f"Total members to fetch: {total_count}")
            
            # Check if we need to continue
            if 'pagination' not in data or 'next' not in data['pagination']:
                break
                
            offset += RECORDS_PER_PAGE
            
            # Safety check
            if offset >= (total_count or float('inf')):
                break
                
        except requests.RequestException as e:
            logger.error(f"Error fetching members at offset {offset}: {str(e)}")
            break

def main():
    try:
        # Create timestamp for this run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Check if we need to fetch new data
        latest_dir = get_latest_data_directory()
        if not latest_dir:
            logger.info("No existing data found. Fetching all members...")
            fetch_all_members(timestamp)
        else:
            logger.info(f"Using existing data from {latest_dir}")
        
        # Load and process the latest data
        members = load_latest_data()
        if members:
            logger.info(f"Processing {len(members)} members")
            update_database(members)
        else:
            logger.warning("No member data found to process")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()
