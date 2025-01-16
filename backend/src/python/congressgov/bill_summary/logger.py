import os
import logging
from datetime import datetime
from typing import Dict, Any

class ProcessLogger:
    def __init__(self, log_dir: str = None):
        """Initialize logger with optional custom log directory"""
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Set up and configure logger"""
        logger = logging.getLogger('bill_summary')
        logger.setLevel(logging.INFO)

        # Create timestamp for log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f'bill_summary_{timestamp}.log')

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def log_processing_start(self, bill_id: int, bill_number: str):
        """Log start of bill processing"""
        self.logger.info(f"Starting processing for bill {bill_number} (ID: {bill_id})")

    def log_api_request(self, api_name: str, endpoint: str, params: Dict[str, Any] = None):
        """Log API requests"""
        msg = f"API Request - {api_name}: {endpoint}"
        if params:
            msg += f" with params: {params}"
        self.logger.info(msg)

    def log_error(self, error_type: str, details: str, exc_info: bool = True):
        """Log errors with context"""
        self.logger.error(
            f"Error ({error_type}): {details}",
            exc_info=exc_info
        )

    def log_metrics(self, metrics_data: Dict[str, Any]):
        """Log processing metrics"""
        self.logger.info(f"Processing Metrics: {metrics_data}")

    def log_success(self, bill_number: str, stage: str):
        """Log successful completion of a processing stage"""
        self.logger.info(f"Successfully completed {stage} for bill {bill_number}")

    def log_warning(self, message: str):
        """Log warning messages"""
        self.logger.warning(message)

    def log_info(self, message: str):
        """Log informational messages"""
        self.logger.info(message)

    def log_debug(self, message: str):
        """Log debug messages"""
        self.logger.debug(message)
