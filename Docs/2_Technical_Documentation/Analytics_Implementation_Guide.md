# Analytics Implementation Guide

## 1. Introduction

### Purpose
This guide serves as a comprehensive reference for implementing analytics features in Project Tacitus. It provides detailed information about current capabilities, required schema changes, and guidelines for adding new analytics use cases.

### How to Use This Guide
- For implementing existing use cases: See Section 2
- For extending the schema: See Section 3
- For adding external data: See Section 4
- For creating new analytics: See Section 6
- For working with Claude: See Section 7

### Current System Overview
The system currently maintains:
- Bill data (status, congress, sponsors, etc.)
- Member data (representatives, roles, terms)
- Voting records
- Committee information
- Tag system for categorization
- Action history for bills

## 2. Current Analytics Capabilities

### 2.1 Existing Schema Overview

#### Core Tables
```sql
bills:
  - id, bill_number, bill_title, sponsor_id
  - introduced_date, status, congress
  - latest_action, latest_action_date
  - normalized_status, tags

members:
  - id, bioguide_id, full_name
  - party, state, district, chamber
  - leadership_role, current_member
  - total_votes, missed_votes

votes:
  - bill_id, member_id
  - vote, vote_date, vote_type

committees:
  - id, committee_name, chamber

bill_actions:
  - bill_number, action_date
  - action_text, action_type

tags:
  - id, type_id, name
  - normalized_name, parent_id
```

#### Currently Available Metrics
1. Legislative Activity
   - Bills per congress
   - Bills by status
   - Introduction to passage time
   - Sponsor activity levels

2. Representative Engagement
   - Voting participation
   - Bill sponsorship
   - Committee membership
   - Leadership positions

3. Policy Analysis
   - Topic distribution
   - Committee workload
   - Tag frequency
   - Status progression

### 2.2 Example Queries

#### Bills by Congress with Status
```sql
SELECT 
  congress,
  status,
  COUNT(*) as bill_count
FROM bills
GROUP BY congress, status
ORDER BY congress DESC, bill_count DESC;
```

#### Representative Activity Score
```sql
SELECT 
  m.full_name,
  COUNT(DISTINCT b.id) as sponsored_bills,
  COUNT(DISTINCT bc.bill_number) as cosponsored_bills,
  m.total_votes - m.missed_votes as votes_participated
FROM members m
LEFT JOIN bills b ON m.bioguide_id = b.sponsor_id
LEFT JOIN bill_cosponsors bc ON m.bioguide_id = bc.cosponsor_id
WHERE m.current_member = true
GROUP BY m.id, m.full_name
ORDER BY sponsored_bills DESC;
```

#### Policy Area Distribution
```sql
SELECT 
  t.name as policy_area,
  COUNT(*) as bill_count
FROM bills b
JOIN bill_tags bt ON b.id = bt.bill_id
JOIN tags t ON bt.tag_id = t.id
JOIN tag_types tt ON t.type_id = tt.id
WHERE tt.name = 'Policy Area'
GROUP BY t.name
ORDER BY bill_count DESC;
```

## 3. Schema Extensions

### 3.1 Temporal Tracking

```sql
-- Bill stage durations
CREATE TABLE bill_stage_durations (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills(id),
    stage_name VARCHAR(50) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    duration_days INTEGER,
    stage_order INTEGER,
    UNIQUE(bill_id, stage_name)
);

-- Committee processing metrics
CREATE TABLE committee_processing_metrics (
    id SERIAL PRIMARY KEY,
    committee_id INTEGER REFERENCES committees(id),
    bill_id INTEGER REFERENCES bills(id),
    referral_date TIMESTAMP WITH TIME ZONE,
    first_hearing_date TIMESTAMP WITH TIME ZONE,
    report_date TIMESTAMP WITH TIME ZONE,
    processing_days INTEGER,
    UNIQUE(committee_id, bill_id)
);
```

### 3.2 Collaboration Metrics

