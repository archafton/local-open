# Bill Summary Testing Guide

This guide outlines the steps to manually test the bill summary system, including data fetching, enrichment, and AI summary generation.

## Prerequisites

- PostgreSQL database running
- Python environment with required dependencies
- Valid API keys in backend/.env:
  ```bash
  CONGRESSGOV_API_KEY=your_key
  CONGRESSGOV_BILL_TEXT_ENDPOINT=https://api.congress.gov/v3/bill/{congress}/{billType}/{billNumber}/text
  ANTHROPIC_API_KEY=your_key
  ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
  ```

## 1. Start PostgreSQL Database

```bash
# Start PostgreSQL service
brew services start postgresql

# Verify database is running
psql project_tacitus_test
```

## 2. Fetch Initial Bill Data

Run the bill fetch script to populate basic bill information:
```bash
python backend/src/python/congressgov/bill_fetch/bill_fetch.py
```

Validate data with:
```sql
SELECT bill_number, bill_title, introduced_date, status 
FROM bills 
ORDER BY introduced_date DESC 
LIMIT 5;
```

## 3. Fetch Bill Details

Run the bill detail fetch script:
```bash
python backend/src/python/congressgov/bill_fetch/bill_detail_fetch.py
```

Validate data with:
```sql
SELECT bill_number, official_title, latest_action, latest_action_date 
FROM bills 
WHERE latest_action IS NOT NULL 
ORDER BY latest_action_date DESC 
LIMIT 5;
```

## 4. Enrich Bill Data

Run the bill enrichment script:
```bash
python backend/src/python/congressgov/bill_fetch/bill_enrichment.py
```

Validate data with:
```sql
-- Check bill actions
SELECT b.bill_number, COUNT(ba.id) as action_count 
FROM bills b 
LEFT JOIN bill_actions ba ON b.bill_number = ba.bill_number 
GROUP BY b.bill_number 
ORDER BY action_count DESC 
LIMIT 5;

-- Check bill cosponsors
SELECT b.bill_number, COUNT(bc.id) as cosponsor_count 
FROM bills b 
LEFT JOIN bill_cosponsors bc ON b.bill_number = bc.bill_number 
GROUP BY b.bill_number 
ORDER BY cosponsor_count DESC 
LIMIT 5;
```

## 5. Fetch Member Data

Run the member fetch script:
```bash
python backend/src/python/congressgov/members_fetch/member_fetch.py
```

Validate data with:
```sql
SELECT full_name, party, state, chamber, current_member 
FROM members 
WHERE current_member = true 
ORDER BY last_name 
LIMIT 10;
```

## 6. Generate Bill Summaries

The bill summary system uses the bill_text_process.py script to:
1. Fetch bill text from Congress.gov
2. Process XML content
3. Generate AI summaries using Anthropic Claude
4. Extract and validate tags
5. Update the database with summaries and tags

### Run Bill Summary Processor

The bill summary processor needs to be run from the project root directory to ensure proper imports:

```bash
# Make sure you're in the project root directory
cd /Users/jakevance/Documents/github/local-open

# Activate your virtual environment if not already activated
source venv/bin/activate

# Run the processor
python backend/src/python/congressgov/bill_summary/bill_text_process.py
```

### Verify Raw Data Files

1. Check Text Version JSON Files:
```bash
ls -l backend/src/python/congressgov/bill_fetch/raw/text_versions_*.json
```
These files contain the raw API responses for bill text versions.

2. Check Downloaded XML Files:
```bash
ls -l backend/src/python/congressgov/bill_fetch/raw/bill_text_*.xml
```
These files contain the actual bill text content.

3. Check Processed XML Files:
```bash
ls -l backend/src/python/congressgov/bill_fetch/raw/processed/
```
Successfully processed XML files are moved here.

### Examine Text Versions

To verify text versions for a specific bill:

1. Find the saved JSON response:
```bash
find backend/src/python/congressgov/bill_fetch/raw -name "text_versions_HR*" | sort -r | head -n 1
```

2. Review the JSON content to understand available formats:
```bash
cat [found_json_file]
```

Look for:
- Multiple text versions (e.g., Introduced, Reported, Enrolled)
- Available formats (XML, PDF, HTML)
- Dates of different versions

### Validate Processing Steps

1. Check Text Links:
```sql
-- Verify text links were added
SELECT bill_number, bill_text_link, bill_law_link
FROM bills
WHERE bill_text_link IS NOT NULL
ORDER BY introduced_date DESC
LIMIT 5;
```

2. Check Summaries:
```sql
-- View generated summaries
SELECT bill_number,
       LEFT(summary, 150) as summary_preview,
       length(summary) as summary_length
FROM bills
WHERE summary IS NOT NULL
ORDER BY introduced_date DESC
LIMIT 5;
```

