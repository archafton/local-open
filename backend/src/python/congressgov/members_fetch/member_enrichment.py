#!/usr/bin/env python3
import os
import json
import shutil
import requests
import psycopg2
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv
from pathlib import Path

# Set up logging
script_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(script_dir, 'member_enrichment.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Starting member enrichment process. Log file: {log_file}")

# Load environment variables
load_dotenv()

# Get API key and endpoints from environment variables
API_KEY = os.getenv('CONGRESSGOV_API_KEY')
SPONSORED_ENDPOINT = os.getenv('CONGRESSGOV_SPONSORED_ENDPOINT')
COSPONSORED_ENDPOINT = os.getenv('CONGRESSGOV_COSPONSORED_ENDPOINT')
DATABASE_URL = os.getenv('DATABASE_URL')

# Constants
RECORDS_PER_PAGE = 20
RAW_DATA_RETENTION_DAYS = 30  # How many days to keep raw response files
API_CALL_DELAY = 2  # Seconds to wait between API calls
SYNC_STATUS_SUCCESS = 'success'
SYNC_STATUS_FAILED = 'failed'
SYNC_STATUS_IN_PROGRESS = 'in_progress'

class RetryStrategy:
    """Implements exponential backoff and retry logic"""
    def __init__(self, max_retries: int = 3, base_delay: int = 1):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def execute(self, func, *args, **kwargs) -> Any:
        """Executes function with retry logic"""
        import time
        from requests.exceptions import RequestException

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                delay = self.base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay} seconds...")
                time.sleep(delay)

class SyncManager:
    """Manages API sync status and progress tracking"""
    def __init__(self, db_url: str):
        self.db_url = db_url

    def get_sync_status(self, endpoint: str) -> Tuple[Optional[datetime], int]:
        """Gets the last sync timestamp and offset for an endpoint"""
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT last_sync_timestamp, last_successful_offset
                    FROM api_sync_status
                    WHERE endpoint = %s
                """, (endpoint,))
                result = cur.fetchone()
                return (result[0], result[1]) if result else (None, 0)

    def update_sync_status(self, endpoint: str, status: str, offset: int = 0, error: str = None):
        """Updates the sync status for an endpoint"""
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO api_sync_status (
                        endpoint, last_sync_timestamp, last_successful_offset,
                        status, last_error
                    ) VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s)
                    ON CONFLICT (endpoint) DO UPDATE SET
                        last_sync_timestamp = CURRENT_TIMESTAMP,
                        last_successful_offset = EXCLUDED.last_successful_offset,
                        status = EXCLUDED.status,
                        last_error = EXCLUDED.last_error
                """, (endpoint, offset, status, error))
            conn.commit()

