# Bill Text Implementation Development Prompt

## Project Context
Project Tacitus is a web application that displays information about congressional bills and representatives. The application fetches data from the Congress.gov API and displays it in a user-friendly interface. The frontend is built with React, and the backend uses Python with Flask.

## Quick Start
1. **Task**: Implement file-based storage for bill text versions and improve UI display

2. **Key Files**:
   - backend/src/python/congressgov/bill_fetch/bill_fetch.py
   - backend/src/python/congressgov/bill_fetch/bill_detail_fetch.py
   - backend/src/python/congressgov/bill_fetch/bill_enrichment.py
   - frontend/src/pages/BillDetails.js
3. **Test Bill**: SJRES33 (has multiple text versions)

4. **Start Development**: THIS IS COMPLETE - The api backend and npm frontend are currently running. If virtual env is needed to run commands, be sure to use `backend/venv/bin/activate`
   ```bash
   cd backend && python3 src/api.py  # Start backend
   cd frontend && npm start          # Start frontend
   ```

5. **View Results**: http://localhost:3001/bills/SJRES33

## Development Environment
- Operating System: macOS Sonoma
- Database: PostgreSQL (local)
- Node.js for frontend
- Python 3.x for backend
- VSCode as IDE
- Current working directory: /Users/jakevance/Documents/github/local-open

### Database Access
PostgreSQL database can be queried directly:
```bash
psql postgresql://localhost/project_tacitus_test -c "SELECT COUNT(*) FROM bills;"
```

## API Configuration
Required environment variables (set in backend/.env):
```bash
CONGRESSGOV_BILLS_LIST_ENDPOINT=https://api.congress.gov/v3/bill
CONGRESSGOV_BILL_DETAIL_ENDPOINT=https://api.congress.gov/v3/bill/{congress}/{billType}/{billNumber}
CONGRESSGOV_BILL_SUMMARY_ENDPOINT=https://api.congress.gov/v3/bill/{congress}/{billType}/{billNumber}/summaries
CONGRESSGOV_BILL_TEXT_ENDPOINT=https://api.congress.gov/v3/bill/{congress}/{billType}/{billNumber}/text
CONGRESSGOV_BILL_ACTIONS_ENDPOINT=https://api.congress.gov/v3/bill/{congress}/{billType}/{billNumber}/actions
DATABASE_URL=postgresql://localhost/project_tacitus_test
```

## API Documentation
Detailed API documentation for congress.gov available in:

- Docs/3_API_Documentation/congressgov-summaries.md
- Docs/3_API_Documentation/congressgov-billtext.md
- Docs/3_API_Documentation/congressgov-actions.md

## Available Development Tools
1. Frontend:
   - React Dev Tools
   - npm for package management
   - Local development server (port 3001)

2. Backend:
   - Flask development server (port 5001)
   - Python virtual environment
   - PostgreSQL database

3. API:
   - Congress.gov API key required, set in virtual environment ( source backend/venv/bin/activate ) variables via `backend/.env` 
   - Rate limits apply
   - JSON response format

## Current Architecture
- Frontend: React application (frontend/)
  - Key file: frontend/src/pages/BillDetails.js
      - Associated file: frontend/src/pages/Bills.js
- Backend: Python/Flask API (backend/)
  - Key files:
    - backend/src/api.py
    - backend/src/python/congressgov/bill_fetch/bill_fetch.py
    - backend/src/python/congressgov/bill_fetch/bill_detail_fetch.py
    - backend/src/python/congressgov/bill_fetch/bill_enrichment.py
- Database: PostgreSQL with JSONB columns for complex data

## Development Task
We need to improve the handling of bill text versions and their display in the UI. This involves:
1. Fetching text versions from Congress.gov API
2. Storing them efficiently
3. Displaying them in the Bill Details page

## Current Data Structure
Example bill text version data from Congress.gov API:
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

## Database Schema
See: `backend/src/schema.sql`

Relevant columns in bills table:
```sql
CREATE TABLE bills (
    id SERIAL PRIMARY KEY,
    bill_number VARCHAR(50) NOT NULL UNIQUE,
    text_versions JSONB,  -- Stores text version data
    -- other columns...
);
```

## UI Requirements
Text versions should appear in two places:
1. Top panel: Most recent version with format links
2. Timeline: Text versions aligned with corresponding actions

## Special Cases to Handle
1. Null dates in text versions
2. Multiple versions on same date
3. Different URL patterns for bills vs laws
4. Format type display mapping

## Proposed Solution
We're moving to a file-first approach:
1. Save raw API responses to files
2. Process files to update database
3. Structure matches future S3 storage:
```
/raw/bill/{congress}/{billType}/{billNumber}/
  ├── details.json
  ├── text.json
  ├── summary.json
  └── actions.json
```

## Development Steps
1. Create new fetch scripts for file storage
2. Create processing scripts
3. Update frontend display
4. Add error handling

## Example API Calls
1. Fetch bill details: This example command has a redacted API key, API key set in `backend/.env` as CONGRESSGOV_API_KEY
```
GET https://api.congress.gov/v3/bill/117/sjres/33?format=json&api_key=[REDACTED]
```

2. Fetch text versions:
```
GET https://api.congress.gov/v3/bill/117/sjres/33/text?format=json&api_key=wY0po1XWU2fmT4TZ3er5ttthOAzjZPThy36mjMOS
```

## Starting Point
Review:
- [Bill Text Implementation](bill_text_implementation.md)
- [Bill Text Architecture](bill_text_architecture.md)
- [Bill Text Data Handling](bill_text_data_handling.md)

Then begin with implementing the file storage structure and updating the fetch scripts to use this new approach. Key considerations:
1. Maintain backward compatibility
2. Handle API rate limits
3. Implement proper error handling
4. Add detailed logging

## Success Criteria
1. Text versions properly stored in files
2. Database updated correctly
3. UI displays versions in correct locations
4. Special cases handled properly
5. Error handling implemented
