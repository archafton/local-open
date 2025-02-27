# Project Tacitus: Member Processing System Guide

This document outlines the new member processing system for Project Tacitus, including the purpose of each script, how to use them, and common workflows.

## Overview

The member processing system consists of several specialized scripts that work together to fetch, process, and enrich member data from Congress.gov. The system is designed to be efficient, modular, and maintainable.

### Key Components

1. **Core Utilities**
   - `congressgov/utils/member_utils.py` - Common member-related utility functions
   - `congressgov/utils/api.py` - API interaction with retry mechanisms
   - `congressgov/utils/database.py` - Database connection and transaction handling
   - `congressgov/utils/file_storage.py` - File operations and management
   - `congressgov/utils/logging_config.py` - Standardized logging

2. **Member Processing Scripts**
   - `member_fetch_core.py` - Primary script for fetching basic member data
   - `member_detail_processor.py` - Fetches and processes detailed member information
   - `member_enrichment.py` - Associates members with their sponsored and cosponsored legislation
   - `member_batch_processor.py` - Processes members in batches with parallel processing support
   - `member_bio.py` - Scrapes biographical information from bioguide.congress.gov

## Usage Instructions

### Initial Member Data Fetching

Use `member_fetch_core.py` to fetch basic member data from Congress.gov.

```bash
# Fetch all members incrementally (only new/updated since last run)
python member_fetch_core.py

# Force a complete fetch of all members
python member_fetch_core.py --force-full

# Fetch members updated in a specific date range
python member_fetch_core.py --start-date 2023-01-01 --end-date 2023-12-31

# Fetch only current members
python member_fetch_core.py --current-only
```

### Fetching Member Details

Use `member_detail_processor.py` to fetch detailed information for members.

```bash
# Process details for recently updated members
python member_detail_processor.py

# Process a specific member by bioguide ID
python member_detail_processor.py --member A000055

# Process all members instead of just recent ones
python member_detail_processor.py --all

# Focus on members with missing details
python member_detail_processor.py --missing

# Limit the number of members processed
python member_detail_processor.py --limit 50
```

### Enriching Member Data

Use `member_enrichment.py` to associate members with bills they've sponsored or cosponsored.

```bash
# Enrich recently updated members
python member_enrichment.py

# Enrich a specific member
python member_enrichment.py --member A000055

# Enrich all current members
python member_enrichment.py --all

# Specify how many days back to look for changes
python member_enrichment.py --days 14

# Limit the number of members processed
python member_enrichment.py --limit 50

# Refresh the bill cache before processing
python member_enrichment.py --refresh
```

### Fetching Member Biographies

Use `member_bio.py` to scrape biographical information from bioguide.congress.gov.

```bash
# Process bios for recently updated members
python member_bio.py

# Process bio for a specific member
python member_bio.py --member A000055

# Process bios for all members
python member_bio.py --all

# Focus on members with missing bios
python member_bio.py --missing

# Limit the number of members processed
python member_bio.py --limit 20

# Specify how many days back to look for changes
python member_bio.py --days 30
```

### Batch Processing

Use `member_batch_processor.py` for more advanced batch processing operations.

```bash
# Process details for all current members in batches
python member_batch_processor.py --process-type details

# Process enrichment for Senate members with parallel processing
python member_batch_processor.py --process-type enrichment --chamber senate --parallel

# Process members missing leadership information
python member_batch_processor.py --process-type details --missing leadership

# Do a dry run to see what would be processed
python member_batch_processor.py --process-type details --missing bio --dry-run

# Process in larger batches with parallel execution
python member_batch_processor.py --process-type enrichment --batch-size 20 --parallel
```

## Common Workflows

### Complete Initial Data Load

For a complete initial data load, run these commands in sequence:

```bash
# 1. Fetch all basic member data
python member_fetch_core.py --force-full

# 2. Fetch detailed information for all members
python member_detail_processor.py --all

# 3. Enrich all current members
python member_enrichment.py --all

# 4. Fetch biographical information (limited batches due to scraping)
python member_bio.py --all --limit 50
```

### Regular Daily Updates

For regular daily updates, run:

```bash
# 1. Fetch updated member data (incremental)
python member_fetch_core.py

# 2. Process details for recently updated members
python member_detail_processor.py

# 3. Enrich recently updated members
python member_enrichment.py

# 4. Process bios for recently updated members (smaller batch)
python member_bio.py --limit 20
```

### Filling in Missing Data

To fill in missing data:

```bash
# 1. Process members with missing details
python member_batch_processor.py --process-type details --missing details

# 2. Process members missing leadership information
python member_batch_processor.py --process-type details --missing leadership

# 3. Process members missing legislation associations
python member_batch_processor.py --process-type enrichment --missing legislation

# 4. Process members missing biographical information
python member_bio.py --missing --limit 20
```

## Important Notes

1. **Bill Processing Priority**: Only `bill_fetch_*.py` scripts should add bills to the database. The `member_enrichment.py` script has been modified to only associate members with bills that already exist in the database.

2. **Incremental Processing**: By default, most scripts use incremental processing to avoid redundant work. Use the `--force-full` or `--all` flags when you need to process all members.

3. **Parallel Processing**: The batch processor supports parallel execution with the `--parallel` flag, which can significantly speed up processing at the cost of more API requests.

4. **Rate Limiting**: Be mindful of API rate limits when using parallel processing or processing large batches.

5. **File Storage**: All scripts save raw API responses to JSON files for debugging and audit purposes. Old files are automatically cleaned up after 30 days.

6. **Web Scraping Considerations**: The `member_bio.py` script uses Selenium for web scraping, which has different requirements:
   - Requires ChromeDriver and Chrome browser to be installed
   - Process in smaller batches to avoid being blocked
   - Works more slowly than API-based scripts due to page loading times
   - Add delays between requests to be respectful of the website

## Troubleshooting

If you encounter issues:

1. Check the log files in the script's directory
2. Look for entries in the `api_sync_status` table
3. Try processing specific members with the `--member` flag
4. Run with a small `--limit` value to test functionality

### Troubleshooting Bio Scraping

For issues with the `member_bio.py` script:

1. Ensure Chrome and ChromeDriver are properly installed
2. Check if the website structure has changed (may require updating selectors)
3. Increase the `WAIT_TIME` if pages aren't loading fully
4. Try with `--member` flag on a known member to isolate issues
5. Examine the raw HTML saved to debug extraction issues

## Advanced Configuration

These scripts support additional configuration via environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `CONGRESSGOV_API_KEY` - API key for Congress.gov
- `LOG_LEVEL` - Set to DEBUG for more verbose logging

Set these in your `.env` file or in your environment before running the scripts.