```sql
-- Vote alignment tracking
CREATE TABLE member_vote_alignment (
    id SERIAL PRIMARY KEY,
    member_id_1 INTEGER REFERENCES members(id),
    member_id_2 INTEGER REFERENCES members(id),
    congress INTEGER NOT NULL,
    total_shared_votes INTEGER DEFAULT 0,
    aligned_votes INTEGER DEFAULT 0,
    alignment_score DECIMAL(5,2),
    UNIQUE(member_id_1, member_id_2, congress)
);

-- Collaboration strength
CREATE TABLE member_collaboration (
    id SERIAL PRIMARY KEY,
    member_id_1 INTEGER REFERENCES members(id),
    member_id_2 INTEGER REFERENCES members(id),
    congress INTEGER NOT NULL,
    cosponsored_bills INTEGER DEFAULT 0,
    shared_committees INTEGER DEFAULT 0,
    collaboration_score DECIMAL(5,2),
    UNIQUE(member_id_1, member_id_2, congress)
);
```

### 3.3 Public Opinion Integration

```sql
-- Poll tracking
CREATE TABLE opinion_polls (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    poll_date DATE NOT NULL,
    topic VARCHAR(255) NOT NULL,
    sample_size INTEGER,
    margin_error DECIMAL(4,2),
    methodology TEXT,
    results JSONB NOT NULL
);

-- Bill sentiment
CREATE TABLE bill_public_sentiment (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills(id),
    source_type VARCHAR(50) NOT NULL,
    capture_date TIMESTAMP WITH TIME ZONE,
    sentiment_score DECIMAL(4,2),
    volume INTEGER,
    key_topics JSONB
);
```

### 3.4 Campaign Finance Integration

```sql
-- Campaign contributions
CREATE TABLE campaign_contributions (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    contributor_name VARCHAR(255),
    contributor_type VARCHAR(50),
    industry_code VARCHAR(10),
    amount DECIMAL(12,2),
    contribution_date DATE,
    election_cycle INTEGER
);

-- Industry aggregates
CREATE TABLE industry_contribution_totals (
    id SERIAL PRIMARY KEY,
    industry_code VARCHAR(10),
    industry_name VARCHAR(255),
    election_cycle INTEGER,
    total_amount DECIMAL(15,2),
    recipient_count INTEGER,
    UNIQUE(industry_code, election_cycle)
);
```

## 4. External Data Integration

### 4.1 Required Data Sources

1. Public Opinion Data
   - Pew Research Center
   - Gallup Analytics
   - Social media sentiment APIs
   - News media APIs

2. Campaign Finance Data
   - OpenFEC API
   - OpenSecrets API (if available)
   - USASpending.gov API

3. Additional Legislative Data
   - Congress.gov API
   - ProPublica Congress API
   - GovInfo API

### 4.2 API Integration Specifications

#### OpenFEC Integration
```python
API_BASE = "https://api.open.fec.gov/v1"
ENDPOINTS = {
    "candidates": "/candidates",
    "committees": "/committees",
    "contributions": "/schedules/schedule_a",
    "disbursements": "/schedules/schedule_b"
}

REQUIRED_FIELDS = {
    "candidates": [
        "candidate_id",
        "name",
        "party",
        "election_years",
        "office"
    ],
    "contributions": [
        "contributor_name",
        "contribution_receipt_amount",
        "contribution_receipt_date",
        "contributor_employer",
        "contributor_occupation"
    ]
}
```

#### Social Media Sentiment
```python
PLATFORMS = {
    "twitter": {
        "search_endpoint": "/2/tweets/search/recent",
        "fields": ["created_at", "text", "public_metrics"]
    },
    "reddit": {
        "search_endpoint": "/search/submission",
        "fields": ["created_utc", "title", "selftext", "score"]
    }
}

SENTIMENT_METRICS = [
    "positive_score",
    "negative_score",
    "neutral_score",
    "compound_score"
]
```

### 4.3 Data Transformation Requirements

1. Standardization Rules
   - Dates to UTC
   - Currency to decimal(12,2)
   - Names to uppercase
   - Party codes normalized
   - State codes to 2-letter format

2. Required Mappings
   - Industry codes to categories
   - State names to codes
   - Party abbreviations to full names
   - Chamber codes to full names

