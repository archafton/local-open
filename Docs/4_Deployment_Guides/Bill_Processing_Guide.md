# Project Tacitus: Bill Processing System Guide

This document outlines the bill processing system for Project Tacitus, including the purpose of each script, how to use them, and common workflows. The system supports both modern and historical bills.

## Overview

The bill processing system consists of several specialized scripts that work together to fetch, process, and enrich legislative data from Congress.gov. The system is designed to be efficient, modular, and maintainable, with special handling for historical bills.

### Key Components

1. **Core Utilities**
   - `congressgov/utils/bill_utils.py` - Common bill-related utility functions
   - `congressgov/utils/tag_utils.py` - Hierarchical tag management utilities
   - `congressgov/utils/api.py` - API interaction with retry mechanisms
   - `congressgov/utils/database.py` - Database connection and transaction handling
   - `congressgov/utils/file_storage.py` - File operations and management
   - `congressgov/utils/logging_config.py` - Standardized logging

2. **Bill Processing Scripts**
   - `bill_fetch_core.py` - Primary script for fetching basic bill data
   - `bill_detail_processor.py` - Fetches and processes detailed bill information
   - `bill_batch_processor.py` - Processes bills in batches with parallel processing support
   - `bill_validation.py` - Validates bill data and identifies gaps

## Usage Instructions

### Initial Bill Data Fetching

Use `bill_fetch_core.py` to fetch basic bill data from Congress.gov.

```bash
# Fetch all bills incrementally (only new/updated since last run)
python bill_fetch_core.py

# Force a complete fetch of all bills
python bill_fetch_core.py --force-full

# Fetch bills from a specific date range
python bill_fetch_core.py --start-date 2023-01-01 --end-date 2023-03-01

# Look back further than the default 7 days
python bill_fetch_core.py --days 30

# Fetch bills from a specific Congress
python bill_fetch_core.py --congress 117

# Enable specialized processing for historical bills
python bill_fetch_core.py --historical
```

### Fetching Bill Details

Use `bill_detail_processor.py` to fetch detailed information for bills.

```bash
# Process details for recently updated bills
python bill_detail_processor.py

# Process a specific bill by number and congress
python bill_detail_processor.py --bill HR1234 --congress 117

# Process all bills that need details instead of just recent ones
python bill_detail_processor.py --all

# Limit the number of bills processed
python bill_detail_processor.py --limit 50

# Process only recently updated bills
python bill_detail_processor.py --recent
```

### Batch Processing

Use `bill_batch_processor.py` for more advanced batch processing operations.

```bash
# Process all bills from a specific Congress
python bill_batch_processor.py --congress 117

# Process bills with a specific status
python bill_batch_processor.py --status "In Committee"

# Process bills missing text versions
python bill_batch_processor.py --missing text_versions

# Process bills missing any type of data
python bill_batch_processor.py --missing all

# Process in larger batches with parallel execution
python bill_batch_processor.py --batch-size 20 --parallel

# Validate and process bills with missing data
python bill_batch_processor.py --validate

# Do a dry run to see what would be processed
python bill_batch_processor.py --validate --dry-run

# Process historical bills (6th-42nd Congresses)
python bill_batch_processor.py --historical

# Process bills excluding historical bills
python bill_batch_processor.py --exclude-historical
```

### Validating Bill Data

Use `bill_validation.py` to check for bills with missing data.

```bash
# Run validation and generate a text report
python bill_validation.py

# Generate a JSON report
python bill_validation.py --format json

# Specify output file location
python bill_validation.py --output bill_validation_report.txt

# Include historical bills in validation reports
python bill_validation.py --include-historical
```

## Common Workflows

### Complete Initial Data Load

For a complete initial data load, run these commands in sequence:

```bash
# 1. Fetch all basic bill data
python bill_fetch_core.py --force-full

# 2. Process details for all bills
python bill_detail_processor.py --all

# 3. Validate and fix any missing data
python bill_validation.py
python bill_batch_processor.py --validate
```

### Regular Daily Updates

For regular daily updates, run:

```bash
# 1. Fetch updated bill data (incremental)
python bill_fetch_core.py

# 2. Process details for recently updated bills
python bill_detail_processor.py

# 3. Run validation to check for any issues
python bill_validation.py
```

### Filling in Missing Data

To fill in missing data:

```bash
# 1. Run validation to identify issues
python bill_validation.py

# 2. Process bills missing text versions
python bill_batch_processor.py --missing text_versions

# 3. Process bills missing actions
python bill_batch_processor.py --missing actions

# 4. Process bills missing subjects
python bill_batch_processor.py --missing subjects
```

### Processing Historical Data

