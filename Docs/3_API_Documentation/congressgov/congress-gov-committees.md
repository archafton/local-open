# 1. Overview and Schema Extensions

## Overview

The Committees module will be responsible for fetching, processing, and enriching committee data from the Congress.gov/GPO endpoint. It will follow the same architectural patterns as the existing bills and members modules, including:

- Incremental and full data syncing capabilities
- Raw API response storage for auditing
- Comprehensive error handling with retry mechanisms
- Database sync status tracking
- Batch and parallel processing support
- REST API endpoints for frontend consumption

## Schema Extensions

### Core Committee Tables

```sql
-- Primary committee table
CREATE TABLE committees (
  id SERIAL PRIMARY KEY,
  committee_id VARCHAR(50) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  normalized_name VARCHAR(255) NOT NULL,
  chamber VARCHAR(50) NOT NULL,
  jurisdiction TEXT,
  parent_committee_id VARCHAR(50),
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
  role VARCHAR(100),
  start_date DATE,
  end_date DATE,
  congress INTEGER,
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
```

### Indexes and Enhancements

```sql
-- Add indexes for performance
CREATE INDEX idx_committees_chamber ON committees(chamber);
CREATE INDEX idx_committees_parent_id ON committees(parent_committee_id);
CREATE INDEX idx_committees_normalized_name ON committees(normalized_name);
CREATE INDEX idx_committee_members_member_id ON committee_members(member_id);
CREATE INDEX idx_committee_members_congress ON committee_members(congress);

-- Enhance bill_committees table
ALTER TABLE bill_committees
ADD COLUMN IF NOT EXISTS referral_date DATE,
ADD COLUMN IF NOT EXISTS referral_type VARCHAR(50);

-- Add updated_at timestamp trigger
CREATE TRIGGER update_committees_updated_at
    BEFORE UPDATE ON committees
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Environment Variables

```
# Committee API settings
COMMITTEE_API_BASE_URL=https://api.congress.gov/v3/committee
COMMITTEE_DATA_RETENTION_DAYS=30
```

# 2. Python Structure and Utility Module

## Directory Structure

The committees module will fit into the existing project structure:

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
│       │   └── committee.py             # NEW: Committee data queries
│       ├── api/
│       │   └── committees.py            # NEW: API endpoints
│       └── utils/                       # Shared utilities
```

## Utility Module

The `committee_utils.py` module will provide helper functions for processing committee data:

```python
"""
Committee-related utilities for processing Congress.gov data.
"""

def normalize_committee_name(name: str) -> str:
    """Convert a tag name to its normalized form (lowercase, no special chars)."""
    if not name:
        return ""
    
    # Convert to lowercase, remove special characters, replace spaces with underscores
    normalized = re.sub(r'[^\w\s]', '', name.lower())
    normalized = re.sub(r'\s+', '_', normalized)
    return normalized

def format_committee_display_name(name: str, chamber: str) -> str:
    """Format committee name for display with chamber prefix if needed."""
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
    """Normalize phone number to (XXX) XXX-XXXX format."""
    # Implementation details

def parse_committee_hierarchy(committee_id: str, parent_id: Optional[str]) -> Tuple[bool, int]:
    """Determine if committee is a subcommittee and its hierarchy level."""
    # Implementation details
```

These utility functions follow the same pattern as those in `bill_utils.py` and `member_utils.py`, focusing on data normalization and formatting.

# 3. Core Processing Scripts

The committee processing pipeline consists of several scripts that work together to fetch, process, and update committee data.

## Committee Fetch Core

The `committee_fetch_core.py` script will handle the initial fetching of committee metadata:

```python
"""
Core committee fetching functionality with incremental processing.
Retrieves committees from Congress.gov API and stores them in the database.
"""

# Key functions:
# - get_last_sync_timestamp(): Get the last successful sync timestamp
# - update_sync_status(): Update sync status in the database
# - fetch_committees(): Fetch committees from the API with pagination
# - update_database(): Insert or update committee records
# - save_committees_to_json(): Save raw API response to files

def main():
    """Main function with command-line argument handling."""
    # Parse arguments for --force-full, --start-date, --end-date, etc.
    
    # Determine sync mode (incremental or full)
    
    # Update status to in-progress
    
    # Fetch committees from Congress.gov API
    
    # Save raw data for auditing
    
    # Update database with fetched committees
    
    # Clean up old files
    
    # Update sync status to success
```

This script closely follows the pattern from `bill_fetch_core.py`, including:
- Reading the last sync timestamp from the database
- Supporting both incremental and full sync modes
- Tracking sync status in the `api_sync_status` table
- Saving raw API responses to JSON files
- Cleaning up old files based on retention policy