## 5. Implementation Guidelines

### 5.1 Query Optimization Patterns

1. Use Materialized Views for Common Aggregates
```sql
CREATE MATERIALIZED VIEW member_activity_scores AS
SELECT 
    m.id,
    m.full_name,
    COUNT(DISTINCT b.id) as sponsored_bills,
    COUNT(DISTINCT bc.bill_number) as cosponsored_bills,
    COALESCE(m.total_votes - m.missed_votes, 0) as votes_participated,
    (
        COUNT(DISTINCT b.id) * 3 + 
        COUNT(DISTINCT bc.bill_number) + 
        COALESCE(m.total_votes - m.missed_votes, 0)
    ) as activity_score
FROM members m
LEFT JOIN bills b ON m.bioguide_id = b.sponsor_id
LEFT JOIN bill_cosponsors bc ON m.bioguide_id = bc.cosponsor_id
GROUP BY m.id, m.full_name;
```

2. Index Strategy
```sql
-- For temporal queries
CREATE INDEX idx_bills_introduced_date ON bills(introduced_date);
CREATE INDEX idx_bill_actions_date ON bill_actions(action_date);

-- For member activity
CREATE INDEX idx_bills_sponsor_congress ON bills(sponsor_id, congress);
CREATE INDEX idx_cosponsors_congress ON bill_cosponsors(cosponsor_id);

-- For tag analysis
CREATE INDEX idx_bill_tags_tag_type ON bill_tags(tag_id, bill_id);
```

3. Partitioning Strategy
```sql
-- Partition bills by congress
CREATE TABLE bills (
    id SERIAL,
    bill_number VARCHAR(50),
    congress INTEGER,
    -- other columns
) PARTITION BY RANGE (congress);

-- Partition votes by date
CREATE TABLE votes (
    id SERIAL,
    vote_date DATE,
    -- other columns
) PARTITION BY RANGE (vote_date);
```

### 5.2 Caching Strategy

1. Cache Levels
```python
CACHE_CONFIG = {
    "L1": {
        "type": "memory",
        "ttl": 300,  # 5 minutes
        "max_size": "1GB",
        "items": [
            "current_member_list",
            "active_bills",
            "committee_assignments"
        ]
    },
    "L2": {
        "type": "redis",
        "ttl": 3600,  # 1 hour
        "items": [
            "member_activity_scores",
            "bill_status_counts",
            "tag_distributions"
        ]
    },
    "L3": {
        "type": "materialized_view",
        "refresh_interval": "1 day",
        "items": [
            "historical_trends",
            "collaboration_networks",
            "voting_patterns"
        ]
    }
}
```

2. Invalidation Rules
```python
INVALIDATION_RULES = {
    "member_activity_scores": [
        "new_bill_sponsored",
        "new_cosponsor_added",
        "vote_recorded"
    ],
    "bill_status_counts": [
        "bill_status_changed",
        "new_bill_added"
    ],
    "tag_distributions": [
        "tag_added",
        "tag_removed",
        "new_bill_tagged"
    ]
}
```

## 6. Adding New Analytics Use Cases

### 6.1 Use Case Template

```markdown
# Analytics Use Case Specification

## Overview
- Name: [Use Case Name]
- Category: [Activity/Policy/Representative/etc.]
- Priority: [High/Medium/Low]

## Data Requirements
- Primary Tables: [List required tables]
- External Sources: [List external data needed]
- New Schema: [Any new tables/columns needed]

## Implementation Details
- Query Patterns: [Basic query structure]
- Performance Considerations: [Indexing/caching needs]
- Update Frequency: [Real-time/Daily/Weekly]

## Visualization
- Chart Type: [Recommended visualization]
- Interactivity: [Required interactive features]
- Filters: [Available filter options]

## Testing Requirements
- Data Validation: [Validation rules]
- Performance Metrics: [Expected response times]
- Edge Cases: [Special conditions to test]
```

### 6.2 Implementation Checklist

1. Data Preparation
   - [ ] Verify required tables exist
   - [ ] Check data completeness
   - [ ] Validate data quality
   - [ ] Create necessary indexes

