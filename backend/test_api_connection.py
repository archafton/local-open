#!/usr/bin/env python3
"""
Simple script to test the connection to the Congress.gov API.
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
API_KEY = os.getenv('CONGRESSGOV_API_KEY')
if not API_KEY:
    print("Error: CONGRESSGOV_API_KEY environment variable not found")
    sys.exit(1)

# API configuration
BASE_API_URL = "https://api.congress.gov/v3"
ENDPOINT = "bill"

def test_api_connection():
    """Test the connection to the Congress.gov API."""
    url = f"{BASE_API_URL}/{ENDPOINT}"
    params = {
        'api_key': API_KEY,
        'format': 'json',
        'limit': 1,
        'offset': 0
    }
    
    print(f"Making GET request to {url}")
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print("API connection successful!")
        print(f"Response status code: {response.status_code}")
        print(f"Response content type: {response.headers.get('Content-Type')}")
        print(f"Response data: {json.dumps(data, indent=2)[:500]}...")
        return True
    except requests.exceptions.Timeout:
        print("Error: Request timed out after 10 seconds")
    except requests.exceptions.RequestException as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    
    return False

if __name__ == "__main__":
    test_api_connection()
