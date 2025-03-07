# Historical Bills Processing Guide

This document outlines the necessary adjustments and considerations for handling historical bills (particularly those from the 6th to 42nd Congresses, 1799-1873) across the bill processing system.

## Table of Contents

1. [API Response Structure Differences](#api-response-structure-differences)
2. [Historical Bills Limitations](#historical-bills-limitations)
3. [Required Adjustments](#required-adjustments)
   - [bill_detail_processor.py](#bill_detail_processorpy)
   - [bill_validation.py](#bill_validationpy)
   - [bill_batch_processor.py](#bill_batch_processorpy)
   - [bill_fetch_core.py](#bill_fetch_corepy)
4. [Schema Considerations](#schema-considerations)
5. [Testing and Validation](#testing-and-validation)
6. [Best Practices](#best-practices)

## API Response Structure Differences

The Congress.gov API returns different data structures for older bills compared to newer ones:

### Newer Bills (Post-1873)

For newer bills, the API returns a single bill object in the `bill` field:

```json
{
    "bill": {
        "congress": 118,
        "type": "HR",
        "number": "10293",
        "introducedDate": "2023-05-15",
        ...
    }
}
```

### Older Bills (1799-1873)

For older bills, the API returns an array of bill objects in the `bill` field:

```json
{
    "bill": [
        {
            "congress": 20,
            "type": "S",
            "number": "34",
            "introducedDate": "1827-12-24",
            ...
        },
        {
            "congress": 20,
            "type": "S",
            "number": "34",
            "introducedDate": "1829-01-12",
            ...
        }
    ]
}
```

This difference causes errors when code tries to access `bill['type']` on what is actually a list.

## Historical Bills Limitations

As noted in the Congress.gov API documentation, older bills (1799-1873) have limited metadata:

- They have text, titles, and some actions
- They do not have sponsors, cosponsors, summaries, amendments, committees, and related bill information
- Bills from 1799 (6th Congress) to 1817 (14th Congress) were not numbered and may have special handling in the API

These limitations need to be considered when processing and validating historical bills.

## Required Adjustments

### bill_detail_processor.py

The `bill_detail_processor.py` script has already been updated with the following changes:

1. Added type checking in the `update_bill_details` method:
   ```python
   # Check if bill_data has the expected structure
   if 'bill' not in bill_data:
       logger.warning("Bill data missing 'bill' field")
       return False
       
   # Handle different bill structures
   if isinstance(bill_data['bill'], list):
       # For older bills (array structure)
       if not bill_data['bill']:  # Empty array
           logger.warning("Bill data contains empty bill array")
           return False
           
       # Sort by updateDate (descending) and use the most recently updated entry
       sorted_bills = sorted(bill_data['bill'], 
                           key=lambda x: x.get('updateDate', ''), 
                           reverse=True)
       bill = sorted_bills[0]
       
       # Log that we found multiple entries
       if len(bill_data['bill']) > 1:
           logger.info(f"Multiple bill entries found for {bill.get('type', '')}{bill.get('number', '')}. "
                     f"Using most recently updated entry from {bill.get('updateDate', 'unknown date')}")
   else:
       # For newer bills (dictionary structure)
       bill = bill_data['bill']
   ```

2. Updated the `process_bill` method with similar logic to handle different structures

3. Added case sensitivity checks in methods that interact with the database using bill numbers:
   ```python
   # Check if the bill exists in the database with this exact bill_number
   cursor.execute("SELECT 1 FROM bills WHERE bill_number = %s", (bill_number,))
   if not cursor.fetchone():
       # Try uppercase version
       uppercase_bill_number = bill_number.upper()
       cursor.execute("SELECT 1 FROM bills WHERE bill_number = %s", (uppercase_bill_number,))
       if cursor.fetchone():
           bill_number = uppercase_bill_number
       else:
           logger.warning(f"Bill {bill_number} not found in database, cannot update actions")
           return 0
   ```

### bill_validation.py

The `bill_validation.py` script needs the following adjustments:

1. **Case Sensitivity Handling**:
   - Add case sensitivity checks in database queries
   - Modify queries to use `UPPER(bill_number)` or add alternative checks for both lowercase and uppercase bill numbers

2. **Historical Bills Awareness**:
   - Add a new validation category specifically for historical bills (6th-42nd Congresses)
   - Adjust expectations for these bills (e.g., don't flag missing sponsors/cosponsors as errors)

3. **Validation Output Enhancement**:
   - Add notes in validation output about expected limitations for historical bills
   - Include Congress number in validation reports to help identify historical bills

Example implementation for historical bills awareness:

```python
def is_historical_bill(congress):
    """Check if a bill is from a historical Congress (6th-42nd)."""
    try:
        congress_num = int(congress)
        return 6 <= congress_num <= 42
    except (ValueError, TypeError):
        return False

def check_missing_details():
    """Check for bills missing detailed information with historical awareness."""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Bills missing text versions
        cur.execute("""
            SELECT bill_number, congress
            FROM bills
            WHERE text_versions IS NULL OR text_versions = '[]'::jsonb
        """)
        missing_text = cur.fetchall()
        
        # Bills missing summaries (exclude historical bills)
        cur.execute("""
            SELECT bill_number, congress
            FROM bills
            WHERE summary IS NULL AND (congress::int > 42 OR congress::int < 6)
        """)
        missing_summary = cur.fetchall()
        
        # Historical bills (for informational purposes)
        cur.execute("""
            SELECT bill_number, congress
            FROM bills
            WHERE congress::int >= 6 AND congress::int <= 42
        """)
        historical_bills = cur.fetchall()
        
        return {
            'missing_text': missing_text,
            'missing_summary': missing_summary,
            'historical_bills': historical_bills
        }
    # ... rest of the function
```

### bill_batch_processor.py

The `bill_batch_processor.py` script needs the following adjustments:

1. **Error Handling Enhancement**:
   - Update error handling to better distinguish between actual errors and expected limitations of historical bills
   - Add specific logging for historical bill processing

2. **Batch Processing Logic**:
   - Add a `--historical` flag to enable specialized processing for older bills
   - Modify the batch processing logic to handle the different bill data structures

3. **Congress-Specific Processing**:
   - Add special handling for bills from early Congresses (6th-42nd)
   - Consider prioritizing or deprioritizing historical bills based on processing needs

Example implementation for historical bills flag:

```python
def main():
    parser = argparse.ArgumentParser(description='Batch processor for Congress.gov bill data')
    # ... existing arguments
    parser.add_argument('--historical', action='store_true', 
                        help='Enable specialized processing for historical bills (6th-42nd Congresses)')
    args = parser.parse_args()
    
    # ... existing code
    
    if args.historical:
        # Get bills from historical Congresses
        historical_bills = []
        for congress in range(6, 43):
            bill_numbers = get_bills_by_congress(str(congress), args.limit)
            for bill_number in bill_numbers:
                bill_type, bill_num = parse_bill_number(bill_number)
                historical_bills.append((str(congress), bill_type, bill_num))
        
        logger.info(f"Found {len(historical_bills)} historical bills to process")
        bills_to_process = historical_bills
    
    # ... rest of the function
```

### bill_fetch_core.py

The `bill_fetch_core.py` script needs the following adjustments:

1. **API Response Structure Handling**:
   - Update the `update_database` function to handle the array structure for older bills
   - Extract common bill structure handling logic into a utility function

2. **Incremental Processing Logic**:
   - Ensure incremental processing works correctly with historical bills
   - Consider adding special handling for historical bills in incremental processing

Example implementation for handling different bill structures:

```python
def get_bill_data(bill):
    """Extract bill data handling both dictionary and list structures."""
    if isinstance(bill, list):
        if not bill:
            return None
        
        # Sort by updateDate (descending) and use the most recently updated entry
        sorted_bills = sorted(bill, key=lambda x: x.get('updateDate', ''), reverse=True)
        return sorted_bills[0]
    else:
        return bill

@with_db_transaction
def update_database(cursor, bills: List[Dict[str, Any]]) -> Dict[str, int]:
    """Update database with bill information."""
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "error": 0}
    
    for bill_data in bills:
        try:
            # Extract bill data handling both structures
            bill = get_bill_data(bill_data.get('bill'))
            if not bill:
                logger.warning("Empty bill data")
                stats["skipped"] += 1
                continue
                
            # Rest of the function using the extracted bill data
            # ...
```

## Schema Considerations

1. **Last Updated Field**:
   - The schema now includes a `last_updated` timestamp field in the bills table
   - This field should be used to prioritize bills for validation and processing
   - Consider adding indexes on this field if not already present

2. **Bill Number Consistency**:
   - Ensure consistent handling of bill number case (uppercase vs. lowercase)
   - Consider normalizing bill numbers to uppercase in the database

3. **Congress Number Handling**:
   - Ensure the `congress` field is properly indexed for efficient querying
   - Consider adding a boolean flag for historical bills to enable faster filtering

## Testing and Validation

1. **Test Cases**:
   - Create specific test cases for historical bills
   - Test with bills from different time periods to ensure consistent handling

2. **Validation Metrics**:
   - Track processing success rates separately for historical and modern bills
   - Monitor for specific errors related to historical bill processing

3. **Manual Verification**:
   - Periodically manually verify a sample of processed historical bills
   - Compare with the Congress.gov website to ensure accuracy

## Recent Updates (March 2025)

### Subjects and Cosponsors Fetching

The `bill_detail_processor.py` script has been updated to properly fetch subjects and cosponsors from their dedicated API endpoints. Previously, the script was looking for this data in the main bill response, but the API actually provides this data through separate endpoints.

1. **New API Endpoint Methods**:
   ```python
   def fetch_bill_cosponsors(self, url: str) -> Dict[str, Any]:
       """Fetch bill cosponsors using the provided URL."""
       logger.info(f"Fetching cosponsors from: {url}")
       return self.api_client.get(url.replace(BASE_API_URL + '/', ''))
   
   def fetch_bill_subjects(self, url: str) -> Dict[str, Any]:
       """Fetch bill subjects using the provided URL."""
       logger.info(f"Fetching subjects from: {url}")
       return self.api_client.get(url.replace(BASE_API_URL + '/', ''))
   ```

2. **Updated Process Bill Method**:
   ```python
   # Fetch and update cosponsors
   if 'cosponsors' in bill and 'url' in bill['cosponsors']:
       try:
           cosponsors_url = bill['cosponsors']['url']
           cosponsors_data = self.fetch_bill_cosponsors(cosponsors_url)
           self.save_bill_data(cosponsors_data, congress_str, bill_type, bill_number, 'cosponsors')
           
           if 'cosponsors' in cosponsors_data:
               results["cosponsors_updated"] = self.update_bill_cosponsors(
                   bill_number=full_bill_number, 
                   cosponsors=cosponsors_data['cosponsors']
               )
       except Exception as e:
           logger.error(f"Error processing cosponsors for bill {full_bill_number}: {str(e)}")
   
   # Fetch and update subjects
   if 'subjects' in bill and 'url' in bill['subjects']:
       try:
           subjects_url = bill['subjects']['url']
           subjects_data = self.fetch_bill_subjects(subjects_url)
           self.save_bill_data(subjects_data, congress_str, bill_type, bill_number, 'subjects')
           
           if 'subjects' in subjects_data and 'legislativeSubjects' in subjects_data['subjects']:
               legislative_subjects = subjects_data['subjects']['legislativeSubjects']
               if legislative_subjects:
                   results["subjects_updated"] = self.update_bill_subjects(
                       bill_number=full_bill_number, 
                       subjects=legislative_subjects
                   )
       except Exception as e:
           logger.error(f"Error processing subjects for bill {full_bill_number}: {str(e)}")
   ```

3. **Updated Bill Selection Query**:
   The `get_bills_for_processing` function has been updated to also select bills that are missing subjects or cosponsors:
   ```python
   # Get bills with missing details or enrichment
   cur.execute("""
       SELECT bill_number, congress
       FROM bills
       WHERE text_versions IS NULL
          OR NOT EXISTS (SELECT 1 FROM bill_actions WHERE bill_actions.bill_number = bills.bill_number)
          OR NOT EXISTS (SELECT 1 FROM bill_subjects WHERE bill_subjects.bill_number = bills.bill_number)
          OR (
              bills.sponsor_id IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM bill_cosponsors WHERE bill_cosponsors.bill_number = bills.bill_number)
          )
       ORDER BY introduced_date DESC
       LIMIT %s
   """, (limit,))
   ```

### Case Sensitivity Standardization

To address case sensitivity issues with bill numbers, the following changes have been made:

1. **Standardized Bill Numbers to Uppercase**:
   ```python
   bill_number = f"{bill['type']}{bill['number']}".upper()
   full_bill_number = f"{bill_type}{bill_number}".upper()
   ```

2. **Updated Validation Queries**:
   The `bill_validation.py` script has been updated to use direct equality comparisons instead of UPPER function calls:
   ```python
   # Bills missing actions
   cur.execute("""
       SELECT b.bill_number, b.congress
       FROM bills b
       LEFT JOIN bill_actions ba ON b.bill_number = ba.bill_number
       GROUP BY b.bill_number, b.congress
       HAVING COUNT(ba.id) = 0
   """)
   ```

3. **Database Migration**:
   A new migration script (`20250306_standardize_bill_numbers.sql`) has been created to convert all existing bill numbers to uppercase across all tables:
   ```sql
   -- Update bills table
   UPDATE bills
   SET bill_number = UPPER(bill_number)
   WHERE bill_number != UPPER(bill_number);

   -- Update bill_actions table
   UPDATE bill_actions
   SET bill_number = UPPER(bill_number)
   WHERE bill_number != UPPER(bill_number);

   -- Update bill_cosponsors table
   UPDATE bill_cosponsors
   SET bill_number = UPPER(bill_number)
   WHERE bill_number != UPPER(bill_number);

   -- Update bill_subjects table
   UPDATE bill_subjects
   SET bill_number = UPPER(bill_number)
   WHERE bill_number != UPPER(bill_number);
   ```

### Usage Instructions

To process bills with these updates:

1. **Apply the Database Migration**:
   ```bash
   cd backend && python src/scripts/apply_migration.py src/migrations/20250306_standardize_bill_numbers.sql
   ```

2. **Run the Bill Detail Processor**:
   ```bash
   cd backend && python src/python/congressgov/bill_fetch/bill_detail_processor.py --all
   ```

3. **Validate the Results**:
   ```bash
   cd backend && python src/python/congressgov/bill_fetch/bill_validation.py
   ```

These updates ensure that the bill processing system correctly fetches and stores subjects and cosponsors data, and handles bill numbers consistently across all tables.

## Best Practices

1. **Logging and Monitoring**:
   - Use consistent logging patterns across all scripts
   - Log specific information about historical bill processing
   - Monitor for recurring errors with historical bills

2. **Error Handling**:
   - Distinguish between expected limitations and actual errors
   - Handle missing data gracefully for historical bills
   - Provide clear error messages that indicate when issues are related to historical bill limitations

3. **Documentation**:
   - Keep documentation updated with any new findings about historical bill data
   - Document any special handling or exceptions for historical bills
   - Include examples of both data structures in code comments

4. **Code Organization**:
   - Extract common functionality for handling different bill structures into utility functions
   - Use consistent patterns across all scripts
   - Consider creating a dedicated module for historical bill processing

By implementing these adjustments and following these best practices, the bill processing system will be able to handle both modern and historical bills efficiently and accurately.