2. Schema Updates
   - [ ] Design new tables/columns
   - [ ] Write migration scripts
   - [ ] Update documentation
   - [ ] Create backup plan

3. Query Development
   - [ ] Write base queries
   - [ ] Optimize performance
   - [ ] Add error handling
   - [ ] Implement caching

4. Testing
   - [ ] Unit tests
   - [ ] Performance tests
   - [ ] Edge case validation
   - [ ] Integration tests

## 7. Working with Claude

### 7.1 Context Requirements

When working with Claude on analytics tasks, provide:

1. Use Case Details
   ```markdown
   - Primary goal of the analysis
   - Required metrics and dimensions
   - Expected output format
   - Performance requirements
   ```

2. Data Context
   ```markdown
   - Relevant tables and relationships
   - Sample data if available
   - Known data quality issues
   - Update frequency
   ```

3. Technical Constraints
   ```markdown
   - Performance requirements
   - Resource limitations
   - Security considerations
   - Integration requirements
   ```

### 7.2 Command Patterns

1. Schema Analysis
   ```sql
   -- Get table structure
   \d table_name

   -- Check indexes
   \di table_name

   -- View dependencies
   SELECT dependent_ns.nspname as dependent_schema,
          dependent_view.relname as dependent_view
   FROM pg_depend 
   JOIN pg_rewrite ON pg_depend.objid = pg_rewrite.oid 
   JOIN pg_class as dependent_view ON pg_rewrite.ev_class = dependent_view.oid 
   JOIN pg_class as source_table ON pg_depend.refobjid = source_table.oid 
   JOIN pg_namespace dependent_ns ON dependent_view.relnamespace = dependent_ns.oid 
   JOIN pg_namespace source_ns ON source_table.relnamespace = source_ns.oid 
   WHERE source_table.relname = 'table_name';
   ```

2. Data Validation
   ```sql
   -- Check for nulls
   SELECT column_name, COUNT(*) as null_count
   FROM table_name
   WHERE column_name IS NULL
   GROUP BY column_name;

   -- Check value distributions
   SELECT column_name, COUNT(*) as value_count
   FROM table_name
   GROUP BY column_name
   ORDER BY value_count DESC;
   ```

3. Performance Analysis
   ```sql
   -- Query timing
   EXPLAIN ANALYZE query;

   -- Index usage
   SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
   FROM pg_stat_user_indexes;
   ```

### 7.3 Example Workflows

1. Creating New Analytics
   ```markdown
   1. Define requirements using template
   2. Validate data availability
   3. Design schema changes
   4. Implement queries
   5. Add caching layer
   6. Create visualization
   ```

2. Optimizing Existing Analytics
   ```markdown
   1. Identify performance issues
   2. Analyze query patterns
   3. Review indexing strategy
   4. Implement caching
   5. Validate improvements
   ```

3. Adding External Data
   ```markdown
   1. Define integration requirements
   2. Create schema extensions
   3. Implement ETL process
   4. Add data validation
   5. Update analytics
   ```

### 7.4 Troubleshooting Guide

1. Performance Issues
   ```markdown
   - Check query execution plan
   - Verify index usage
   - Review data distribution
   - Analyze cache hit rates
   ```

2. Data Quality Issues
   ```markdown
   - Validate data completeness
   - Check for anomalies
   - Verify transformation logic
   - Review update processes
   ```

3. Integration Problems
   ```markdown
   - Check API connectivity
   - Verify authentication
   - Review rate limits
   - Validate data mapping
   ```

## 8. Conclusion

This guide serves as a living document for implementing analytics features in Project Tacitus. It provides:

- Current system capabilities and limitations
- Required schema changes for new features
- Integration patterns for external data
- Best practices for implementation
- Guidelines for working with Claude

When implementing new analytics features:
1. Review relevant sections of this guide
2. Follow the templates and checklists provided
3. Document any new patterns or solutions discovered
4. Update this guide with new learnings

For questions or clarifications, refer to the project maintainers or raise an issue in the repository.
