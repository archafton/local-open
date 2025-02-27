"""
Centralized logging configuration.
"""

import os
import logging
from datetime import datetime

def setup_logging(
    logger_name: str,
    log_level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_file: str = None,
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
):
    """
    Set up logging configuration.
    
    Args:
        logger_name: Name of the logger
        log_level: Logging level
        log_to_file: Whether to log to a file
        log_to_console: Whether to log to the console
        log_file: Path to log file (if None, a default path will be used)
        log_format: Log message format
        
    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    formatter = logging.Formatter(log_format)
    
    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        if log_file is None:
            # Use default log file path
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(script_dir, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d')
            log_file = os.path.join(log_dir, f"{logger_name}_{timestamp}.log")
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Logging to {log_file}")
    
    return logger