class LegislationFetcher:
    """Handles API interactions and pagination"""
    def __init__(self, api_key: str, base_url: str, records_per_page: int = 20):
        self.api_key = api_key
        self.base_url = base_url
        self.records_per_page = records_per_page
        self.session = requests.Session()
        self.retry_strategy = RetryStrategy()

    def fetch_page(self, bioguide_id: str, offset: int = 0, from_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Fetches a single page with error handling and retries"""
        import time
        
        url = self.base_url.format(bioguideId=bioguide_id)
        params = {
            'api_key': self.api_key,
            'format': 'json',
            'limit': self.records_per_page,
            'offset': offset,
            'sort': 'updateDate desc'
        }
        
        if from_date:
            params['fromDateTime'] = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        def make_request():
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()

        # Add delay between API calls
        time.sleep(API_CALL_DELAY)
        return self.retry_strategy.execute(make_request)

    def fetch_all(self, bioguide_id: str, from_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Implements pagination with error recovery"""
        all_items = []
        offset = 0
        total_count = None

        while True:
            data = self.fetch_page(bioguide_id, offset, from_date)
            
            # Extract items based on the endpoint type
            if 'sponsoredLegislation' in data:
                items = data['sponsoredLegislation']
                pagination = data.get('pagination', {})
            elif 'cosponsoredLegislation' in data:
                items = data['cosponsoredLegislation']
                pagination = data.get('pagination', {})
            else:
                items = []
                pagination = {}

            if items:
                all_items.extend(items)

            # Get total count from first response
            if total_count is None and 'count' in pagination:
                total_count = pagination['count']
                logger.info(f"Total items to fetch for {bioguide_id}: {total_count}")

            # Check if we need to continue
            if 'next' not in pagination:
                break

            offset += self.records_per_page

            # Safety check
            if offset >= (total_count or float('inf')):
                break

        return all_items

class DataStorage:
    """Handles raw data storage and cleanup"""
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def ensure_directory(self, *paths) -> str:
        """Ensures directory exists and returns the path"""
        dir_path = os.path.join(self.base_dir, *paths)
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    def save_response(self, data: Dict[str, Any], bioguide_id: str, type_prefix: str, page_num: int) -> str:
        """Saves raw API response"""
        dir_path = self.ensure_directory('raw', self.timestamp, type_prefix)
        filename = f"member_{bioguide_id}_page_{page_num:04d}.json"
        file_path = os.path.join(dir_path, filename)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {type_prefix} data to {file_path}")
        return file_path

    def cleanup_old_files(self):
        """Removes raw response files older than RAW_DATA_RETENTION_DAYS"""
        raw_dir = Path(self.base_dir) / 'raw'
        if not raw_dir.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=RAW_DATA_RETENTION_DAYS)
        
        for dir_path in raw_dir.iterdir():
            if not dir_path.is_dir():
                continue
                
            try:
                # Directory names are in format YYYYMMDD_HHMMSS
                dir_date = datetime.strptime(dir_path.name, "%Y%m%d_%H%M%S")
                if dir_date < cutoff_date:
                    shutil.rmtree(dir_path)
                    logger.info(f"Removed old data directory: {dir_path}")
            except (ValueError, OSError) as e:
                logger.warning(f"Error processing directory {dir_path}: {str(e)}")

