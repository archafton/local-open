# Bill Text Implementation Status

## Current Implementation

### Data Flow
1. `bill_detail_fetch.py` and `bill_enrichment.py` both make API calls to congress.gov
   - `bill_detail_fetch.py` fetches basic bill info and summaries
   - `bill_enrichment.py` handles additional data like text versions
2. Both scripts save raw JSON responses to `/raw` directory
3. Both scripts attempt to update the database directly after fetching

### Data Structure Example
From `bill_text_SJRES33_20241024_210740.json`:
```json
{
  "textVersions": [
    {
      "date": null,
      "type": "Enrolled Bill",
      "formats": [
        {
          "type": "Formatted Text",
          "url": "https://www.congress.gov/117/bills/sjres33/BILLS-117sjres33enr.htm"
        },
        {
          "type": "PDF",
          "url": "https://www.congress.gov/117/bills/sjres33/BILLS-117sjres33enr.pdf"
        }
      ]
    },
    {
      "date": "2021-12-17T04:59:59Z",
      "type": "Public Law",
      "formats": [
        {
          "type": "Formatted Text",
          "url": "https://www.congress.gov/117/plaws/publ73/PLAW-117publ73.htm"
        }
      ]
    }
  ]
}
```

### Frontend Display
- Bill text links should appear in two places:
  1. Top panel: Most recent text version with links to formats (HTML/PDF/XML)
     ```html
     Public Law: 2021-12-17 - HTML | PDF | XML
     ```
  2. Timeline: Text version links aligned with corresponding action dates
     ```html
     <action date>
     <action text>
     [View HTML] [View PDF] [View XML]
     ```

### Current Issues

1. **Overlapping Functionality**
   - Both scripts fetch and process similar data
   - Risk of race conditions when updating database
   - Inefficient use of API rate limits

2. **Data Storage**
   - Raw JSON files are saved but not utilized
   - Direct database updates make testing/recovery harder
   - No clear separation between data fetching and processing

3. **Frontend Display**
   - Text versions not consistently appearing in UI
   - Date matching between actions and text versions unreliable
   - Special cases need handling:
     * Null dates in text versions (e.g., "Enrolled Bill" version)
     * Multiple versions on same date (e.g., "2021-12-14" has two versions)
     * Different URL patterns for Public Law vs. Bill versions

4. **Data Handling Edge Cases**
   - Null dates need special handling (usually earliest version)
   - Multiple versions on same date need ordering logic
   - Different URL patterns:
     * Bills: `BILLS-117sjres33enr.htm`
     * Public Laws: `PLAW-117publ73.htm`
   - Format type variations:
     * "Formatted Text" should display as "HTML"
     * XML files may have different suffixes (`_uslm.xml` vs `.xml`)

## Implementation Progress

### Completed
1. Initial database schema with text_versions JSONB column
2. Basic frontend display in BillDetails.js
3. Initial API integration in bill_detail_fetch.py

### In Progress
1. Fixing JSON parsing issues in frontend
2. Handling null dates in text versions
3. Matching text versions with actions

### Next Steps
1. Implement new directory structure for raw files
2. Create separate fetch and process scripts
3. Update frontend to handle all text version cases
4. Add proper error handling and logging

## Questions and Decisions

1. **Storage Strategy**
   - Q: Store summaries in database or files?
   - A: Keep in database for now (TEXT column can handle size)
   - Future: Consider moving to S3 for larger datasets

2. **API Rate Limits**
   - Q: How to handle Congress.gov API limits?
   - A: Implement file-first approach to minimize API calls
   - Future: Add caching layer for frequently accessed data

3. **Frontend Display**
   - Q: How to handle multiple versions on same date?
   - A: Group by date, sort by type importance
   - Future: Add collapsible groups for better organization

## Related Documentation
- [Bill Text Architecture](bill_text_architecture.md) - Proposed new architecture and storage details
- [Bill Text Data Handling](bill_text_data_handling.md) - Special cases and data processing details
