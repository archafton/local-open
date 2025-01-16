import os
import json
import requests
import logging
from typing import Dict, Optional, List
from datetime import datetime

class CongressAPI:
    def __init__(self):
        self.api_key = os.getenv('CONGRESSGOV_API_KEY')
        self.bill_detail_endpoint = os.getenv('CONGRESSGOV_BILL_DETAIL_ENDPOINT')
        self.bill_text_endpoint = os.getenv('CONGRESSGOV_BILL_TEXT_ENDPOINT')
        self.raw_dir = os.path.join(os.path.dirname(__file__), '..', 'bill_fetch', 'raw')
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging configuration"""
        self.logger = logging.getLogger('congress_api')
        self.logger.setLevel(logging.INFO)
        
        # Create handler for file logging
        file_handler = logging.FileHandler('congress_api.log')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def _ensure_raw_directory(self):
        """Ensure raw directory exists"""
        if not os.path.exists(self.raw_dir):
            os.makedirs(self.raw_dir)

    def _save_response(self, data: Dict, prefix: str, bill_number: str):
        """Save API response to JSON file"""
        self._ensure_raw_directory()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{bill_number}_{timestamp}.json"
        filepath = os.path.join(self.raw_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Saved response to {filepath}")
        return filepath

    async def fetch_bill_text_versions(self, congress: int, bill_type: str, bill_number: str) -> Dict:
        """
        Fetch text versions from Congress.gov API
        Returns all available text versions for a bill
        """
        params = {
            'api_key': self.api_key,
            'format': 'json'
        }
        
        endpoint = self.bill_text_endpoint.format(
            congress=congress,
            billType=bill_type,
            billNumber=bill_number
        )
        
        try:
            self.logger.info(f"Fetching text versions for {bill_type}{bill_number}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Save response for reference
            self._save_response(data, 'text_versions', f"{bill_type}{bill_number}")
            
            return data
        except requests.RequestException as e:
            self.logger.error(f"Error fetching text versions: {str(e)}")
            raise

    async def extract_latest_text_link(self, versions_data: Dict) -> Optional[str]:
        """
        Extract the latest XML text link from versions data
        Returns the URL for the most recent XML version
        """
        try:
            if not versions_data.get('textVersions'):
                return None

            # Handle both list and dict responses
            versions = versions_data['textVersions']
            if isinstance(versions, dict):
                versions = versions.get('item', [])
            
            # Sort versions by date if available
            sorted_versions = sorted(
                versions,
                key=lambda x: x.get('date', ''),
                reverse=True
            )

            for version in sorted_versions:
                formats = version.get('formats', {}).get('item', [])
                if isinstance(formats, dict):
                    formats = [formats]
                
                for fmt in formats:
                    if fmt.get('type') == 'XML':
                        return fmt.get('url')
            
            return None
        except Exception as e:
            self.logger.error(f"Error extracting text link: {str(e)}")
            raise

    async def extract_law_link(self, versions_data: Dict) -> Optional[str]:
        """
        Extract public law link if available
        Returns the URL for the public law version if the bill became law
        """
        try:
            if not versions_data.get('textVersions'):
                return None

            versions = versions_data['textVersions']
            if isinstance(versions, dict):
                versions = versions.get('item', [])

            for version in versions:
                if version.get('type') == 'Public Law':
                    formats = version.get('formats', {}).get('item', [])
                    if isinstance(formats, dict):
                        formats = [formats]
                    
                    for fmt in formats:
                        if fmt.get('type') == 'XML':
                            return fmt.get('url')
            
            return None
        except Exception as e:
            self.logger.error(f"Error extracting law link: {str(e)}")
            raise

    async def download_xml(self, url: str, bill_number: str) -> str:
        """
        Download XML content from provided URL
        Returns the path to the saved XML file
        """
        try:
            self.logger.info(f"Downloading XML for bill {bill_number}")
            response = requests.get(url)
            response.raise_for_status()
            
            self._ensure_raw_directory()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bill_text_{bill_number}_{timestamp}.xml"
            filepath = os.path.join(self.raw_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            self.logger.info(f"Saved XML to {filepath}")
            return filepath
        except requests.RequestException as e:
            self.logger.error(f"Error downloading XML: {str(e)}")
            raise