## Committee Detail Processor

The `committee_detail_processor.py` script will fetch detailed information for committees:

```python
"""
Committee detail processor - fetches detailed information for committees.
Handles contact information, website, jurisdiction, and related data.
"""

class CommitteeDetailProcessor:
    """Class for processing committee details."""
    
    def __init__(self, api_client: APIClient):
        """Initialize with API client and set up file storage."""
        
    def fetch_committee_detail(self, committee_id: str) -> Dict[str, Any]:
        """Fetch detailed committee information."""
        
    def save_committee_data(self, data: Dict[str, Any], committee_id: str, data_type: str = 'details') -> str:
        """Save committee data to a JSON file."""
        
    @with_db_transaction
    def update_committee_details(self, cursor, committee_data: Dict[str, Any]) -> bool:
        """Update committee details in the database."""
        
    def process_committee(self, committee_id: str) -> Dict[str, Any]:
        """Process a single committee, fetching and updating detailed information."""
```

This class follows the pattern from `member_detail_processor.py` and provides:
- Detailed committee data fetching
- Transaction-safe database updates
- Raw data storage for auditing
- Comprehensive error handling
- Status reporting

## Committee Member Processor

The `committee_member_processor.py` script will handle committee-member relationships:

```python
"""
Committee-member relationship processor - associates members with their committee assignments.
"""

class CommitteeMemberProcessor:
    """Handles processing committee-member relationships."""
    
    def fetch_committee_members(self, committee_id: str) -> Dict[str, Any]:
        """Fetch members for a specific committee."""
        
    @with_db_transaction
    def update_committee_members(self, cursor, committee_id: str, members_data: Dict[str, Any]) -> int:
        """Update committee-member relationships in the database."""
        
    def process_committee(self, committee_id: str) -> Dict[str, Any]:
        """Process members for a single committee."""
```

This script handles the association between committees and members, tracking information such as:
- Member roles within committees (Chair, Ranking Member, etc.)
- Start and end dates for committee assignments
- Congress number for historical tracking

Let's move on to the next section.

# 4. Validation and Member Processing

## Committee Validation

The `committee_validation.py` script will check for missing or inconsistent committee data:

```python
"""
Committee validation script - checks for missing or incomplete committee data.
"""

def check_missing_details():
    """
    Check for committees missing detailed information.
    
    Returns:
        Dictionary with lists of committee IDs missing various details
    """
    # Checks for missing website, phone, address, jurisdiction

def check_committee_relationships():
    """
    Check for issues with committee relationships.
    
    Returns:
        Dictionary with lists of committee IDs with relationship issues
    """
    # Checks for:
    # - Subcommittees with invalid parent references
    # - Committees missing member associations
    # - Committee history gaps

def export_validation_results(results, output_format='text', output_file=None):
    """Export validation results to a file in text or JSON format."""
```

This validation script serves several purposes:
- Quality assurance for committee data
- Identifying committees needing additional processing
- Providing reports for data completeness monitoring
- Supporting troubleshooting of data issues

## Committee Batch Processor

The `committee_batch_processor.py` script supports batch processing of committees:

```python
"""
Batch processor for committees - for processing large volumes of committee data
or filling in missing data. Supports batched operations and parallel processing.
"""

def get_all_committees(chamber: str = None, limit: int = None) -> List[Tuple[int, str]]:
    """Get all committees from the database, optionally filtered by chamber."""

def get_committees_missing_data(data_type: str, limit: int = None) -> List[Tuple[int, str]]:
    """Get committees missing specific data."""
    
def process_committee_batch(committees: List[Tuple[int, str]], process_type: str, 
                           batch_size: int = 5, parallel: bool = False) -> Dict[str, int]:
    """Process a batch of committees, optionally in parallel."""
```

Key features of the batch processor include:
- Support for processing committees in batches
- Optional parallel processing for improved performance
- Ability to focus on committees missing specific data
- Chamber-specific processing (House, Senate, Joint)
- Statistics reporting on processing results

This script is particularly useful for:
- Initial data population
- Filling in data gaps identified by the validation script
- Processing historical committee data
- Performing focused updates on specific committee types

# 5. API Endpoints and Database Models

## Database Models (models/committee.py)

The committee data models will handle database queries for committee data:

