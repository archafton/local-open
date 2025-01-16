# Bill Text Architecture

## Proposed Solution

### Directory Structure
```
/raw/
  └── bill/
      └── {congress}/              # e.g., 117
          └── {billType}/          # e.g., sjres
              └── {billNumber}/    # e.g., 33
                  ├── details.json  # Basic bill info
                  ├── text.json    # Text versions
                  ├── summary.json # Bill summaries
                  └── actions.json # Bill actions
```

Example for SJRES33:
```
/raw/
  └── bill/
      └── 117/
          └── sjres/
              └── 33/
                  ├── details.json
                  ├── text.json    # Contains all text versions
                  ├── summary.json # Contains all summaries
                  └── actions.json # Contains all actions
```

### Benefits

1. **Logical Organization**
   - Clear hierarchy matches Congress.gov structure
   - Easy to locate specific bill data
   - Separates different types of data

2. **Cloud Migration Ready**
   - Maps directly to S3 bucket structure
   - Supports versioning and lifecycle policies
   - Easy to implement access controls

3. **Efficient Processing**
   - Can process bills in parallel
   - Easy to implement incremental updates
   - Supports backup and restore

4. **Development Friendly**
   - Easy to work with test data
   - Simple to share specific bill data
   - Clear separation of concerns

## Implementation Plan

### 1. API Fetching Scripts
```python
# fetch_bill_data.py
def fetch_and_save(congress, bill_type, bill_number):
    # Create directory structure
    path = f"raw/bill/{congress}/{bill_type}/{bill_number}"
    os.makedirs(path, exist_ok=True)
    
    # Fetch and save each data type
    save_json(fetch_bill_details(), f"{path}/details.json")
    save_json(fetch_bill_text(), f"{path}/text.json")
    save_json(fetch_bill_summary(), f"{path}/summary.json")
    save_json(fetch_bill_actions(), f"{path}/actions.json")
```

### 2. Processing Scripts
```python
# process_bill_data.py
def process_bill(congress, bill_type, bill_number):
    path = f"raw/bill/{congress}/{bill_type}/{bill_number}"
    
    # Load all data
    details = load_json(f"{path}/details.json")
    text = load_json(f"{path}/text.json")
    summary = load_json(f"{path}/summary.json")
    actions = load_json(f"{path}/actions.json")
    
    # Process and update database
    update_bill_details(details)
    update_bill_text(text)
    update_bill_summary(summary)
    update_bill_actions(actions)
```

## Storage Considerations

### 1. Local Development
- Store under project directory
- Use .gitignore to exclude raw data
- Document cleanup procedures

### 2. Production (S3)
- Bucket structure matches local
- Use prefixes for organization
  ```
  s3://project-tacitus-bills/raw/bill/117/sjres/33/text.json
  ```
- Implement lifecycle policies
  * Archive older congresses
  * Delete temporary files
  * Maintain versions

### 3. Migration Strategy
- Start with local storage
- Add S3 upload capability
- Switch to S3 as primary storage
- Keep local as cache/backup

### 4. Access Patterns
- Read-heavy workload
- Batch updates for new data
- Rare updates to existing data

## Advantages

1. **Better Separation of Concerns**
   - Clear distinction between fetching and processing
   - Easier to test and debug each step
   - Better error recovery (can reprocess without refetching)

2. **Efficient API Usage**
   - Single fetch per data type
   - Easy to implement rate limiting
   - Clear audit trail of API responses

3. **Cloud Ready**
   - Structure matches S3 bucket organization
   - Easy to migrate to cloud storage
   - Supports backup and versioning

4. **Improved Maintainability**
   - Each script has a single responsibility
   - Easier to modify processing logic
   - Better data consistency checks

## Risks and Considerations

1. **Storage Requirements**
   - Need to manage disk space for raw files
   - Consider cleanup strategy for old data
   - Plan for S3 migration

2. **Processing Complexity**
   - Need to handle file system operations
   - Must maintain data consistency
   - Additional error handling required

3. **Migration Path**
   - Need to maintain service during transition
   - Database schema changes may be required
   - Consider backward compatibility

## Next Steps

1. Create new fetch scripts with file-based storage
2. Create separate processing scripts
3. Update database schema if needed
4. Modify frontend to handle new data structure
5. Create migration plan for existing data
6. Implement cleanup strategy for raw files
7. Add monitoring for storage usage
8. Document new architecture and processes

## Related Documentation
- [Bill Text Implementation](bill_text_implementation.md) - Current status and issues
- [Bill Text Data Handling](bill_text_data_handling.md) - Special cases and data processing details
