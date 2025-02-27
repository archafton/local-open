# Committees API Documentation

## Overview

The Committees module will be responsible for fetching, processing, and enriching committee data from the Congress.gov/GPO endpoint (e.g., [GPO Committees](https://gpo.congress.gov/#/committee)). It will allow users to view detailed committee information (such as committee names, jurisdictions, contact details, and hierarchy) and will integrate with the existing system in a consistent, modular fashion.

Similar to the existing bills and members modules, this module will:
- **Fetch basic committee metadata** from the external API.
- **Fetch detailed committee information** (e.g., contact information, jurisdiction, parent/subcommittee relationships).
- **Store raw API responses** for auditing and debugging.
- **Update the PostgreSQL database** with committee data using incremental and full-sync strategies.
- **Support batch and parallel processing** for historical data or data gap filling.
- **Expose REST API endpoints** (under `/api/committees`) for the frontend to query committee information.
- **Track sync status** in the existing `api_sync_status` table.
- **Implement comprehensive error handling and retry mechanisms**.

---

## Schema Extensions

### New Tables: `committees` and Related Tables

```sql
-- Primary committee table
CREATE TABLE committees (
  id SERIAL PRIMARY KEY,
  committee_id VARCHAR(50) UNIQUE NOT NULL,  -- Unique identifier from Congress.gov/GPO
  name VARCHAR(255) NOT NULL,
  normalized_name VARCHAR(255) NOT NULL,     -- Lower-case, no spaces for consistent matching
  chamber VARCHAR(50) NOT NULL,              -- e.g., "House" or "Senate"
  jurisdiction TEXT,                         -- A description of the committee's scope
  parent_committee_id VARCHAR(50),           -- If this is a subcommittee
  website VARCHAR(255),
  phone VARCHAR(50),
  address TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Committee member relationships
CREATE TABLE committee_members (
  id SERIAL PRIMARY KEY,
  committee_id INTEGER REFERENCES committees(id) ON DELETE CASCADE,
  member_id INTEGER REFERENCES members(id) ON DELETE CASCADE,
  role VARCHAR(100),                         -- e.g., "Chair", "Ranking Member", "Member"
  start_date DATE,
  end_date DATE,
  congress INTEGER,                          -- For historical tracking
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (committee_id, member_id, congress)
);

-- Committee history for tracking changes over time
CREATE TABLE committee_history (
  id SERIAL PRIMARY KEY,
  committee_id INTEGER REFERENCES committees(id) ON DELETE CASCADE,
  congress INTEGER NOT NULL,
  name VARCHAR(255) NOT NULL,
  jurisdiction TEXT,
  parent_committee_id VARCHAR(50),
  effective_date DATE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bill-committee relationships (extending existing table)
ALTER TABLE bill_committees
ADD COLUMN IF NOT EXISTS referral_date DATE,
ADD COLUMN IF NOT EXISTS referral_type VARCHAR(50);

-- Add necessary indexes for performance
CREATE INDEX idx_committees_chamber ON committees(chamber);
CREATE INDEX idx_committees_parent_id ON committees(parent_committee_id);
CREATE INDEX idx_committees_normalized_name ON committees(normalized_name);
CREATE INDEX idx_committee_members_member_id ON committee_members(member_id);
CREATE INDEX idx_committee_members_congress ON committee_members(congress);
CREATE INDEX idx_committee_history_congress ON committee_history(congress);
```

### Updated Function for Committee Timestamps

```sql
-- Add trigger to update the updated_at timestamp
CREATE TRIGGER update_committees_updated_at
    BEFORE UPDATE ON committees
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## Environment Variable Additions

Extend your `.env` file with committee-specific configuration:

```dotenv
# Committee API settings
COMMITTEE_API_BASE_URL=https://api.congress.gov/v3/committee
COMMITTEE_RETRY_ATTEMPTS=3
COMMITTEE_RETRY_DELAY=2
COMMITTEE_DATA_RETENTION_DAYS=30
```

It will use the same `CONGRESSGOV_API_KEY` used in bills and members.

---

## Python Structure and Module Organization

### Directory Structure

```
project-tacitus/
├── backend/
│   └── src/
│       ├── congressgov/
│       │   ├── bill_fetch/              # Existing bill modules
│       │   ├── members_fetch/           # Existing member modules
│       │   └── committee_fetch/         # NEW: Committee modules
│       │       ├── committee_fetch_core.py
│       │       ├── committee_detail_processor.py
│       │       ├── committee_batch_processor.py
│       │       ├── committee_validation.py
│       │       ├── committee_member_processor.py
│       │       └── committee_utils.py
│       ├── models/
│       │   └── committee.py             # NEW: Committee data queries and models
│       ├── api/
│       │   └── committees.py            # NEW: API endpoints for committees
│       └── utils/
│           ├── database.py
│           ├── file_storage.py
│           ├── logging_config.py
│           └── api.py
```

### Utility Module

#### committee_utils.py

```python
"""
Committee-related utilities for processing Congress.gov data.
"""
import re
import logging
from typing import Dict, Any, Optional, Tuple, List

# Set up logging
logger = logging.getLogger(__name__)

def normalize_committee_name(name: str) -> str:
    """
    Normalize committee name for consistent matching.
    
    Args:
        name: Committee name
        
    Returns:
        Normalized name (lowercase, no special characters)
    """
    if not name:
        return ""
    
    # Convert to lowercase, remove special characters, replace spaces with underscores
    normalized = re.sub(r'[^\w\s]', '', name.lower())
    normalized = re.sub(r'\s+', '_', normalized)
    return normalized

def format_committee_display_name(name: str, chamber: str) -> str:
    """
    Format committee name for display.
    
    Args:
        name: Committee name
        chamber: Committee chamber ('house' or 'senate')
        
    Returns:
        Formatted display name
    """
    if not name:
        return ""
    
    chamber_prefix = ""
    if chamber.lower() == 'house':
        chamber_prefix = "House "
    elif chamber.lower() == 'senate':
        chamber_prefix = "Senate "
    elif chamber.lower() == 'joint':
        chamber_prefix = "Joint "
    
    # Check if name already starts with the chamber
    if name.lower().startswith(chamber_prefix.lower()):
        return name
    
    return f"{chamber_prefix}{name}"

def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number format.
    
    Args:
        phone: Phone number string
        
    Returns:
        Normalized phone number
    """
    if not phone:
        return ""
    
    # Remove non-numeric characters
    digits = re.sub(r'\D', '', phone)
    
    # Format as (XXX) XXX-XXXX
    if len(digits) == 10:
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
    
    # Return original if not a standard format
    return phone

def format_jurisdiction(text: str) -> str:
    """
    Clean and format committee jurisdiction text.
    
    Args:
        text: Jurisdiction text
        
    Returns:
        Formatted jurisdiction text
    """
    if not text:
        return ""
    
    # Remove extra whitespace and line breaks
    cleaned = re.sub(r'\s+', ' ', text).strip()
    
    # Split into sentences and capitalize each
    sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    formatted = ' '.join(s[0].upper() + s[1:] if s else '' for s in sentences)
    
    return formatted

def parse_committee_hierarchy(committee_id: str, parent_id: Optional[str]) -> Tuple[bool, int]:
    """
    Determine committee hierarchy level.
    
    Args:
        committee_id: Committee ID
        parent_id: Parent committee ID
        
    Returns:
        Tuple of (is_subcommittee, hierarchy_level)
    """
    is_subcommittee = bool(parent_id)
    hierarchy_level = 0
    
    if is_subcommittee:
        hierarchy_level = 1
        # Look for sub-subcommittees with specific patterns in the ID
        if committee_id and '_sub_' in committee_id.lower():
            hierarchy_level = 2
    
    return is_subcommittee, hierarchy_level

def get_committee_url(committee_id: str) -> str:
    """
    Generate a URL for the committee on Congress.gov.
    
    Args:
        committee_id: Committee ID
        
    Returns:
        URL string
    """
    return f"https://www.congress.gov/committee/{committee_id}"
```

### Core Modules

#### committee_fetch_core.py

This script handles the initial fetching of committee metadata and creates base records in the database. It supports incremental updates based on the last sync timestamp.

```python
#!/usr/bin/env python3
"""
Committee validation script - checks for missing or incomplete committee data.
"""

import os
import argparse
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Import utilities
from congressgov.utils.logging_config import setup_logging
from congressgov.utils.database import get_db_connection

# Set up logging
logger = setup_logging(__name__)

def check_missing_details():
    """
    Check for committees missing detailed information.
    
    Returns:
        Dictionary with lists of committee IDs missing various details
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Committees missing website
            cur.execute("""
                SELECT committee_id, name, chamber
                FROM committees
                WHERE website IS NULL OR website = ''
            """)
            missing_website = cur.fetchall()
            
            # Committees missing phone
            cur.execute("""
                SELECT committee_id, name, chamber
                FROM committees
                WHERE phone IS NULL OR phone = ''
            """)
            missing_phone = cur.fetchall()
            
            # Committees missing address
            cur.execute("""
                SELECT committee_id, name, chamber
                FROM committees
                WHERE address IS NULL OR address = ''
            """)
            missing_address = cur.fetchall()
            
            # Committees missing jurisdiction
            cur.execute("""
                SELECT committee_id, name, chamber
                FROM committees
                WHERE jurisdiction IS NULL OR jurisdiction = ''
            """)
            missing_jurisdiction = cur.fetchall()
            
            return {
                'missing_website': missing_website,
                'missing_phone': missing_phone,
                'missing_address': missing_address,
                'missing_jurisdiction': missing_jurisdiction
            }

def check_committee_relationships():
    """
    Check for issues with committee relationships.
    
    Returns:
        Dictionary with lists of committee IDs with relationship issues
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Subcommittees with invalid parent
            cur.execute("""
                SELECT c.committee_id, c.name, c.parent_committee_id
                FROM committees c
                LEFT JOIN committees p ON c.parent_committee_id = p.committee_id
                WHERE c.parent_committee_id IS NOT NULL
                  AND p.committee_id IS NULL
            """)
            invalid_parent = cur.fetchall()
            
            # Committees missing member associations
            cur.execute("""
                SELECT c.committee_id, c.name, c.chamber
                FROM committees c
                LEFT JOIN committee_members cm ON c.id = cm.committee_id
                GROUP BY c.committee_id, c.name, c.chamber
                HAVING COUNT(cm.id) = 0
            """)
            missing_members = cur.fetchall()
            
            # Committee history gaps
            cur.execute("""
                SELECT c.committee_id, c.name
                FROM committees c
                LEFT JOIN committee_history ch ON c.id = ch.committee_id
                GROUP BY c.committee_id, c.name
                HAVING COUNT(ch.id) = 0
            """)
            missing_history = cur.fetchall()
            
            return {
                'invalid_parent': invalid_parent,
                'missing_members': missing_members,
                'missing_history': missing_history
            }

def export_validation_results(results, output_format='text', output_file=None):
    """
    Export validation results to a file.
    
    Args:
        results: Dictionary with validation results
        output_format: Format of the output ('text' or 'json')
        output_file: Optional output file path
        
    Returns:
        Path to the output file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if output_file:
        filename = output_file
    else:
        filename = f"committee_validation_{timestamp}.{output_format}"
    
    if output_format == 'json':
        # Convert results to serializable format
        serializable_results = {}
        for category, data in results['details'].items():
            serializable_results[category] = [
                {'committee_id': row[0], 'name': row[1], 'chamber': row[2] if len(row) > 2 else None}
                for row in data
            ]
        
        for category, data in results['relationships'].items():
            serializable_results[category] = [
                {'committee_id': row[0], 'name': row[1], 
                 'parent_id' if category == 'invalid_parent' else 'chamber': row[2] if len(row) > 2 else None}
                for row in data
            ]
        
        with open(filename, 'w') as f:
            json.dump({
                'results': serializable_results,
                'timestamp': results['timestamp']
            }, f, indent=2)
    else:
        with open(filename, 'w') as f:
            f.write("Committee Validation Results\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Missing details
            f.write("COMMITTEES MISSING DETAILS\n")
            f.write("=========================\n")
            
            f.write("\nMissing Website:\n")
            for committee in results['details']['missing_website']:
                f.write(f"  {committee[1]} ({committee[0]}) - Chamber: {committee[2]}\n")
            
            f.write("\nMissing Phone:\n")
            for committee in results['details']['missing_phone']:
                f.write(f"  {committee[1]} ({committee[0]}) - Chamber: {committee[2]}\n")
            
            f.write("\nMissing Address:\n")
            for committee in results['details']['missing_address']:
                f.write(f"  {committee[1]} ({committee[0]}) - Chamber: {committee[2]}\n")
            
            f.write("\nMissing Jurisdiction:\n")
            for committee in results['details']['missing_jurisdiction']:
                f.write(f"  {committee[1]} ({committee[0]}) - Chamber: {committee[2]}\n")
            
            # Relationship issues
            f.write("\n\nCOMMITTEE RELATIONSHIP ISSUES\n")
            f.write("=============================\n")
            
            f.write("\nInvalid Parent Committee:\n")
            for committee in results['relationships']['invalid_parent']:
                f.write(f"  {committee[1]} ({committee[0]}) - Invalid Parent: {committee[2]}\n")
            
            f.write("\nMissing Member Associations:\n")
            for committee in results['relationships']['missing_members']:
                f.write(f"  {committee[1]} ({committee[0]}) - Chamber: {committee[2]}\n")
            
            f.write("\nMissing Historical Data:\n")
            for committee in results['relationships']['missing_history']:
                f.write(f"  {committee[1]} ({committee[0]})\n")
    
    logger.info(f"Validation results exported to {filename}")
    return filename

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Validate committee data in the database')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    parser.add_argument('--output', help='Output file path')
    args = parser.parse_args()
    
    try:
        # Run validation checks
        logger.info("Checking for committees missing details...")
        missing_details = check_missing_details()
        
        logger.info("Checking for committee relationship issues...")
        relationship_issues = check_committee_relationships()
        
        # Combine results
        results = {
            'details': missing_details,
            'relationships': relationship_issues,
            'timestamp': datetime.now().isoformat()
        }
        
        # Print summary
        total_missing_details = sum(len(v) for v in missing_details.values())
        total_relationship_issues = sum(len(v) for v in relationship_issues.values())
        
        logger.info(f"Found {total_missing_details} committees missing details")
        logger.info(f"Found {total_relationship_issues} committees with relationship issues")
        
        # Export results
        output_file = export_validation_results(results, args.format, args.output)
        logger.info(f"Results exported to {output_file}")
        
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
"""
Core committee fetching functionality with incremental processing.
Retrieves committees from Congress.gov API and stores them in the database.
"""

import os
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Import utilities
from congressgov.utils.logging_config import setup_logging
from congressgov.utils.api import APIClient
from congressgov.utils.database import get_db_connection, with_db_transaction
from congressgov.utils.file_storage import ensure_directory, save_json, cleanup_old_files
from congressgov.committee_fetch.committee_utils import normalize_committee_name, format_committee_display_name

# Set up logging
logger = setup_logging(__name__)

# API configuration
BASE_API_URL = "https://api.congress.gov/v3"
COMMITTEES_LIST_ENDPOINT = "committee"
SYNC_STATUS_TABLE = "api_sync_status"
DEFAULT_LIMIT = 250
RAW_DATA_RETENTION_DAYS = 30

def get_last_sync_timestamp() -> Optional[datetime]:
    """Get the last successful sync timestamp from the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT last_sync_timestamp 
                FROM {SYNC_STATUS_TABLE} 
                WHERE endpoint = %s AND status = 'success'
                ORDER BY last_sync_timestamp DESC 
                LIMIT 1
            """, (COMMITTEES_LIST_ENDPOINT,))
            result = cur.fetchone()
            return result[0] if result else None

def update_sync_status(status: str, offset: int = 0, error: str = None):
    """Update sync status in the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {SYNC_STATUS_TABLE} (
                    endpoint, last_sync_timestamp, last_successful_offset,
                    status, last_error
                ) VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s)
                ON CONFLICT (endpoint) DO UPDATE SET
                    last_sync_timestamp = CURRENT_TIMESTAMP,
                    last_successful_offset = EXCLUDED.last_successful_offset,
                    status = EXCLUDED.status,
                    last_error = EXCLUDED.last_error
            """, (COMMITTEES_LIST_ENDPOINT, offset, status, error))
            conn.commit()

def save_committees_to_json(committees_data: Dict[str, Any], timestamp: str = None) -> str:
    """Save committees data to a JSON file."""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    raw_dir = ensure_directory(os.path.dirname(__file__), 'raw', timestamp)
    filename = f"committees_{timestamp}.json"
    
    return save_json(committees_data, raw_dir, filename)

@with_db_transaction
def update_database(cursor, committees: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Update database with committee information.
    
    Args:
        cursor: Database cursor
        committees: List of committee data dictionaries
        
    Returns:
        Dictionary with counts of inserted, updated, and skipped committees
    """
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "error": 0}
    
    for committee in committees:
        try:
            # Extract committee data
            committee_id = committee.get('committeeId')
            if not committee_id:
                logger.warning(f"Committee missing ID: {committee}")
                stats["skipped"] += 1
                continue
                
            name = committee.get('name', '')
            normalized_name = normalize_committee_name(name)
            chamber = committee.get('chamber', '')
            parent_id = committee.get('parentCommitteeId')
            jurisdiction = committee.get('jurisdiction', '')
            
            # Check if committee already exists
            cursor.execute("SELECT id, updated_at FROM committees WHERE committee_id = %s", (committee_id,))
            existing_committee = cursor.fetchone()
            
            # For incremental processing: if committee exists and hasn't been modified since our data,
            # we can skip it
            if existing_committee and committee.get('updateDate'):
                try:
                    committee_update_date = datetime.fromisoformat(committee.get('updateDate').replace('Z', '+00:00'))
                    db_update_date = existing_committee[1]
                    
                    if db_update_date and db_update_date >= committee_update_date:
                        logger.debug(f"Skipping committee {committee_id} - no updates")
                        stats["skipped"] += 1
                        continue
                except ValueError:
                    # If date parsing fails, proceed with update
                    pass
            
            # Insert or update committee
            cursor.execute("""
                INSERT INTO committees (
                    committee_id, name, normalized_name, chamber, 
                    parent_committee_id, jurisdiction, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (committee_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    normalized_name = EXCLUDED.normalized_name,
                    chamber = EXCLUDED.chamber,
                    parent_committee_id = EXCLUDED.parent_committee_id,
                    jurisdiction = EXCLUDED.jurisdiction,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                committee_id, name, normalized_name, chamber,
                parent_id, jurisdiction
            ))
            
            committee_db_id = cursor.fetchone()[0]
            
            # Add committee history entry
            current_congress = committee.get('congress')
            if current_congress:
                cursor.execute("""
                    INSERT INTO committee_history (
                        committee_id, congress, name, jurisdiction,
                        parent_committee_id, effective_date
                    ) VALUES (%s, %s, %s, %s, %s, CURRENT_DATE)
                    ON CONFLICT DO NOTHING
                """, (
                    committee_db_id, current_congress, name, jurisdiction, parent_id
                ))
            
            # Record type of operation for stats
            if existing_committee:
                stats["updated"] += 1
            else:
                stats["inserted"] += 1
                
        except Exception as e:
            logger.error(f"Error processing committee {committee.get('committeeId', 'unknown')}: {str(e)}")
            stats["error"] += 1
    
    return stats

def fetch_committees(api_client: APIClient, from_date: Optional[datetime] = None, 
                     to_date: Optional[datetime] = None, limit: int = DEFAULT_LIMIT) -> Dict[str, Any]:
    """
    Fetch committees from Congress.gov API.
    
    Args:
        api_client: API client
        from_date: Start date filter
        to_date: End date filter
        limit: Maximum committees per page
        
    Returns:
        Dictionary with fetched committees data
    """
    params = {
        'limit': limit,
        'sort': 'updateDate desc'
    }
    
    # Add date filtering if provided
    if from_date:
        params['fromDateTime'] = from_date.strftime("%Y-%m-%dT00:00:00Z")
    if to_date:
        params['toDateTime'] = to_date.strftime("%Y-%m-%dT23:59:59Z")
    
    # Get all committees using pagination
    committees = api_client.get_paginated(COMMITTEES_LIST_ENDPOINT, params, 'committees')
    
    return {'committees': committees, 'fetchDate': datetime.now().isoformat()}

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Fetch committees from Congress.gov API')
    parser.add_argument('--force-full', action='store_true', help='Force full sync instead of incremental')
    parser.add_argument('--start-date', help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', help='End date in YYYY-MM-DD format')
    parser.add_argument('--days', type=int, default=7, help='Number of days to look back for incremental sync')
    parser.add_argument('--chamber', choices=['house', 'senate', 'joint'], help='Filter by chamber')
    args = parser.parse_args()
    
    try:
        # Initialize API client
        api_client = APIClient(BASE_API_URL)
        
        # Start incremental sync by default
        from_date = None
        to_date = None
        
        # Use command line date filters if provided
        if args.start_date:
            from_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        
        if args.end_date:
            to_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        
        # If not forced and no explicit dates, get last sync date
        if not args.force_full and not args.start_date:
            last_sync = get_last_sync_timestamp()
            if last_sync:
                # Look back a few days before last sync to ensure no gaps
                from_date = last_sync - timedelta(days=args.days)
                logger.info(f"Running incremental sync from {from_date.isoformat()}")
            else:
                logger.info("No previous sync found, running full sync")
        
        # Update status to in-progress
        update_sync_status('in_progress')
        
        # Fetch committees
        logger.info("Fetching committees from Congress.gov API")
        committees_data = fetch_committees(api_client, from_date, to_date)
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = save_committees_to_json(committees_data, timestamp)
        logger.info(f"Committees data saved to {file_path}")
        
        # Clean up old files
        cleanup_old_files(os.path.join(os.path.dirname(__file__), 'raw'), 
                         pattern='*', days=RAW_DATA_RETENTION_DAYS)
        
        # Update database
        if committees_data['committees']:
            # Filter by chamber if requested
            if args.chamber:
                committees = [c for c in committees_data['committees'] 
                             if c.get('chamber', '').lower() == args.chamber.lower()]
                logger.info(f"Filtered to {len(committees)} {args.chamber} committees from {len(committees_data['committees'])} total")
            else:
                committees = committees_data['committees']
                
            logger.info(f"Updating database with {len(committees)} committees")
            stats = update_database(committees)
            logger.info(f"Database updated: {stats['inserted']} inserted, {stats['updated']} updated, "
                       f"{stats['skipped']} skipped, {stats['error']} errors")
        else:
            logger.info("No committees to update")
        
        # Update sync status to success
        update_sync_status('success')
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        update_sync_status('failed', error=str(e))
        raise

if __name__ == "__main__":
    main()
```

#### committee_detail_processor.py

This script handles fetching and processing detailed committee information, including contact details, website, and more specific data points.

```python
#!/usr/bin/env python3
"""
Committee detail processor - fetches detailed information for committees.
Handles contact information, website, jurisdiction, and related data.
"""

import os
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Import utilities
from congressgov.utils.logging_config import setup_logging
from congressgov.utils.api import APIClient
from congressgov.utils.database import get_db_connection, with_db_transaction
from congressgov.utils.file_storage import ensure_directory, save_json, cleanup_old_files
from congressgov.committee_fetch.committee_utils import normalize_phone_number, format_jurisdiction

# Set up logging
logger = setup_logging(__name__)

# API configuration
BASE_API_URL = "https://api.congress.gov/v3"
COMMITTEE_DETAIL_ENDPOINT = "committee/{committeeId}"
SYNC_STATUS_TABLE = "api_sync_status"
RAW_DATA_RETENTION_DAYS = 30

class CommitteeDetailProcessor:
    """Class for processing committee details."""
    
    def __init__(self, api_client: APIClient):
        """Initialize with API client."""
        self.api_client = api_client
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.raw_dir = ensure_directory(os.path.dirname(__file__), 'raw', 'details', self.timestamp)
    
    def fetch_committee_detail(self, committee_id: str) -> Dict[str, Any]:
        """Fetch detailed committee information."""
        endpoint = COMMITTEE_DETAIL_ENDPOINT.format(committeeId=committee_id)
        
        logger.info(f"Fetching details for committee {committee_id}")
        return self.api_client.get(endpoint)
    
    def save_committee_data(self, data: Dict[str, Any], committee_id: str, data_type: str = 'details') -> str:
        """Save committee data to a JSON file."""
        dir_path = ensure_directory(self.raw_dir, committee_id)
        filename = f"{data_type}.json"
        
        return save_json(data, dir_path, filename)
    
    @with_db_transaction
    def update_committee_details(self, cursor, committee_data: Dict[str, Any]) -> bool:
        """Update committee details in the database."""
        if 'committee' not in committee_data:
            logger.warning("No committee data found in response")
            return False
            
        committee = committee_data['committee']
        committee_id = committee.get('committeeId')
        
        if not committee_id:
            logger.warning("No committee ID found in committee data")
            return False
            
        # Extract detailed committee information
        name = committee.get('name')
        chamber = committee.get('chamber')
        jurisdiction = format_jurisdiction(committee.get('jurisdiction', ''))
        website = committee.get('url')
        phone = normalize_phone_number(committee.get('phone'))
        address = committee.get('address')
        parent_id = committee.get('parentCommitteeId')
        
        # Update the committees table with additional details
        cursor.execute("""
            UPDATE committees SET
                name = %s,
                chamber = %s,
                jurisdiction = %s,
                website = %s,
                phone = %s,
                address = %s,
                parent_committee_id = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE committee_id = %s
            RETURNING id
        """, (
            name,
            chamber,
            jurisdiction,
            website,
            phone,
            address,
            parent_id,
            committee_id
        ))
        
        result = cursor.fetchone()
        if not result:
            logger.warning(f"No committee record found for {committee_id}")
            return False
            
        committee_db_id = result[0]
        
        # Process current Congress information if available
        if 'congress' in committee:
            current_congress = committee['congress']
            
            # Update committee history
            cursor.execute("""
                INSERT INTO committee_history (
                    committee_id, congress, name, jurisdiction,
                    parent_committee_id, effective_date
                ) VALUES (%s, %s, %s, %s, %s, CURRENT_DATE)
                ON CONFLICT (committee_id, congress) DO UPDATE SET
                    name = EXCLUDED.name,
                    jurisdiction = EXCLUDED.jurisdiction,
                    parent_committee_id = EXCLUDED.parent_committee_id
            """, (
                committee_db_id,
                current_congress,
                name,
                jurisdiction,
                parent_id
            ))
        
        return True
    
    def process_committee(self, committee_id: str) -> Dict[str, Any]:
        """Process a single committee, fetching and updating detailed information."""
        results = {
            "committee_id": committee_id,
            "status": "success",
            "details_updated": False
        }
        
        try:
            # Fetch committee details
            committee_data = self.fetch_committee_detail(committee_id)
            
            # Save raw data
            self.save_committee_data(committee_data, committee_id, 'details')
            
            # Update committee details
            results["details_updated"] = self.update_committee_details(committee_data)
            
            logger.info(f"Successfully processed committee {committee_id}")
            
        except Exception as e:
            logger.error(f"Error processing committee {committee_id}: {str(e)}", exc_info=True)
            results["status"] = "failed"
            results["error"] = str(e)
            
        return results

def get_committees_for_processing(recent_only: bool = True, days: int = 7, limit: int = 100) -> List[str]:
    """Get committees to process, either recently updated or all."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if recent_only:
                # Get committees updated in the last N days
                cutoff_date = datetime.now() - timedelta(days=days)
                cur.execute("""
                    SELECT committee_id 
                    FROM committees 
                    WHERE updated_at >= %s
                    ORDER BY updated_at ASC
                    LIMIT %s
                """, (cutoff_date, limit))
            else:
                # Get committees with missing details or oldest updated
                cur.execute("""
                    SELECT committee_id 
                    FROM committees 
                    WHERE website IS NULL
                       OR phone IS NULL
                       OR address IS NULL
                    UNION
                    SELECT committee_id 
                    FROM committees 
                    ORDER BY updated_at ASC NULLS FIRST
                    LIMIT %s
                """, (limit,))
            
            return [row[0] for row in cur.fetchall()]

def update_sync_status(status: str, processed: int = 0, errors: int = 0, error: str = None):
    """Update sync status in the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {SYNC_STATUS_TABLE} (
                    endpoint, last_sync_timestamp, last_successful_offset,
                    status, last_error
                ) VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s)
                ON CONFLICT (endpoint) DO UPDATE SET
                    last_sync_timestamp = CURRENT_TIMESTAMP,
                    last_successful_offset = EXCLUDED.last_successful_offset,
                    status = EXCLUDED.status,
                    last_error = EXCLUDED.last_error
            """, (COMMITTEE_DETAIL_ENDPOINT, processed, status, error))
            conn.commit()

def main():
    parser = argparse.ArgumentParser(description='Process committee details')
    parser.add_argument('--committee', help='Process specific committee by ID')
    parser.add_argument('--all', action='store_true', help='Process all committees instead of just recent ones')
    parser.add_argument('--days', type=int, default=7, help='For recent mode, how many days back to consider')
    parser.add_argument('--limit', type=int, default=100, help='Maximum number of committees to process')
    parser.add_argument('--missing', action='store_true', help='Focus on committees with missing details')
    args = parser.parse_args()
    
    try:
        # Initialize API client
        api_client = APIClient(BASE_API_URL)
        
        # Initialize processor
        processor = CommitteeDetailProcessor(api_client)
        
        # Update status to in-progress
        update_sync_status('in_progress')
        
        # Determine which committees to process
        if args.committee:
            # Process single specified committee
            committees_to_process = [args.committee]
            logger.info(f"Processing single committee: {args.committee}")
        else:
            # Get committees from database
            recent_only = not args.all and not args.missing
            committees_to_process = get_committees_for_processing(recent_only, args.days, args.limit)
            logger.info(f"Processing {len(committees_to_process)} committees")
        
        # Process each committee
        results = []
        processed_count = 0
        error_count = 0
        
        for committee_id in committees_to_process:
            try:
                result = processor.process_committee(committee_id)
                results.append(result)
                
                if result['status'] == 'success':
                    processed_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing committee {committee_id}: {str(e)}", exc_info=True)
                error_count += 1
        
        # Clean up old files
        cleanup_old_files(os.path.join(os.path.dirname(__file__), 'raw', 'details'), 
                         pattern='*', days=RAW_DATA_RETENTION_DAYS)
        
        # Update sync status to success
        if error_count == 0:
            update_sync_status('success', processed_count)
        else:
            update_sync_status('completed_with_errors', processed_count, error_count)
        
        logger.info(f"Process completed. {processed_count} committees processed successfully, {error_count} errors.")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        update_sync_status('failed', error=str(e))
        raise

if __name__ == "__main__":
    main()
```

#### committee_validation.py

This script checks for missing or incomplete committee data to help monitor data quality.

```python
#!/usr/bin/env python3