3. Check Tags:
```sql
-- View tag categories
SELECT bill_number,
       tags,
       array_length(tags, 1) as tag_count
FROM bills
WHERE tags IS NOT NULL
AND array_length(tags, 1) > 0
ORDER BY introduced_date DESC
LIMIT 5;
```

4. Check Processing Status:
```sql
-- Overview of processing status
SELECT 
    COUNT(*) as total_bills,
    COUNT(bill_text_link) as has_text_link,
    COUNT(summary) as has_summary,
    COUNT(CASE WHEN array_length(tags, 1) > 0 THEN 1 END) as has_tags
FROM bills;
```

5. Check Text Version Details:
```sql
-- View text version information
SELECT bill_number,
       bill_text_link,
       bill_law_link,
       CASE 
           WHEN bill_text_link LIKE '%xml%' THEN 'XML'
           WHEN bill_text_link LIKE '%pdf%' THEN 'PDF'
           ELSE 'OTHER'
       END as text_format
FROM bills
WHERE bill_text_link IS NOT NULL
ORDER BY introduced_date DESC
LIMIT 5;
```

6. Verify XML Processing:
```sql
-- Find bills where XML processing might have failed
SELECT b.bill_number,
       b.bill_text_link,
       b.summary
FROM bills b
WHERE b.bill_text_link LIKE '%xml%'
AND b.summary IS NULL
ORDER BY b.introduced_date DESC;
```

7. Check Version Types:
```sql
-- View bills that became law
SELECT bill_number,
       bill_text_link,
       bill_law_link
FROM bills
WHERE bill_law_link IS NOT NULL
ORDER BY introduced_date DESC;
```

## Monitoring and Logs

Check processing logs in:
- backend/src/python/congressgov/logs/bill_summary_*.log
- backend/src/python/congressgov/logs/congress_api.log
- backend/src/python/congressgov/logs/xml_handler.log

Key metrics to monitor in logs:
- Processing time per bill
- Summary length
- Tag count
- Success/failure rates

## Troubleshooting

### Common Issues

1. Missing Bill Text
```sql
-- Find bills without text links
SELECT bill_number, introduced_date 
FROM bills 
WHERE bill_text_link IS NULL 
ORDER BY introduced_date DESC;
```

2. Failed Summary Generation
```sql
-- Find bills with text but no summary
SELECT bill_number, introduced_date 
FROM bills 
WHERE bill_text_link IS NOT NULL 
AND summary IS NULL 
ORDER BY introduced_date DESC;
```

3. Invalid Tags
```sql
-- Check for unexpected tag formats
SELECT bill_number, tags 
FROM bills 
WHERE tags IS NOT NULL 
AND array_length(tags, 1) > 0 
ORDER BY introduced_date DESC;
```

4. Processing Failures
```sql
-- Find bills that might have failed processing
SELECT bill_number, 
       bill_text_link,
       summary,
       array_length(tags, 1) as tag_count
FROM bills
WHERE bill_text_link IS NOT NULL
AND (
    summary IS NULL OR
    tags IS NULL OR
    array_length(tags, 1) = 0
)
ORDER BY introduced_date DESC;
```

### Congress.gov API Issues

1. API Response Issues:
- Check the raw JSON files in backend/src/python/congressgov/bill_fetch/raw/
- Verify response structure matches expected format
- Look for error messages or unexpected null values

2. XML Download Issues:
- Try accessing the bill_text_link URL directly in a browser
- Check XML file content for completeness
- Verify character encoding in downloaded files

3. Version Selection Issues:
- Review text_versions JSON to ensure correct version selection
- Verify date sorting for latest version
- Check for presence of required format (XML)

4. Law Text Issues:
- Verify bill has become law before expecting law_link
- Check Public Law version availability
- Validate law text URL accessibility

### Error Resolution

1. If bill text fetch fails:
   - Check Congress.gov API status
   - Verify API key in .env file
   - Review congress_api.log for specific errors
   - Check if the bill text URL is accessible in a browser

2. If summary generation fails:
   - Check Anthropic API status
   - Verify ANTHROPIC_API_KEY in .env
   - Review bill_summary logs for error details
   - Check if the bill text was properly extracted from XML

3. If tag validation fails:
   - Check tag_processor.log for validation errors
   - Review tag categories in tag_processor.py
   - Verify tag format in database
   - Ensure the AI response follows the expected schema

4. For XML processing issues:
   - Check the raw XML files in the raw directory
   - Verify XML structure is valid
   - Review xml_handler.log for parsing errors
   - Check if the archived XML files are complete

### Manual Testing of Individual Bills

To test processing of a specific bill:

1. Find the bill's ID:
```sql
SELECT id, bill_number, introduced_date
FROM bills
WHERE bill_number = 'HR1234';
```

2. Reset the bill's summary data:
```sql
UPDATE bills
SET bill_text_link = NULL,
    bill_law_link = NULL,
    summary = NULL,
    tags = NULL
WHERE bill_number = 'HR1234';
```

3. Run the processor with the specific bill ID:
