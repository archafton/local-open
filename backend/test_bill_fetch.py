#!/usr/bin/env python3
"""
Simplified bill fetching script for testing.
"""

import os
import sys
import requests
import json
import argparse
from datetime import datetime
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

def fetch_bills(start_date=None, end_date=None, limit=10):
    """Fetch bills from Congress.gov API."""
    url = f"{BASE_API_URL}/{ENDPOINT}"
    params = {
        'api_key': API_KEY,
        'format': 'json',
        'limit': limit,
        'offset': 0
    }
    
    # Add date filtering if provided
    if start_date:
        params['fromDateTime'] = f"{start_date}T00:00:00Z"
    if end_date:
        params['toDateTime'] = f"{end_date}T23:59:59Z"
    
    print(f"Making GET request to {url} with params: {params}")
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract bills
        bills = data.get('bills', [])
        print(f"Successfully fetched {len(bills)} bills")
        
        # Print bill details
        for i, bill in enumerate(bills):
            print(f"\nBill {i+1}:")
            print(f"  Number: {bill.get('number')}")
            print(f"  Congress: {bill.get('congress')}")
            print(f"  Title: {bill.get('title', '')[:100]}...")
            print(f"  Latest Action: {bill.get('latestAction', {}).get('text', '')[:100]}...")
            print(f"  Action Date: {bill.get('latestAction', {}).get('actionDate', '')}")
        
        return bills
    except requests.exceptions.Timeout:
        print("Error: Request timed out after 10 seconds")
    except requests.exceptions.RequestException as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    
    return []

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Fetch bills from Congress.gov API')
    parser.add_argument('--start-date', help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', help='End date in YYYY-MM-DD format')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of bills to fetch')
    args = parser.parse_args()
    
    # Fetch bills
    fetch_bills(args.start_date, args.end_date, args.limit)

if __name__ == "__main__":
    main()
