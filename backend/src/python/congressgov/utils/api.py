"""
API utilities for making requests to external services with error handling and retries.
"""

import os
import time
import logging
import requests
from typing import Dict, Any, Optional, Callable
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
API_KEY = os.getenv('CONGRESSGOV_API_KEY')

# Set up logging
logger = logging.getLogger(__name__)

class RetryStrategy:
    """Implements exponential backoff and retry logic for API requests."""
    
    def __init__(self, max_retries: int = 3, base_delay: int = 1):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Executes function with retry logic and exponential backoff
        
        Args:
            func: The function to execute
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the function call
            
        Raises:
            The last exception encountered if all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except requests.RequestException as e:
                last_error = e
                if attempt == self.max_retries - 1:
                    # Last attempt failed, re-raise the exception
                    logger.error(f"All {self.max_retries} retry attempts failed")
                    raise
                
                # Calculate delay with exponential backoff
                delay = self.base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay} seconds...")
                time.sleep(delay)
        
        # We should never reach here, but just in case
        if last_error:
            raise last_error
        raise Exception("Retry strategy failed for unknown reason")

class APIClient:
    """Client for making requests to Congress.gov API with error handling and retry logic."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, delay: float = 0.5):
        """
        Initialize API client
        
        Args:
            base_url: Base URL for API requests
            api_key: API key (defaults to environment variable if not provided)
            delay: Delay between requests in seconds
        """
        self.base_url = base_url
        self.api_key = api_key or API_KEY
        self.delay = delay
        self.session = requests.Session()
        self.retry_strategy = RetryStrategy()
        
        if not self.api_key:
            logger.warning("No API key provided. Requests may fail if authentication is required.")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request to the API with retry logic
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        all_params = params or {}
        
        # Add API key to parameters if available
        if self.api_key:
            all_params['api_key'] = self.api_key
            
        # Add format parameter if not provided
        if 'format' not in all_params:
            all_params['format'] = 'json'
        
        logger.info(f"Making GET request to {url}")
        
        def make_request():
            response = self.session.get(url, params=all_params)
            response.raise_for_status()
            # Add delay to avoid rate limiting
            time.sleep(self.delay)
            return response.json()
        
        return self.retry_strategy.execute(make_request)
    
    def get_paginated(self, endpoint: str, params: Optional[Dict[str, Any]] = None, 
                    items_key: str = None, limit: int = 250) -> list:
        """
        Fetch all pages of results using pagination
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            items_key: Key in the response that contains the items array
            limit: Number of items per page
            
        Returns:
            List of all items across all pages
        """
        all_items = []
        current_params = params.copy() if params else {}
        current_params['limit'] = limit
        current_params['offset'] = current_params.get('offset', 0)
        
        while True:
            response = self.get(endpoint, current_params)
            
            # Extract items from response
            if items_key and items_key in response:
                page_items = response[items_key]
                if isinstance(page_items, list):
                    all_items.extend(page_items)
                else:
                    logger.warning(f"Expected list for {items_key}, got {type(page_items)}")
            else:
                # If no items_key specified, use the first list found in the response
                for key, value in response.items():
                    if isinstance(value, list) and key != 'pagination':
                        all_items.extend(value)
                        break
            
            # Check if we need to fetch the next page
            if 'pagination' not in response or 'next' not in response['pagination']:
                break
                
            # Update offset for next page
            current_params['offset'] += limit
        
        return all_items