```python
"""
Committee data models and database queries.
"""

def get_all_committees(filter_chamber: str = None, 
                      filter_parent: str = None,
                      include_members: bool = False,
                      include_subcommittees: bool = False) -> List[Dict[str, Any]]:
    """Get all committees with optional filtering."""
    # Implementation with filtering options and relationship loading

def get_committee_by_id(committee_id: str, include_members: bool = True,
                     include_subcommittees: bool = True) -> Optional[Dict[str, Any]]:
    """Get a single committee by ID with optional relationship loading."""
    # Implementation with parent and subcommittee relationship handling

def get_committee_members(committee_db_id: int) -> List[Dict[str, Any]]:
    """Get members for a specific committee."""
    # Implementation with role-based sorting

def get_member_committees(bioguide_id: str, current_only: bool = True) -> List[Dict[str, Any]]:
    """Get committees for a specific member."""
    # Implementation with hierarchical grouping

def get_bills_by_committee(committee_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get bills referred to a specific committee."""
    # Implementation with sorting by introduced date

def search_committees(query: str, chamber: str = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Search for committees by name or jurisdiction."""
    # Implementation with text search
```

The database models follow the same pattern as those for bills and members, providing:
- Filtering options for lists
- Relationship loading (members, subcommittees)
- Hierarchical data structuring
- Efficient database queries using indexes

## API Endpoints (api/committees.py)

The API endpoints will expose committee data to the frontend:

```python
"""
Committee API endpoints for accessing committee data.
"""

committee_bp = Blueprint('committees', __name__, url_prefix='/api/committees')

@committee_bp.route('/', methods=['GET'])
def list_committees():
    """Get a list of all committees with optional filtering."""
    # Implementation with chamber filtering and relationship inclusion options

@committee_bp.route('/<committee_id>', methods=['GET'])
def committee_detail(committee_id):
    """Get detailed information about a specific committee."""
    # Implementation with members and subcommittees

@committee_bp.route('/search', methods=['GET'])
def search():
    """Search for committees by name or jurisdiction."""
    # Implementation with text search

@committee_bp.route('/<committee_id>/bills', methods=['GET'])
def committee_bills(committee_id):
    """Get bills referred to a specific committee."""
    # Implementation with pagination

@committee_bp.route('/<committee_id>/stats', methods=['GET'])
def committee_stats(committee_id):
    """Get activity statistics for a specific committee."""
    # Implementation with bill and member statistics

@committee_bp.route('/member/<bioguide_id>', methods=['GET'])
def member_committees(bioguide_id):
    """Get committees for a specific member."""
    # Implementation with current vs. historical options
```

Key features of the API endpoints:
- REST-based design consistent with existing endpoints
- Query parameter support for filtering
- Relationship inclusion options for flexible data loading
- Search capabilities for committee discovery
- Statistics endpoints for analytics

Thank you! Let's continue with the next section.

# 6. Frontend Integration

To integrate committee data into the frontend, we'll need React components that interact with the API endpoints.

## Committee List Component

```jsx
// src/components/CommitteesList.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const CommitteesList = () => {
  const [committees, setCommittees] = useState([]);
  const [chamber, setChamber] = useState('all');
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Fetch committees with optional chamber filter
    // Update state with results
  }, [chamber]);
  
  return (
    <div className="committees-list">
      {/* Chamber filter controls */}
      <div className="committees">
        {/* Render committee cards with links to detail view */}
        {/* Show subcommittees if available */}
      </div>
    </div>
  );
};
```

## Committee Detail Component

```jsx
// src/components/CommitteeDetail.jsx
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';

const CommitteeDetail = () => {
  const { committeeId } = useParams();
  const [committee, setCommittee] = useState(null);
  const [bills, setBills] = useState([]);
  
  useEffect(() => {
    // Fetch committee details and related bills
  }, [committeeId]);
  
  return (
    <div className="committee-detail">
      {/* Committee header with name and metadata */}
      {/* Jurisdiction section */}
      {/* Contact information section */}
      {/* Members list grouped by role */}
      {/* Subcommittees section if parent committee */}
      {/* Recent bills section */}
    </div>
  );
};
```

These components will:
- Fetch data from the API endpoints
- Provide filtering options for users
- Display hierarchical committee relationships
- Link to related data (members, bills)
- Handle loading states and errors appropriately

# 7. Testing Strategy

The committees module should include comprehensive testing to ensure reliability:

## Unit Tests

```python
# tests/test_committee_utils.py
import unittest
from congressgov.committee_fetch.committee_utils import normalize_committee_name

class TestCommitteeUtils(unittest.TestCase):
    def test_normalize_committee_name(self):
        self.assertEqual(normalize_committee_name("Budget & Appropriations"), "budget_and_appropriations")
        # More test cases...
```

## Integration Tests

