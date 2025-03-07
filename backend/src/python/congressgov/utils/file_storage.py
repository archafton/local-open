"""
File storage utilities for saving and loading data files.
"""

import os
import json
import logging
import shutil
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

def ensure_directory(*paths) -> str:
    """
    Ensure that the specified directory path exists.
    
    Args:
        *paths: Path components to join
        
    Returns:
        Path to the created directory
    """
    dir_path = os.path.join(*paths)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def save_json(data: Dict[str, Any], directory: str, filename: str, create_backup: bool = False) -> str:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        directory: Directory to save to
        filename: Filename
        create_backup: If True and file exists, create a backup
        
    Returns:
        Path to the saved file
    """
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)
    
    # Create backup if requested and file exists
    if create_backup and os.path.exists(file_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(directory, f"{os.path.splitext(filename)[0]}_{timestamp}.json.bak")
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup at {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
    
    # Save data
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved data to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to save data: {str(e)}")
        raise

def load_json(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load data from a JSON file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Loaded data or None if file doesn't exist
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return None
        
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded data from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Failed to load data: {str(e)}")
        return None

def cleanup_old_files(directory: str, pattern: str = '*', days: int = 30):
    """
    Remove files older than the specified number of days.
    
    Args:
        directory: Directory to clean up
        pattern: File pattern to match
        days: Maximum age in days
    """
    if not os.path.exists(directory):
        logger.warning(f"Directory not found: {directory}")
        return
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for path in Path(directory).glob(pattern):
        if path.is_file():
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
                if mtime < cutoff_date:
                    os.remove(path)
                    logger.info(f"Removed old file: {path}")
            except Exception as e:
                logger.warning(f"Error processing file {path}: {str(e)}")
        elif path.is_dir():
            try:
                # For directories, check if they're empty after processing their contents
                shutil.rmtree(path)
                logger.info(f"Removed old directory: {path}")
            except Exception as e:
                logger.warning(f"Error removing directory {path}: {str(e)}")