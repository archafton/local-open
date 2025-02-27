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

## Testing Strategy

The committees module should include comprehensive testing to ensure reliability. Here are the key testing components:

### Unit Tests

Create unit tests for the utility functions and core processing logic:

```bash
# File: tests/test_committee_utils.py

import unittest
from congressgov.committee_fetch.committee_utils import (
    normalize_committee_name, 
    format_committee_display_name,
    normalize_phone_number,
    format_jurisdiction,
    parse_committee_hierarchy
)

class TestCommitteeUtils(unittest.TestCase):
    def test_normalize_committee_name(self):
        self.assertEqual(normalize_committee_name("Budget & Appropriations"), "budget_and_appropriations")
        self.assertEqual(normalize_committee_name("HEALTH, EDUCATION & WELFARE"), "health_education_and_welfare")
        self.assertEqual(normalize_committee_name(None), "")
    
    def test_format_committee_display_name(self):
        self.assertEqual(format_committee_display_name("Budget", "house"), "House Budget")
        self.assertEqual(format_committee_display_name("House Budget", "house"), "House Budget")
        self.assertEqual(format_committee_display_name("Armed Services", "senate"), "Senate Armed Services")
    
    def test_normalize_phone_number(self):
        self.assertEqual(normalize_phone_number("202-555-1234"), "(202) 555-1234")
        self.assertEqual(normalize_phone_number("(202) 555-1234"), "(202) 555-1234")
        self.assertEqual(normalize_phone_number("202.555.1234"), "(202) 555-1234")
    
    def test_format_jurisdiction(self):
        self.assertEqual(
            format_jurisdiction("budget. appropriations. fiscal policy."), 
            "Budget. Appropriations. Fiscal policy."
        )
    
    def test_parse_committee_hierarchy(self):
        self.assertEqual(parse_committee_hierarchy("budget", None), (False, 0))
        self.assertEqual(parse_committee_hierarchy("budget_sub", "budget"), (True, 1))
        self.assertEqual(parse_committee_hierarchy("budget_sub_defense", "budget_sub"), (True, 2))

if __name__ == '__main__':
    unittest.main()
```

### Integration Tests

Create integration tests to verify the end-to-end functionality:

```bash
# File: tests/test_committee_integration.py

import unittest
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from congressgov.utils.api import APIClient
from congressgov.utils.database import get_db_connection
from congressgov.committee_fetch.committee_detail_processor import CommitteeDetailProcessor

class TestCommitteeIntegration(unittest.TestCase):
    def setUp(self):
        self.api_client = APIClient(os.getenv('CONGRESSGOV_API_BASE_URL'))
        self.processor = CommitteeDetailProcessor(self.api_client)
    
    def test_fetch_and_process_committee(self):
        # Test with a known stable committee
        committee_id = "hscai"  # House Permanent Select Committee on Intelligence
        result = self.processor.process_committee(committee_id)
        
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['details_updated'])
        
        # Verify database entry
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name, chamber FROM committees WHERE committee_id = %s", 
                           (committee_id,))
                committee = cur.fetchone()
                self.assertIsNotNone(committee)
                self.assertEqual(committee[1], "house")
    
    def test_committee_api_endpoints(self):
        # This would be implemented as an API test using requests or Flask test client
        pass

if __name__ == '__main__':
    unittest.main()
```

### Mock API Responses

Create mock API responses for testing without hitting the actual Congress.gov API:

```python
# File: tests/mocks/committee_responses.py

MOCK_COMMITTEE_LIST = {
    "committees": [
        {
            "committeeId": "hscai",
            "name": "Permanent Select Committee on Intelligence",
            "chamber": "House",
            "congress": "118",
            "jurisdiction": "The Permanent Select Committee on Intelligence oversees..."
        },
        {
            "committeeId": "hsag",
            "name": "Committee on Agriculture",
            "chamber": "House",
            "congress": "118",
            "jurisdiction": "Agriculture generally..."
        }
    ]
}

MOCK_COMMITTEE_DETAIL = {
    "committee": {
        "committeeId": "hscai",
        "name": "Permanent Select Committee on Intelligence",
        "chamber": "House",
        "congress": "118",
        "jurisdiction": "The Permanent Select Committee on Intelligence oversees...",
        "url": "https://intelligence.house.gov/",
        "phone": "(202) 555-1234",
        "address": "123 Capitol Hill, Washington DC 20515"
    }
}

MOCK_COMMITTEE_MEMBERS = {
    "committeeId": "hscai",
    "congress": "118",
    "members": [
        {
            "bioguideId": "T000476",
            "fullName": "Mike Turner",
            "role": "Chair",
            "party": "Republican",
            "state": "OH"
        },
        {
            "bioguideId": "H001082",
            "fullName": "Jim Himes",
            "role": "Ranking Member",
            "party": "Democrat",
            "state": "CT"
        }
    ]
}
```