```python
# tests/test_committee_integration.py
import unittest
from congressgov.utils.api import APIClient
from congressgov.committee_fetch.committee_detail_processor import CommitteeDetailProcessor

class TestCommitteeIntegration(unittest.TestCase):
    def setUp(self):
        self.api_client = APIClient(os.getenv('CONGRESSGOV_API_BASE_URL'))
        self.processor = CommitteeDetailProcessor(self.api_client)
    
    def test_fetch_and_process_committee(self):
        # Test with a known stable committee
        # Verify database entry
```

## Mock API Responses

```python
# tests/mocks/committee_responses.py
MOCK_COMMITTEE_LIST = {
    "committees": [
        {
            "committeeId": "hscai",
            "name": "Permanent Select Committee on Intelligence",
            # Other properties...
        },
        # More committees...
    ]
}
```

These testing approaches will ensure:
- Utility functions work correctly
- Database operations maintain data integrity
- API integration functions as expected
- Edge cases are handled appropriately

Let's continue with the final section on deployment and monitoring.

# 8. Deployment and Monitoring

## Database Migration

To add the new committee tables to the database, we'll create a migration script:

```sql
-- migration_committees.sql

-- Add new committee tables
CREATE TABLE IF NOT EXISTS committees (...);
CREATE TABLE IF NOT EXISTS committee_members (...);
CREATE TABLE IF NOT EXISTS committee_history (...);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_committees_chamber ON committees(chamber);
-- Additional indexes...

-- Enhance bill_committees table
ALTER TABLE bill_committees
ADD COLUMN IF NOT EXISTS referral_date DATE,
ADD COLUMN IF NOT EXISTS referral_type VARCHAR(50);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column() ... ;
```

## Health Check Script

```python
#!/usr/bin/env python3
"""
Committee data health check script.
"""

def check_committee_data_health():
    """Check the health of committee data."""
    # Check for recent sync status
    # Check committee counts
    # Check for missing data
    # Check for orphaned subcommittees
    # Check for recent updates
    # Return overall health status
```

## Scheduled Updates

Set up cron jobs to run committee data updates regularly:

```bash
# crontab -e

# Run committee fetch every day at 2:00 AM
0 2 * * * cd /path/to/project-tacitus && python3 congressgov/committee_fetch/committee_fetch_core.py

# Run committee detail processor every day at 3:00 AM
0 3 * * * cd /path/to/project-tacitus && python3 congressgov/committee_fetch/committee_detail_processor.py

# Run committee member processor every day at 4:00 AM
0 4 * * * cd /path/to/project-tacitus && python3 congressgov/committee_fetch/committee_member_processor.py
```

## Monitoring Dashboards

Create monitoring dashboards to track:
- Sync status and failures
- Data completeness metrics
- API performance statistics
- Error rates and types

## Common Workflows

Here are some common workflows for operating the committee processing system:


## Common Workflows and Usage Examples

### Complete Initial Data Load

For a complete initial data load, run these commands in sequence:

```bash
# 1. Fetch all basic committee data
python committee_fetch_core.py --force-full

# 2. Fetch detailed information for all committees
python committee_detail_processor.py --all

# 3. Process committee-member relationships
python committee_member_processor.py --all --limit 100

# 4. Validate the data and identify any gaps
python committee_validation.py
```

### Regular Daily Updates

For regular daily updates, run:

```bash
# 1. Fetch updated committee data (incremental)
python committee_fetch_core.py

# 2. Process details for recently updated committees
python committee_detail_processor.py

# 3. Update committee-member relationships for recently updated committees
python committee_member_processor.py

# 4. Run validation to check for any issues
python committee_validation.py
```

### Filling in Missing Data

To fill in missing data:

```bash
# 1. Run validation to identify issues
python committee_validation.py

# 2. Process committees missing contact information
python committee_batch_processor.py --process-type details --missing details

# 3. Process committees missing member information
python committee_batch_processor.py --process-type members --missing members

# 4. Check for committees missing historical data
python committee_batch_processor.py --process-type details --missing history
```

### Chamber-Specific Processing

To process committees from a specific chamber:

```bash
# Process all House committees
python committee_batch_processor.py --chamber house --process-type details

# Process all Senate committees
python committee_batch_processor.py --chamber senate --process-type members

# Process only Joint committees
python committee_fetch_core.py --chamber joint
```

# Conclusion

This committee processing system integrates seamlessly with the existing Project Tacitus architecture, providing a robust solution for tracking legislative committees and their activities. The implementation follows the same patterns used for bills and members, ensuring consistency and maintainability.

Key benefits include:
- Consistent architecture with existing modules
- Comprehensive data coverage
- Efficient incremental processing
- Robust validation and monitoring
- Performance optimization with caching and indexing

This completes the legislative data triad of bills, members, and committees, providing a full picture of the legislative process for Project Tacitus users.