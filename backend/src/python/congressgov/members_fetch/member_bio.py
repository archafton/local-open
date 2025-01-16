import os
import json
import psycopg2
import logging
import time
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Any, Optional
from glob import glob
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Set up logging to both file and console
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, 'member_bio_fetch.log')

# Create a logger
logger = logging.getLogger('member_bio')
logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Load environment variables
load_dotenv()

# Print working directory and environment for debugging
print(f"Current working directory: {os.getcwd()}")
print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")

# Database connection string
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")
    raise ValueError("DATABASE_URL environment variable not set")

# Bioguide endpoint
BIOGUIDE_ENDPOINT = "https://bioguide.congress.gov/search/bio/{bioguide_id}"

def setup_driver():
    """
    Set up a headless Chrome browser
    """
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
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def extract_bio_text(html_content: str) -> str:
    """
    Extract biography text from HTML content
    """
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

def fetch_member_bio(driver: webdriver.Chrome, bioguide_id: str) -> Dict[str, Any]:
    """
    Fetch biographical information for a specific member using Selenium
    """
    url = BIOGUIDE_ENDPOINT.format(bioguide_id=bioguide_id)
    logger.info(f"Fetching bio for member {bioguide_id}")
    
    try:
        driver.get(url)
        
        # Wait for page to load
        time.sleep(5)  # Give time for JavaScript to execute
        
        # Get the page source and extract bio text
        bio_text = extract_bio_text(driver.page_source)
        
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

def ensure_raw_directory(timestamp: str) -> str:
    """
    Ensure that the timestamped 'raw/bios' directory exists
    Returns the path to the directory
    """
    raw_dir = os.path.join(os.path.dirname(__file__), 'raw', timestamp, 'bios')
    os.makedirs(raw_dir, exist_ok=True)
    return raw_dir

def save_to_json(data: Dict[str, Any], timestamp: str, bioguide_id: str) -> str:
    """
    Save member bio data to a JSON file in the timestamped directory
    """
    raw_dir = ensure_raw_directory(timestamp)
    filename = f"member_bio_{bioguide_id}.json"
    file_path = os.path.join(raw_dir, filename)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved member bio data to {file_path}")
    return file_path

def update_database_with_bio(bio_data: Dict[str, Any], bioguide_id: str):
    """
    Update the database with biographical information
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Extract relevant information from bio data
        profile_text = bio_data.get('profileText', '')
        bio_directory = bio_data.get('bioDirectory', '')
        bio_update_date = datetime.now()

        # Update the members table with bio information
        cur.execute("""
            UPDATE members SET
                profile_text = %s,
                bio_directory = %s,
                bio_update_date = %s
            WHERE bioguide_id = %s
        """, (
            profile_text,
            bio_directory,
            bio_update_date,
            bioguide_id
        ))

        conn.commit()
        logger.info(f"Successfully updated database with bio for member {bioguide_id}")

    except Exception as e:
        logger.error(f"Error updating database with member bio: {str(e)}")
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
        logger.info(f"Retrieved {len(bioguide_ids)} bioguide IDs from database")
        
    except Exception as e:
        logger.error(f"Error fetching bioguide IDs: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()
    
    return bioguide_ids

def main():
    logger.info("Starting member bio fetch process")
    driver = None
    try:
        # Create timestamp for this run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Using timestamp: {timestamp}")
        
        # Set up the browser
        driver = setup_driver()
        logger.info("Browser setup complete")
        
        # Get all bioguide IDs from the database
        bioguide_ids = get_all_bioguide_ids()
        
        if not bioguide_ids:
            logger.warning("No bioguide IDs found in database")
            return
        
        logger.info(f"Found {len(bioguide_ids)} members to fetch bios for")
        
        # Test with a single member first
        test_id = 'L000174'  # Patrick Leahy
        logger.info(f"Testing with member {test_id}")
        try:
            bio_data = fetch_member_bio(driver, test_id)
            logger.info("Test fetch successful")
            logger.info(f"Bio data keys: {bio_data.keys()}")
            save_to_json(bio_data, timestamp, test_id)
            update_database_with_bio(bio_data, test_id)
        except Exception as e:
            logger.error(f"Test fetch failed: {str(e)}")
            return

        # If test was successful, proceed with all members
        for bioguide_id in bioguide_ids:
            if bioguide_id == test_id:  # Skip the test ID since we already processed it
                continue
                
            try:
                bio_data = fetch_member_bio(driver, bioguide_id)
                save_to_json(bio_data, timestamp, bioguide_id)
                update_database_with_bio(bio_data, bioguide_id)
                # Add a small delay between requests
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error processing member {bioguide_id}: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise
    finally:
        if driver:
            driver.quit()
            logger.info("Browser closed")

if __name__ == "__main__":
    main()