## Caching Strategy

To improve performance, implement caching for committee data that doesn't change frequently:

```python
# In api/committees.py

from flask_caching import Cache
from flask import Flask, Blueprint, jsonify

app = Flask(__name__)
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 3600  # 1 hour
})

committee_bp = Blueprint('committees', __name__, url_prefix='/api/committees')

@committee_bp.route('/', methods=['GET'])
@cache.cached(timeout=3600, query_string=True)
def list_committees():
    # Implementation remains the same
    pass

@committee_bp.route('/<committee_id>', methods=['GET'])
@cache.cached(timeout=3600, query_string=True)
def committee_detail(committee_id):
    # Implementation remains the same
    pass

# Committee membership changes more frequently, so use shorter cache timeout
@committee_bp.route('/<committee_id>/members', methods=['GET'])
@cache.cached(timeout=1800, query_string=True)  # 30 minutes
def committee_members(committee_id):
    # Implementation
    pass

# Bills referred to committees change often, so use shorter cache timeout
@committee_bp.route('/<committee_id>/bills', methods=['GET'])
@cache.cached(timeout=900, query_string=True)  # 15 minutes
def committee_bills(committee_id):
    # Implementation
    pass
```

## Frontend Integration

Here's an example of how to integrate committee data into the frontend using React components:

```jsx
// src/components/CommitteesList.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const CommitteesList = () => {
  const [committees, setCommittees] = useState([]);
  const [chamber, setChamber] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchCommittees = async () => {
      setLoading(true);
      try {
        const params = chamber !== 'all' ? { chamber } : {};
        const response = await axios.get('/api/committees', { params });
        setCommittees(response.data.committees);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch committees');
        setLoading(false);
      }
    };
    
    fetchCommittees();
  }, [chamber]);
  
  if (loading) return <div>Loading committees...</div>;
  if (error) return <div className="error">{error}</div>;
  
  return (
    <div className="committees-list">
      <div className="filters">
        <select value={chamber} onChange={e => setChamber(e.target.value)}>
          <option value="all">All Chambers</option>
          <option value="house">House</option>
          <option value="senate">Senate</option>
          <option value="joint">Joint</option>
        </select>
      </div>
      
      <div className="committees">
        {committees.map(committee => (
          <div key={committee.committee_id} className="committee-card">
            <h3>
              <Link to={`/committees/${committee.committee_id}`}>
                {committee.name}
              </Link>
            </h3>
            <div className="committee-meta">
              <span className="chamber">{committee.chamber}</span>
              {committee.phone && <span className="phone">{committee.phone}</span>}
            </div>
            {committee.subcommittees && (
              <div className="subcommittees">
                <h4>Subcommittees ({committee.subcommittees.length})</h4>
                <ul>
                  {committee.subcommittees.map(sub => (
                    <li key={sub.committee_id}>
                      <Link to={`/committees/${sub.committee_id}`}>
                        {sub.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default CommitteesList;
```

