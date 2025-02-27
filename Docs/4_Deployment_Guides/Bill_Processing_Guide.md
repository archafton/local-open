# Project Tacitus: Bill Processing System Guide

This document outlines the new bill processing system for Project Tacitus, including the purpose of each script, how to use them, and common workflows.

## Overview

The bill processing system consists of several specialized scripts that work together to fetch, process, and enrich legislative data from Congress.gov. The system is designed to be efficient, modular, and maintainable.

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
python bill_fetch_core.py --start-date 2023-01-01 --end-date 2023-12-31

# Look back further than the default 7 days
python bill_fetch_core.py --days 30
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
```

## Important Notes

1. **Hierarchical Tag System**: The system uses a hierarchical tag structure for categorizing bills. Policy areas are automatically converted to tags.

2. **Incremental Processing**: By default, most scripts use incremental processing to avoid redundant work. Use the `--force-full` or `--all` flags when you need to process all bills.

3. **Parallel Processing**: The batch processor supports parallel execution with the `--parallel` flag, which can significantly speed up processing at the cost of more API requests.

4. **Rate Limiting**: Be mindful of API rate limits when using parallel processing or processing large batches.

5. **File Storage**: All scripts save raw API responses to JSON files for debugging and audit purposes. Old files are automatically cleaned up after 30 days.

6. **Transaction Safety**: All database operations use transactions to ensure data integrity even if errors occur during processing.

## Troubleshooting

If you encounter issues:

1. Check the log files in the script's directory
2. Look for entries in the `api_sync_status` table
3. Try processing specific bills with the `--bill` flag
4. Run with a small `--limit` value to test functionality
5. Run `bill_validation.py` to identify potential data issues

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