class DatabaseUpdater:
    """Handles database operations"""
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.known_bills = self.get_known_bills()
        logger.info(f"Loaded {len(self.known_bills)} known bills from database")

    def get_known_bills(self) -> set:
        """Get set of bill numbers already in database"""
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT bill_number FROM bills")
                return {row[0] for row in cur.fetchall()}

    def update_sponsored_legislation(self, data: List[Dict[str, Any]], member_id: int):
        """Updates bills and related tables for sponsored legislation"""
        processed_count = 0
        skipped_count = 0
        
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                for item in data:
                    # Skip amendments for now as they require different handling
                    if 'amendmentNumber' in item:
                        continue

                    bill_type = item.get('type', '')
                    bill_number = f"{bill_type}{item.get('number', '')}"
                    congress = item.get('congress')

                    # Skip if bill not in database
                    if bill_number not in self.known_bills:
                        skipped_count += 1
                        continue

                    processed_count += 1

                    # Insert or update bill
                    cur.execute("""
                        INSERT INTO bills (
                            bill_number, bill_title, congress, bill_type,
                            policy_area, api_url, introduced_date
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (bill_number) DO UPDATE SET
                            bill_title = EXCLUDED.bill_title,
                            congress = EXCLUDED.congress,
                            bill_type = EXCLUDED.bill_type,
                            policy_area = EXCLUDED.policy_area,
                            api_url = EXCLUDED.api_url,
                            introduced_date = EXCLUDED.introduced_date
                        RETURNING id
                    """, (
                        bill_number,
                        item.get('title', ''),
                        congress,
                        bill_type,
                        item.get('policyArea', {}).get('name'),
                        item.get('url'),
                        item.get('introducedDate')
                    ))
                    bill_id = cur.fetchone()[0]

                    # Insert sponsored legislation relationship
                    cur.execute("""
                        INSERT INTO sponsored_legislation (
                            member_id, bill_id, introduced_date
                        ) VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
                        member_id,
                        bill_id,
                        item.get('introducedDate')
                    ))

                    # Update bill actions
                    latest_action = item.get('latestAction', {})
                    if latest_action:
                        cur.execute("""
                            INSERT INTO bill_actions (
                                bill_number, action_date, action_text, action_time
                            ) VALUES (%s, %s, %s, %s)
                            ON CONFLICT (bill_number, action_date, action_text) DO UPDATE SET
                                action_time = EXCLUDED.action_time
                        """, (
                            bill_number,
                            latest_action.get('actionDate'),
                            latest_action.get('text'),
                            latest_action.get('actionTime')
                        ))

        logger.info(f"Sponsored legislation: processed {processed_count} bills, skipped {skipped_count} bills not in database")

    def update_cosponsored_legislation(self, data: List[Dict[str, Any]], member_id: int):
        """Updates bill_cosponsors and related tables"""
        processed_count = 0
        skipped_count = 0
        
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                for item in data:
                    bill_type = item.get('type', '')
                    bill_number = f"{bill_type}{item.get('number', '')}"
                    congress = item.get('congress')

                    # Skip if bill not in database
                    if bill_number not in self.known_bills:
                        skipped_count += 1
                        continue

                    processed_count += 1

                    # Get member info for the cosponsor
                    cur.execute("""
                        SELECT chamber, district FROM members WHERE id = %s
                    """, (member_id,))
                    member_info = cur.fetchone()
                    chamber = member_info[0] if member_info else None
                    district = member_info[1] if member_info else None

                    # Insert or update bill first
                    cur.execute("""
                        INSERT INTO bills (
                            bill_number, bill_title, congress, bill_type,
                            policy_area, api_url
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (bill_number) DO UPDATE SET
                            bill_title = EXCLUDED.bill_title,
                            congress = EXCLUDED.congress,
                            bill_type = EXCLUDED.bill_type,
                            policy_area = EXCLUDED.policy_area,
                            api_url = EXCLUDED.api_url
                        RETURNING id
                    """, (
                        bill_number,
                        item.get('title', ''),
                        congress,
                        bill_type,
                        item.get('policyArea', {}).get('name'),
                        item.get('url')
                    ))
                    bill_id = cur.fetchone()[0]

                    # Insert cosponsored legislation relationship
                    cur.execute("""
                        INSERT INTO cosponsored_legislation (
                            member_id, bill_id, cosponsored_date
                        ) VALUES (%s, %s, CURRENT_DATE)
                        ON CONFLICT DO NOTHING
                    """, (
                        member_id,
                        bill_id
                    ))

                    # Get member info for cosponsor record
                    cur.execute("""
                        SELECT bioguide_id, full_name, party, state
                        FROM members WHERE id = %s
                    """, (member_id,))
                    cosponsor_info = cur.fetchone()
                    if cosponsor_info:
                        # Update bill_cosponsors table
                        cur.execute("""
                            INSERT INTO bill_cosponsors (
                                bill_number, cosponsor_id, cosponsor_name,
                                cosponsor_party, cosponsor_state, cosponsor_chamber,
                                cosponsor_district, cosponsor_date
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
                            ON CONFLICT (bill_number, cosponsor_id) DO UPDATE SET
                                cosponsor_name = EXCLUDED.cosponsor_name,
                                cosponsor_party = EXCLUDED.cosponsor_party,
                                cosponsor_state = EXCLUDED.cosponsor_state,
                                cosponsor_chamber = EXCLUDED.cosponsor_chamber,
                                cosponsor_district = EXCLUDED.cosponsor_district,
                                cosponsor_date = EXCLUDED.cosponsor_date
                        """, (
                            bill_number,
                            cosponsor_info[0],  # bioguide_id
                            cosponsor_info[1],  # full_name
                            cosponsor_info[2],  # party
                            cosponsor_info[3],  # state
                            chamber,
                            district,
                        ))

def main():
    """Main process flow"""
    try:
        # Initialize components
        sync_manager = SyncManager(DATABASE_URL)
        sponsored_fetcher = LegislationFetcher(API_KEY, SPONSORED_ENDPOINT, RECORDS_PER_PAGE)
        cosponsored_fetcher = LegislationFetcher(API_KEY, COSPONSORED_ENDPOINT, RECORDS_PER_PAGE)
        storage = DataStorage(os.path.dirname(__file__))
        db_updater = DatabaseUpdater(DATABASE_URL)

        # Clean up old raw files
        storage.cleanup_old_files()

        # Get sync status for both endpoints
        sponsored_last_sync, sponsored_offset = sync_manager.get_sync_status(SPONSORED_ENDPOINT)
        cosponsored_last_sync, cosponsored_offset = sync_manager.get_sync_status(COSPONSORED_ENDPOINT)

        # Update sync status to in_progress
        sync_manager.update_sync_status(SPONSORED_ENDPOINT, SYNC_STATUS_IN_PROGRESS)
        sync_manager.update_sync_status(COSPONSORED_ENDPOINT, SYNC_STATUS_IN_PROGRESS)

        # Get list of bioguide_ids from database, starting after the last failed member
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Get the last failed member ID
                cur.execute("""
                    SELECT last_error
                    FROM api_sync_status
                    WHERE endpoint = %s AND status = 'failed'
                    ORDER BY last_sync_timestamp DESC
                    LIMIT 1
                """, (SPONSORED_ENDPOINT,))
                result = cur.fetchone()
                last_error = result[0] if result else None
                
                last_failed_member = None
                if last_error:
                    import re
                    match = re.search(r'Error processing member (\w+):', last_error)
                    if match:
                        last_failed_member = match.group(1)

                # Get members list, starting after the last failed member if any
                if last_failed_member:
                    cur.execute("""
                        SELECT id, bioguide_id 
                        FROM members 
                        WHERE current_member = true
                          AND bioguide_id > %s
                        ORDER BY bioguide_id ASC
                    """, (last_failed_member,))
                else:
                    cur.execute("""
                        SELECT id, bioguide_id 
                        FROM members 
                        WHERE current_member = true
                        ORDER BY last_updated ASC
                    """)
                members = cur.fetchall()

        # Process each member
        for member_id, bioguide_id in members:
            try:
                logger.info(f"Processing member {bioguide_id}")

                # Fetch sponsored legislation
                sponsored_data = sponsored_fetcher.fetch_all(bioguide_id, sponsored_last_sync)
                if sponsored_data:
                    storage.save_response(
                        {'sponsoredLegislation': sponsored_data},
                        bioguide_id,
                        'sponsored',
                        1
                    )
                    db_updater.update_sponsored_legislation(sponsored_data, member_id)

                # Fetch cosponsored legislation
                cosponsored_data = cosponsored_fetcher.fetch_all(bioguide_id, cosponsored_last_sync)
                if cosponsored_data:
                    storage.save_response(
                        {'cosponsoredLegislation': cosponsored_data},
                        bioguide_id,
                        'cosponsored',
                        1
                    )
                    db_updater.update_cosponsored_legislation(cosponsored_data, member_id)

                # Update member's last_updated timestamp
                with psycopg2.connect(DATABASE_URL) as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE members 
                            SET last_updated = CURRENT_TIMESTAMP 
                            WHERE id = %s
                        """, (member_id,))
                    conn.commit()

                logger.info(f"Completed processing for member {bioguide_id}")

            except Exception as e:
                error_msg = f"Error processing member {bioguide_id}: {str(e)}"
                logger.error(error_msg)
                sync_manager.update_sync_status(SPONSORED_ENDPOINT, SYNC_STATUS_FAILED, error=error_msg)
                sync_manager.update_sync_status(COSPONSORED_ENDPOINT, SYNC_STATUS_FAILED, error=error_msg)
                continue

        # Update final sync status
        sync_manager.update_sync_status(SPONSORED_ENDPOINT, SYNC_STATUS_SUCCESS)
        sync_manager.update_sync_status(COSPONSORED_ENDPOINT, SYNC_STATUS_SUCCESS)

    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        logger.error(error_msg)
        sync_manager.update_sync_status(SPONSORED_ENDPOINT, SYNC_STATUS_FAILED, error=error_msg)
        sync_manager.update_sync_status(COSPONSORED_ENDPOINT, SYNC_STATUS_FAILED, error=error_msg)
        raise

if __name__ == "__main__":
    main()