```jsx
// src/components/CommitteeDetail.jsx
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';

const CommitteeDetail = () => {
  const { committeeId } = useParams();
  const [committee, setCommittee] = useState(null);
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchCommitteeData = async () => {
      setLoading(true);
      try {
        // Fetch committee details
        const committeeResponse = await axios.get(`/api/committees/${committeeId}`);
        setCommittee(committeeResponse.data);
        
        // Fetch committee bills
        const billsResponse = await axios.get(`/api/committees/${committeeId}/bills`);
        setBills(billsResponse.data.bills);
        
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch committee data');
        setLoading(false);
      }
    };
    
    fetchCommitteeData();
  }, [committeeId]);
  
  if (loading) return <div>Loading committee data...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!committee) return <div>Committee not found</div>;
  
  return (
    <div className="committee-detail">
      <div className="committee-header">
        <h1>{committee.name}</h1>
        <div className="committee-meta">
          <span className="chamber">{committee.chamber}</span>
          {committee.parent_committee_id && (
            <span className="parent">
              Subcommittee of{' '}
              <Link to={`/committees/${committee.parent_committee_id}`}>
                {committee.parent_committee?.name || 'Parent Committee'}
              </Link>
            </span>
          )}
        </div>
      </div>
      
      {committee.jurisdiction && (
        <div className="committee-jurisdiction">
          <h2>Jurisdiction</h2>
          <p>{committee.jurisdiction}</p>
        </div>
      )}
      
      {committee.website && (
        <div className="committee-contact">
          <h2>Contact Information</h2>
          <p>
            <a href={committee.website} target="_blank" rel="noopener noreferrer">
              {committee.website}
            </a>
          </p>
          {committee.phone && <p>Phone: {committee.phone}</p>}
          {committee.address && <p>Address: {committee.address}</p>}
        </div>
      )}
      
      {committee.members && committee.members.length > 0 && (
        <div className="committee-members">
          <h2>Committee Members</h2>
          <div className="member-list">
            {committee.members.map(member => (
              <div key={member.bioguide_id} className="member-card">
                <Link to={`/members/${member.bioguide_id}`}>
                  {member.full_name}
                </Link>
                <div className="member-meta">
                  <span className="role">{member.role}</span>
                  <span className="party">{member.party}</span>
                  <span className="state">{member.state}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {committee.subcommittees && committee.subcommittees.length > 0 && (
        <div className="subcommittees">
          <h2>Subcommittees</h2>
          <div className="subcommittee-list">
            {committee.subcommittees.map(sub => (
              <div key={sub.committee_id} className="subcommittee-card">
                <h3>
                  <Link to={`/committees/${sub.committee_id}`}>
                    {sub.name}
                  </Link>
                </h3>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {bills.length > 0 && (
        <div className="committee-bills">
          <h2>Recent Bills</h2>
          <div className="bill-list">
            {bills.map(bill => (
              <div key={bill.bill_number} className="bill-card">
                <h3>
                  <Link to={`/bills/${bill.bill_number}`}>
                    {bill.bill_number}: {bill.bill_title}
                  </Link>
                </h3>
                <div className="bill-meta">
                  <span className="status">{bill.normalized_status}</span>
                  <span className="date">
                    Introduced: {new Date(bill.introduced_date).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <Link to={`/committees/${committeeId}/bills`} className="view-all">
            View all bills
          </Link>
        </div>
      )}
    </div>
  );
};

export default CommitteeDetail;# Committees API Documentation

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

#### committee_member_processor.py

```python
#!/usr/bin/env python3
"""
Committee-member relationship processor - associates members with their committee assignments.
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

# Set up logging
logger = setup_logging(__name__)

# API configuration
BASE_API_URL = "https://api.congress.gov/v3"
COMMITTEE_MEMBERS_ENDPOINT = "committee/{committeeId}/members"
SYNC_STATUS_TABLE = "api_sync_status"
RAW_DATA_RETENTION_DAYS = 30

class CommitteeMemberProcessor:
    """Handles processing committee-member relationships."""
    
    def __init__(self, api_client: APIClient):
        """Initialize with API client."""
        self.api_client = api_client
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.raw_dir = ensure_directory(os.path.dirname(__file__), 'raw', 'members', self.timestamp)
    
    def fetch_committee_members(self, committee_id: str) -> Dict[str, Any]:
        """Fetch members for a specific committee."""
        endpoint = COMMITTEE_MEMBERS_ENDPOINT.format(committeeId=committee_id)
        
        logger.info(f"Fetching members for committee {committee_id}")
        return self.api_client.get(endpoint)
    
    def save_member_data(self, data: Dict[str, Any], committee_id: str) -> str:
        """Save member data to a JSON file."""
        dir_path = ensure_directory(self.raw_dir, committee_id)
        filename = f"members.json"
        
        return save_json(data, dir_path, filename)
    
    @with_db_transaction
    def update_committee_members(self, cursor, committee_id: str, members_data: Dict[str, Any]) -> int:
        """Update committee-member relationships in the database."""
        if 'members' not in members_data or not members_data['members']:
            logger.warning(f"No members found for committee {committee_id}")
            return 0
        
        # Get committee database ID
        cursor.execute("SELECT id FROM committees WHERE committee_id = %s", (committee_id,))
        result = cursor.fetchone()
        if not result:
            logger.warning(f"Committee {committee_id} not found in database")
            return 0
            
        committee_db_id = result[0]
        
        # Get current Congress
        members = members_data['members']
        current_congress = members_data.get('congress')
        if not current_congress:
            logger.warning("Congress not specified in member data")
            # Try to determine current Congress from the first member
            if members and isinstance(members, list) and len(members) > 0:
                current_congress = members[0].get('congress')
        
        if not current_congress:
            logger.warning("Could not determine Congress for committee members")
            current_congress = 118  # Fallback to a reasonable default
        
        # Process each member
        count = 0
        for member in members:
            bioguide_id = member.get('bioguideId')
            if not bioguide_id:
                logger.warning(f"Member missing bioguide ID: {member}")
                continue
            
            # Get member database ID
            cursor.execute("SELECT id FROM members WHERE bioguide_id = %s", (bioguide_id,))
            member_result = cursor.fetchone()
            if not member_result:
                logger.warning(f"Member {bioguide_id} not found in database")
                continue
                
            member_db_id = member_result[0]
            
            # Get role information
            role = member.get('role', 'Member')
            start_date = member.get('startDate')
            end_date = member.get('endDate')
            
            # Insert or update committee-member relationship
            cursor.execute("""
                INSERT INTO committee_members (
                    committee_id, member_id, role, start_date, end_date, congress
                ) VALUES (
                    %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (committee_id, member_id, congress) DO UPDATE SET
                    role = EXCLUDED.role,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date
            """, (
                committee_db_id,
                member_db_id,
                role,
                start_date,
                end_date,
                current_congress
            ))
            
            count += 1
        
        return count
    
    def process_committee(self, committee_id: str) -> Dict[str, Any]:
        """Process members for a single committee."""
        results = {
            "committee_id": committee_id,
            "status": "success",
            "members_updated": 0
        }
        
        try:
            # Fetch committee members
            members_data = self.fetch_committee_members(committee_id)
            
            # Save raw data
            self.save_member_data(members_data, committee_id)
            
            # Update committee-member relationships
            results["members_updated"] = self.update_committee_members(committee_id, members_data)
            
            logger.info(f"Successfully processed {results['members_updated']} members for committee {committee_id}")
            
        except Exception as e:
            logger.error(f"Error processing committee {committee_id}: {str(e)}", exc_info=True)
            results["status"] = "failed"
            results["error"] = str(e)
            
        return results

def get_committees_for_processing(recent_only: bool = True, days: int = 7, limit: int = 50) -> List[str]:
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
                # Get committees with missing members or oldest updated
                cur.execute("""
                    SELECT c.committee_id 
                    FROM committees c
                    LEFT JOIN committee_members cm ON c.id = cm.committee_id
                    GROUP BY c.committee_id, c.updated_at
                    HAVING COUNT(cm.id) = 0
                    ORDER BY c.updated_at ASC NULLS FIRST
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
            """, (COMMITTEE_MEMBERS_ENDPOINT, processed, status, error))
            conn.commit()

def main():
    parser = argparse.ArgumentParser(description='Process committee-member relationships')
    parser.add_argument('--committee', help='Process specific committee by ID')
    parser.add_argument('--all', action='store_true', help='Process all committees instead of just recent ones')
    parser.add_argument('--days', type=int, default=7, help='For recent mode, how many days back to consider')
    parser.add_argument('--limit', type=int, default=50, help='Maximum number of committees to process')
    parser.add_argument('--missing', action='store_true', help='Focus on committees with missing members')
    args = parser.parse_args()
    
    try:
        # Initialize API client
        api_client = APIClient(BASE_API_URL)
        
        # Initialize processor
        processor = CommitteeMemberProcessor(api_client)
        
        # Update status to in-progress
        update_sync_status('in_progress')
        
        # Determine which committees to process
        if args.committee:
            # Process single specified committee
            committees_to_process = [args.committee]
            logger.info(f"Processing members for committee: {args.committee}")
        else:
            # Get committees from database
            recent_only = not args.all and not args.missing
            committees_to_process = get_committees_for_processing(recent_only, args.days, args.limit)
            logger.info(f"Processing members for {len(committees_to_process)} committees")
        
        # Process each committee
        results = []
        processed_count = 0
        error_count = 0
        total_members_updated = 0
        
        for committee_id in committees_to_process:
            try:
                result = processor.process_committee(committee_id)
                results.append(result)
                
                if result['status'] == 'success':
                    processed_count += 1
                    total_members_updated += result['members_updated']
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing committee {committee_id}: {str(e)}", exc_info=True)
                error_count += 1
        
        # Clean up old files
        cleanup_old_files(os.path.join(os.path.dirname(__file__), 'raw', 'members'), 
                         pattern='*', days=RAW_DATA_RETENTION_DAYS)
        
        # Update sync status to success
        if error_count == 0:
            update_sync_status('success', processed_count)
        else:
            update_sync_status('completed_with_errors', processed_count, error_count)
        
        logger.info(f"Process completed. {processed_count} committees processed successfully with {total_members_updated} member relationships updated, {error_count} errors.")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        update_sync_status('failed', error=str(e))
        raise

if __name__ == "__main__":
    main()
```

#### committee_batch_processor.py

```python
#!/usr/bin/env python3
"""
Batch processor for committees - for processing large volumes of committee data
or filling in missing data. Supports batched operations and parallel processing.
"""

import os
import json
import argparse
import concurrent.futures
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Import utilities
from congressgov.utils.logging_config import setup_logging
from congressgov.utils.api import APIClient
from congressgov.utils.database import get_db_connection, with_db_transaction

# Import our other committee processors
from committee_detail_processor import CommitteeDetailProcessor
from committee_member_processor import CommitteeMemberProcessor

# Set up logging
logger = setup_logging(__name__)

# API configuration
BASE_API_URL = "https://api.congress.gov/v3"
MAX_WORKERS = 4  # Maximum number of concurrent workers for parallel processing

def get_all_committees(chamber: str = None, limit: int = None) -> List[Tuple[int, str]]:
    """Get all committees from the database, optionally filtered by chamber."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if chamber:
                query = """
                    SELECT id, committee_id 
                    FROM committees 
                    WHERE chamber = %s
                    ORDER BY updated_at ASC NULLS FIRST
                """
                params = [chamber]
            else:
                query = """
                    SELECT id, committee_id 
                    FROM committees 
                    ORDER BY updated_at ASC NULLS FIRST
                """
                params = []
                
            if limit:
                query += " LIMIT %s"
                params.append(limit)
                
            cur.execute(query, params)
            return [(row[0], row[1]) for row in cur.fetchall()]

def get_committees_missing_data(data_type: str, limit: int = None) -> List[Tuple[int, str]]:
    """Get committees missing specific data."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = ""
            
            if data_type == 'details':
                query = """
                    SELECT id, committee_id 
                    FROM committees 
                    WHERE website IS NULL
                       OR phone IS NULL
                       OR address IS NULL
                    ORDER BY updated_at ASC NULLS FIRST
                """
            elif data_type == 'members':
                query = """
                    SELECT c.id, c.committee_id 
                    FROM committees c
                    LEFT JOIN committee_members cm ON c.id = cm.committee_id
                    GROUP BY c.id, c.committee_id, c.updated_at
                    HAVING COUNT(cm.id) = 0
                    ORDER BY c.updated_at ASC NULLS FIRST
                """
            elif data_type == 'history':
                query = """
                    SELECT c.id, c.committee_id 
                    FROM committees c
                    LEFT JOIN committee_history ch ON c.id = ch.committee_id
                    GROUP BY c.id, c.committee_id, c.updated_at
                    HAVING COUNT(ch.id) = 0
                    ORDER BY c.updated_at ASC NULLS FIRST
                """
            else:
                raise ValueError(f"Unknown data type: {data_type}")
            
            if limit:
                query += f" LIMIT {limit}"
                
            cur.execute(query)
            return [(row[0], row[1]) for row in cur.fetchall()]

def process_committee_batch(committees: List[Tuple[int, str]], process_type: str, 
                           batch_size: int = 5, parallel: bool = False) -> Dict[str, int]:
    """
    Process a batch of committees, optionally in parallel.
    
    Args:
        committees: List of tuples (committee_db_id, committee_id)
        process_type: Type of processing ('details', 'members')
        batch_size: Number of committees to process in each batch
        parallel: Whether to process committees in parallel
        
    Returns:
        Dictionary with processing statistics
    """
    api_client = APIClient(BASE_API_URL)
    
    if process_type == 'details':
        processor = CommitteeDetailProcessor(api_client)
    elif process_type == 'members':
        processor = CommitteeMemberProcessor(api_client)
    else:
        raise ValueError(f"Unsupported process type: {process_type}")
    
    stats = {
        "total": len(committees),
        "processed": 0,
        "success": 0,
        "failed": 0
    }
    
    # Process committees in batches
    for i in range(0, len(committees), batch_size):
        batch = committees[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(committees)-1)//batch_size + 1} ({len(batch)} committees)")
        
        if parallel and len(batch) > 1:
            # Process batch in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(batch))) as executor:
                futures = {}
                for committee_db_id, committee_id in batch:
                    if process_type == 'details':
                        future = executor.submit(processor.process_committee, committee_id)
                    elif process_type == 'members':
                        future = executor.submit(processor.process_committee, committee_id)
                    
                    futures[future] = (committee_db_id, committee_id)
                
                for future in concurrent.futures.as_completed(futures):
                    committee_db_id, committee_id = futures[future]
                    try:
                        result = future.result()
                        stats["processed"] += 1
                        
                        if result["status"] == "success":
                            stats["success"] += 1
                            logger.info(f"Successfully processed committee {committee_id}")
                        else:
                            stats["failed"] += 1
                            logger.error(f"Failed to process committee {committee_id}: {result.get('error', 'Unknown error')}")
                            
                    except Exception as e:
                        stats["processed"] += 1
                        stats["failed"] += 1
                        logger.error(f"Error processing committee {committee_id}: {str(e)}")
        else:
            # Process batch sequentially
            for committee_db_id, committee_id in batch:
                try:
                    if process_type == 'details':
                        result = processor.process_committee(committee_id)
                    elif process_type == 'members':
                        result = processor.process_committee(committee_id)
                    
                    stats["processed"] += 1
                    
                    if result["status"] == "success":
                        stats["success"] += 1
                        logger.info(f"Successfully processed committee {committee_id}")
                    else:
                        stats["failed"] += 1
                        logger.error(f"Failed to process committee {committee_id}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    stats["processed"] += 1
                    stats["failed"] += 1
                    logger.error(f"Error processing committee {committee_id}: {str(e)}")
        
        logger.info(f"Batch complete. Progress: {stats['processed']}/{stats['total']} committees processed.")
    
    return stats

def main():
    parser = argparse.ArgumentParser(description='Batch processor for committees')
    parser.add_argument('--process-type', choices=['details', 'members'], 
                      default='details', help='Type of processing to perform')
    parser.add_argument('--chamber', choices=['house', 'senate', 'joint'], 
                      help='Process committees from a specific chamber')
    parser.add_argument('--missing', choices=['details', 'members', 'history'], 
                      help='Process committees missing specific data')
    parser.add_argument('--batch-size', type=int, default=5, help='Number of committees to process in each batch')
    parser.add_argument('--limit', type=int, help='Maximum number of committees to process')
    parser.add_argument('--parallel', action='store_true', help='Process committees in parallel')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without actually processing')
    args = parser.parse_args()
    
    try:
        committees_to_process = []
        
        if args.chamber:
            # Get committees from a specific chamber
            committees_to_process = get_all_committees(args.chamber, args.limit)
            logger.info(f"Found {len(committees_to_process)} committees in the {args.chamber}")
            
        elif args.missing:
            # Get committees missing specific data
            committees_to_process = get_committees_missing_data(args.missing, args.limit)
            logger.info(f"Found {len(committees_to_process)} committees missing {args.missing} data")
            
        else:
            # Get all committees
            committees_to_process = get_all_committees(limit=args.limit)
            logger.info(f"Found {len(committees_to_process)} committees")
        
        if not committees_to_process:
            logger.warning("No committees found to process based on the given criteria")
            return
        
        if args.dry_run:
            logger.info("Dry run - would process the following committees:")
            for committee_db_id, committee_id in committees_to_process:
                logger.info(f"  {committee_id} (ID: {committee_db_id})")
            return
        
        # Process committees in batches
        logger.info(f"Processing {len(committees_to_process)} committees in batches of {args.batch_size}")
        logger.info(f"Process type: {args.process_type}")
        logger.info(f"Parallel processing: {'Enabled' if args.parallel else 'Disabled'}")
        
        stats = process_committee_batch(committees_to_process, args.process_type, args.batch_size, args.parallel)
        
        logger.info("Batch processing complete")
        logger.info(f"Total committees: {stats['total']}")
        logger.info(f"Successfully processed: {stats['success']}")
        logger.info(f"Failed: {stats['failed']}")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
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