To process bills from previous Congresses:

```bash
# Process all bills from the 116th Congress
python bill_batch_processor.py --congress 116 --batch-size 50

# Process bills with "Became Law" status from any Congress
python bill_batch_processor.py --status "Became Law"

# Process all historical bills (6th-42nd Congresses)
python bill_batch_processor.py --historical --batch-size 20

# Process historical bills with specialized handling
python bill_batch_processor.py --congress 20 --historical
```

## Important Notes

1. **Hierarchical Tag System**: The system uses a hierarchical tag structure for categorizing bills. Policy areas are automatically converted to tags.

2. **Incremental Processing**: By default, most scripts use incremental processing to avoid redundant work. Use the `--force-full` or `--all` flags when you need to process all bills.

3. **Parallel Processing**: The batch processor supports parallel execution with the `--parallel` flag, which can significantly speed up processing at the cost of more API requests.

4. **Rate Limiting**: Be mindful of API rate limits when using parallel processing or processing large batches.

5. **File Storage**: All scripts save raw API responses to JSON files for debugging and audit purposes. Old files are automatically cleaned up after 30 days.

6. **Transaction Safety**: All database operations use transactions to ensure data integrity even if errors occur during processing.

7. **Historical Bills Structure**: The Congress.gov API returns different data structures for older bills (particularly those from the 6th to 42nd Congresses, 1799-1873):
   - For newer bills, the API returns a single bill object in the `bill` field
   - For older bills, the API returns an array of bill objects in the `bill` field, often containing multiple entries for the same bill number with different introduction dates
   - The system automatically handles this difference by selecting the most recently updated entry when multiple entries are found
   - Informational messages are logged when multiple entries are detected

8. **Historical Bills Limitations**: As noted in the Congress.gov API documentation, older bills (1799-1873) have limited metadata. They have text, titles, and some actions, but do not have sponsors, cosponsors, summaries, amendments, committees, and related bill information.

9. **Historical Bills Processing**: The system includes specialized handling for historical bills:
   - The `--historical` flag enables specialized processing for bills from the 6th-42nd Congresses
   - Expected limitations (missing sponsors, cosponsors, summaries) are logged as warnings rather than errors
   - Validation reports distinguish between issues in modern bills and expected limitations in historical bills
   - The `--exclude-historical` flag can be used to skip historical bills when processing

## Troubleshooting

If you encounter issues:

1. Check the log files in the script's directory
2. Look for entries in the `api_sync_status` table
3. Try processing specific bills with the `--bill` flag
4. Run with a small `--limit` value to test functionality
5. Run `bill_validation.py` to identify potential data issues

### Historical Bills Issues

When working with historical bills (particularly from Congresses before the 43rd):

1. **Multiple Bill Entries**: If you see log messages about "Multiple bill entries found," this is normal for older bills. The system will automatically use the most recently updated entry.

2. **Missing Metadata**: Older bills have limited metadata. If you see warnings about missing sponsors, cosponsors, or other fields, this is expected for bills from 1799-1873.

3. **Different Data Structures**: If you encounter unexpected errors with older bills, check the logs for details. The system is designed to handle the different API response structures, but edge cases may exist.

4. **Bill Numbers**: Bills from 1799 (6th Congress) to 1817 (14th Congress) were not numbered and may have special handling in the API.

5. **Case Sensitivity**: Historical bills may have inconsistent case in bill numbers. The system now handles this with case-insensitive comparisons.

6. **Expected Errors**: When using the `--historical` flag, certain errors related to missing metadata are expected and will be logged as warnings rather than errors.

## Advanced Configuration

These scripts support additional configuration via environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `CONGRESSGOV_API_KEY` - API key for Congress.gov
- `LOG_LEVEL` - Set to DEBUG for more verbose logging

Set these in your `.env` file or in your environment before running the scripts.

## Using the Parameterized Bill Fetch

A special parameterized version is available for fetching historical bill data:

```bash
# Fetch bills from a specific date range
python params_bill_fetch.py --start-date 2021-01-01 --end-date 2021-12-31

# Fetch bills from the last N days
python params_bill_fetch.py --days 90
```

This is particularly useful for initial population of the database or for catching up after extended periods without updates.

## Historical Bills Processing Guide

For more detailed information about handling historical bills, please refer to the [Historical Bills Processing Guide](../5_Working_Docs/Historical_Bills_Processing_Guide.md), which provides in-depth explanations of:

- API response structure differences between modern and historical bills
- Limitations of historical bill metadata
- Required adjustments for processing historical bills
- Schema considerations for historical bills
- Testing and validation approaches
- Best practices for historical bill processing
