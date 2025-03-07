#!/usr/bin/env python3
"""
Script to apply a database migration.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import from the congressgov package first
try:
    from congressgov.utils.database import get_db_connection
except ImportError:
    # If that fails, try to import from utils directly
    try:
        from utils.database import get_db_connection
    except ImportError:
        # If that also fails, use a direct import
        from src.utils.database import get_db_connection

def apply_migration(migration_file):
    """Apply a migration file to the database."""
    if not os.path.exists(migration_file):
        print(f"Error: Migration file {migration_file} does not exist")
        return False
    
    print(f"Applying migration: {migration_file}")
    
    # Read the migration file
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    # Apply the migration
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        print("Migration applied successfully")
        return True
    except Exception as e:
        print(f"Error applying migration: {str(e)}")
        return False

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Apply a database migration')
    parser.add_argument('migration_file', help='Path to the migration file')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Apply the migration
    success = apply_migration(args.migration_file)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
