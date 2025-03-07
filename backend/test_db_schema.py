#!/usr/bin/env python3
"""
Script to test if the database schema has been updated correctly.
"""

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import from the congressgov package first
try:
    from src.utils.database import get_db_connection
except ImportError:
    try:
        from utils.database import get_db_connection
    except ImportError:
        print("Error: Could not import database module")
        sys.exit(1)

def check_bills_table():
    """Check if the bills table has the last_updated column."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if the last_updated column exists
                cur.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'bills'
                    AND column_name = 'last_updated'
                """)
                result = cur.fetchone()
                
                if result:
                    print("Success: The 'last_updated' column exists in the 'bills' table")
                    return True
                else:
                    print("Error: The 'last_updated' column does not exist in the 'bills' table")
                    return False
    except Exception as e:
        print(f"Error checking database schema: {str(e)}")
        return False

def main():
    # Load environment variables
    load_dotenv()
    
    # Check the bills table
    success = check_bills_table()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
