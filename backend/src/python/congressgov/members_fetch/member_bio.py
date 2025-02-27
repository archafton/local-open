#!/usr/bin/env python3
"""
Member bio processor - fetches biographical information from bioguide.congress.gov
using Selenium for web scraping.
"""

import os
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Import utilities
from congressgov.utils.logging_config import setup_logging
from congressgov.utils.database import get_db_connection, with_db_transaction
from congressgov.utils.file_storage import ensure_directory, save_json, cleanup_old_files

# Web scraping libraries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# Set up logging
logger = setup_logging(__name__)

# Configuration
BIOGUIDE_ENDPOINT = "https://bioguide.congress.gov/search/bio/{bioguide_id}"
RAW_DATA_RETENTION_DAYS = 30
WAIT_TIME = 5  # Seconds to wait for page loading

class MemberBioProcessor:
    """Handles fetching and processing biographical information for members."""
    
    def __init__(self):
        """Initialize the processor."""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.raw_dir = ensure_directory(os.path.dirname(__file__), 'raw', 'bios', self.timestamp)
        self.driver = self.setup_driver()
        
    def setup_driver(self) -> webdriver.Chrome:
        """Set up a headless Chrome browser for scraping."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    
    def extract_bio_text(self, html_content: str) -> str:
        """Extract biography text from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try to find the biography section
        bio_text = ""
        
        # Look for the specific biography container with the new class structure
        bio_element = soup.select_one('.c-tabs-container__page--active .u-inline-paragraphs')
        
        if bio_element:
            bio_text = bio_element.get_text(strip=True)
        else:
            # Fallback to try different possible elements that might contain the biography
            for selector in ['.biography', '.bioguide-info', '#biography', '#bioguide-info']:
                bio_element = soup.select_one(selector)
                if bio_element:
                    bio_text = bio_element.get_text(strip=True)
                    break
            
            if not bio_text:
                # Try to find text between Biography and Bibliography sections
                text = soup.get_text()
                try:
                    start = text.index('Biography')
                    end = text.index('Bibliography')
                    bio_text = text[start:end].strip()
                except ValueError:
                    # If we can't find the sections, just get all text
                    bio_text = text.strip()
        
        return bio_text
    
    def fetch_member_bio(self, bioguide_id: str) -> Dict[str, Any]:
        """Fetch biographical information for a specific member."""
        url = BIOGUIDE_ENDPOINT.format(bioguide_id=bioguide_id)
        logger.info(f"Fetching bio for member {bioguide_id}")
        
        try:
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(WAIT_TIME)  # Give time for JavaScript to execute
            
            # Get the page source and extract bio text
            bio_text = self.extract_bio_text(self.driver.page_source)
            
            # Create a structured response
            bio_data = {
                'bioguideId': bioguide_id,
                'profileText': bio_text,
                'bioDirectory': url,
                'fetchDate': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully fetched bio for {bioguide_id}")
            return bio_data
                
        except Exception as e:
            logger.error(f"Error fetching bio for {bioguide_id}: {str(e)}")
            raise
    
    def save_bio_data(self, data: Dict[str, Any], bioguide_id: str) -> str:
        """Save bio data to a JSON file."""
        dir_path = ensure_directory(self.raw_dir, bioguide_id)
        filename = f"bio.json"
        
        return save_json(data, dir_path, filename)
    
    @with_db_transaction
    def update_member_bio(self, cursor, bio_data: Dict[str, Any]) -> bool:
        """Update member bio in the database."""
        bioguide_id = bio_data.get('bioguideId')
        
        if not bioguide_id:
            logger.warning("No bioguide ID found in bio data")
            return False
            
        # Extract relevant information from bio data
        profile_text = bio_data.get('profileText', '')
        bio_directory = bio_data.get('bioDirectory', '')
        bio_update_date = datetime.now()
        
        # Update the members table with bio information
        cursor.execute("""
            UPDATE members SET
                profile_text = %s,
                bio_directory = %s,
                bio_update_date = %s,
                last_updated = CURRENT_TIMESTAMP
            WHERE bioguide_id = %s
            RETURNING id
        """, (
            profile_text,
            bio_directory,
            bio_update_date,
            bioguide_id
        ))
        
        result = cursor.fetchone()
        if not result:
            logger.warning(f"No member record found for {bioguide_id}")
            return False
            
        return True
    
    def process_member(self, bioguide_id: str) -> Dict[str, Any]:
        """Process a single member, fetching and updating bio information."""
        results = {
            "bioguide_id": bioguide_id,
            "status": "success",
            "bio_updated": False
        }
        
        try:
            # Fetch bio data
            bio_data = self.fetch_member_bio(bioguide_id)
            
            # Save bio data
            file_path = self.save_bio_data(bio_data, bioguide_id)
            logger.info(f"Saved bio data to {file_path}")
            
            # Update database
            results["bio_updated"] = self.update_member_bio(bio_data)
            
            logger.info(f"Successfully processed bio for member {bioguide_id}")
            
        except Exception as e:
            logger.error(f"Error processing bio for member {bioguide_id}: {str(e)}", exc_info=True)
            results["status"] = "failed"
            results["error"] = str(e)
            
        return results
    
    def close(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")

def get_members_for_processing(recent_only: bool = True, days: int = 7, limit: int = 100) -> List[str]:
    """Get members to process, either recently updated or all."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if recent_only:
                # Get members updated in the last N days
                cutoff_date = datetime.now() - timedelta(days=days)
                cur.execute("""
                    SELECT bioguide_id 
                    FROM members 
                    WHERE last_updated >= %s
                    ORDER BY last_updated ASC
                    LIMIT %s
                """, (cutoff_date, limit))
            else:
                # Get members with missing bios or oldest updated
                cur.execute("""
                    SELECT bioguide_id 
                    FROM members 
                    WHERE profile_text IS NULL
                       OR bio_directory IS NULL
                    UNION
                    SELECT bioguide_id 
                    FROM members 
                    ORDER BY bio_update_date ASC NULLS FIRST
                    LIMIT %s
                """, (limit,))
            
            return [row[0] for row in cur.fetchall()]

def main():
    parser = argparse.ArgumentParser(description='Process member bios')
    parser.add_argument('--member', help='Process specific member by bioguide ID')
    parser.add_argument('--all', action='store_true', help='Process all members instead of just recent ones')
    parser.add_argument('--days', type=int, default=7, help='For recent mode, how many days back to consider')
    parser.add_argument('--limit', type=int, default=50, help='Maximum number of members to process')
    parser.add_argument('--missing', action='store_true', help='Focus on members with missing bios')
    args = parser.parse_args()
    
    processor = None
    
    try:
        # Initialize processor
        processor = MemberBioProcessor()
        
        # Determine which members to process
        if args.member:
            # Process single specified member
            members_to_process = [args.member]
            logger.info(f"Processing single member: {args.member}")
        else:
            # Get members from database
            recent_only = not args.all and not args.missing
            members_to_process = get_members_for_processing(recent_only, args.days, args.limit)
            logger.info(f"Processing {len(members_to_process)} members")
        
        # Process each member
        results = []
        processed_count = 0
        error_count = 0
        
        for bioguide_id in members_to_process:
            try:
                result = processor.process_member(bioguide_id)
                results.append(result)
                
                if result['status'] == 'success':
                    processed_count += 1
                else:
                    error_count += 1
                    
                # Add a small delay between requests to avoid overloading the server
                time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Error processing member {bioguide_id}: {str(e)}", exc_info=True)
                error_count += 1
        
        # Clean up old files
        cleanup_old_files(os.path.join(os.path.dirname(__file__), 'raw', 'bios'), 
                         pattern='*', days=RAW_DATA_RETENTION_DAYS)
        
        logger.info(f"Process completed. {processed_count} members processed successfully, {error_count} errors.")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        raise
    finally:
        if processor:
            processor.close()

if __name__ == "__main__":
    main()