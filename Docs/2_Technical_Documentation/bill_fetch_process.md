# Bill Fetch Process Documentation

## Overview
The bill fetch process implements a file-first approach to fetching, storing, and processing bill data from the Congress.gov API. This document outlines the components, their roles, and how they work together to provide bill information to the application.

## Directory Structure
```
backend/src/python/congressgov/bill_fetch/
├── bill_fetch.py          # Fetch List of Bills
├── bill_storage.py        # Core storage functionality
├── bill_detail_fetch.py   # Fetches and processes bill details
├── bill_enrichment.py     # Enriches bills with additional data
└── raw/
    └── bill/
        └── {congress}/
            └── {billType}/
                └── {billNumber}/
                    ├── details.json   # Basic bill information
                    ├── text.json      # Text versions
                    ├── summary.json   # Bill summaries
                    ├── actions.json   # Bill actions
                    └── *.json.bak     # Timestamped backups
```

## Core Components

### 1. BillStorage (bill_storage.py)
The central component managing file-based storage of bill data.

Key Features:
- Manages hierarchical directory structure
- Handles file operations (save/load)
- Creates automatic backups of existing files
- Provides consistent interface for other components

Key Methods:
- `ensure_bill_directory()`: Creates necessary directory structure
- `save_bill_data()`: Saves data with automatic backup
- `load_bill_data()`: Retrieves stored data
- `list_bill_files()`: Lists available data files
- `get_bill_path()`: Generates standardized file paths

Backup System:
- Automatic backup creation before file updates
- Timestamp-based backup naming (YYYYMMDD_HHMMSS)
- Separate backup files for each data type
- Retention of previous versions for recovery

### 2. Bill Detail Fetch (bill_detail_fetch.py)
Primary component for fetching bill details from Congress.gov API.

Responsibilities:
- Fetches basic bill information
- Retrieves text versions
- Processes and normalizes dates
- Updates database with processed data

Key Features:
- Handles null dates in text versions
- Processes multiple versions on same date
- Normalizes format display names (HTML/PDF/XML)
- Maps text versions to actions

### 3. Bill Enrichment (bill_enrichment.py)
Enhances bill data with additional information.

Responsibilities:
- Fetches and processes related bills
- Handles bill actions
- Manages cosponsors and subjects
- Updates database with enriched data

Key Features:
- Maintains consistency with file storage
- Processes multiple data types
- Handles relationship mappings
- Updates database atomically

## Data Flow

1. Initial Fetch:
   - `bill_detail_fetch.py` retrieves bill data from Congress.gov
   - Data is immediately saved to appropriate JSON files
   - File structure follows congress/type/number hierarchy
   - Automatic backups created for existing files

2. Storage:
   - `bill_storage.py` manages all file operations
   - Creates timestamped backups before updates
   - Maintains consistent directory structure
   - Handles file naming and organization
   - Provides error handling and logging

3. Processing:
   - Raw JSON responses stored in hierarchical structure
   - Data processed for database storage
   - Special cases handled (null dates, multiple versions)
   - Format types normalized for display

4. Database Update:
   - Processed data stored in PostgreSQL
   - Maintains relationships between entities
   - Handles conflicts and updates
   - Ensures data consistency

## Error Handling and Recovery

1. File Operations:
   - Automatic backup creation before any file update
   - Timestamped backups for version tracking
   - Directory existence verification
   - Write permission checks
   - Exception handling for I/O operations
   - Detailed error logging

2. Data Validation:
   - JSON format verification
   - Required field checks
   - Data type validation
   - Null value handling

3. Recovery Procedures:
   - Backup files available for restoration
   - Timestamp-based version selection
   - Separate backups for each data type
   - Logging of all backup operations

4. Logging System:
   - Detailed operation logging
   - Error tracking with stack traces
   - Success/failure status recording
   - Timestamp and context information
   - Separate log files for different components

## Special Cases Handling

1. Text Versions:
   - Null dates handled using introduced_date
   - Multiple versions on same date sorted by type importance
   - Format types normalized (HTML/PDF/XML)
   - Version types properly mapped to actions

2. File Management:
   - Automatic backup creation
   - Timestamp-based versioning
   - Consistent naming conventions
   - Error handling and logging

3. Data Processing:
   - Date normalization
   - Format type mapping
   - Action type correlation
   - Version type prioritization

## Frontend Integration

The processed data is served through the API and displayed in several key areas:

1. Header Section:
   - Shows initial and latest versions
   - Displays format links (HTML/PDF/XML)
   - Indicates version types and dates

2. Timeline Section:
   - Aligns text versions with actions
   - Shows version progression
   - Provides access to all formats

## Maintenance and Updates

1. Regular Tasks:
   - Check for new bills
   - Update existing bills
   - Verify file integrity
   - Clean up old backups
   - Monitor storage usage

2. Error Recovery:
   - File backup restoration
   - Database rollback
   - API retry logic
   - Data validation
   - Log analysis

3. Storage Management:
   - Backup rotation
   - Space monitoring
   - File cleanup
   - Integrity checks

## Future Considerations

1. Storage Optimization:
   - S3 integration readiness
   - Cleanup strategies
   - Version retention policies
   - Storage monitoring
   - Compression options

2. Performance:
   - Caching strategies
   - Batch processing
   - Parallel fetching
   - Resource optimization
   - Response time monitoring

3. Scalability:
   - Cloud storage migration
   - Load distribution
   - Rate limit management
   - Resource allocation
   - Horizontal scaling

4. Monitoring and Alerting:
   - Storage usage alerts
   - Error rate monitoring
   - Performance metrics
   - API health checks
   - System status dashboards
