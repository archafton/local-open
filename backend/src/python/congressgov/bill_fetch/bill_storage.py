import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BillStorage:
    """Handles file-based storage for bill data using a hierarchical structure."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize with base directory for storage."""
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(__file__), 'raw')
        self.base_dir = base_dir
        
    def get_bill_path(self, congress: str, bill_type: str, bill_number: str) -> str:
        """Get the full path for a bill's directory."""
        return os.path.join(self.base_dir, 'bill', str(congress), bill_type.lower(), str(bill_number))
        
    def ensure_bill_directory(self, congress: str, bill_type: str, bill_number: str) -> str:
        """Create and return the full path for a bill's directory."""
        path = self.get_bill_path(congress, bill_type, bill_number)
        os.makedirs(path, exist_ok=True)
        return path
        
    def save_bill_data(self, 
                      congress: str, 
                      bill_type: str, 
                      bill_number: str, 
                      data_type: str, 
                      data: Dict[str, Any]) -> str:
        """
        Save bill data to the appropriate JSON file.
        
        Args:
            congress: Congress number (e.g., "117")
            bill_type: Type of bill (e.g., "sjres")
            bill_number: Bill number (e.g., "33")
            data_type: Type of data ("details", "text", "summary", or "actions")
            data: The data to save
            
        Returns:
            str: Path to the saved file
        """
        bill_dir = self.ensure_bill_directory(congress, bill_type, bill_number)
        file_path = os.path.join(bill_dir, f"{data_type}.json")
        
        # Create backup if file exists
        if os.path.exists(file_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(bill_dir, f"{data_type}_{timestamp}.json.bak")
            try:
                os.rename(file_path, backup_path)
                logger.info(f"Created backup at {backup_path}")
            except Exception as e:
                logger.error(f"Failed to create backup: {str(e)}")
        
        # Save new data
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {data_type} data to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to save {data_type} data: {str(e)}")
            raise
            
    def load_bill_data(self, 
                      congress: str, 
                      bill_type: str, 
                      bill_number: str, 
                      data_type: str) -> Optional[Dict[str, Any]]:
        """
        Load bill data from a JSON file.
        
        Args:
            congress: Congress number
            bill_type: Type of bill
            bill_number: Bill number
            data_type: Type of data to load
            
        Returns:
            Dict containing the loaded data, or None if file doesn't exist
        """
        file_path = os.path.join(
            self.get_bill_path(congress, bill_type, bill_number),
            f"{data_type}.json"
        )
        
        if not os.path.exists(file_path):
            logger.warning(f"No {data_type} data found at {file_path}")
            return None
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded {data_type} data from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load {data_type} data: {str(e)}")
            return None
            
    def list_bill_files(self, congress: str, bill_type: str, bill_number: str) -> Dict[str, str]:
        """
        List all data files for a specific bill.
        
        Returns:
            Dict mapping data types to file paths
        """
        bill_dir = self.get_bill_path(congress, bill_type, bill_number)
        if not os.path.exists(bill_dir):
            return {}
            
        files = {}
        for data_type in ['details', 'text', 'summary', 'actions']:
            file_path = os.path.join(bill_dir, f"{data_type}.json")
            if os.path.exists(file_path):
                files[data_type] = file_path
                
        return files
