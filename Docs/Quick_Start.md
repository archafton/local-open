# Quickstart - Not 1st time setup
1. 1st Terminal
```bash
cd backend
source venv/bin/activate
python3 src/api.py
```

2. 2nd Terminal
```bash
npm start
```

3. 3rd Terminal
check database
```bash
psql postgresql://localhost/project_tacitus_test -c "SELECT COUNT(*) FROM bills;"
```

if not started,

```bash
brew services start postgresql
```


# 1st time setup

1. Set Up Python Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

2. Install Python Dependencies

```bash
pip install -r backend/requirements.txt
```

3. Database setup

```bash
brew install postgresql
brew services start postgresql
```

4. Create Local PostgreSQL Database

```bash
createdb project_tacitus_test
psql -d project_tacitus_test -f backend/src/schema.sql
```

5. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
touch backend/.env
```

Add the following content to the `.env` file:

```
DATABASE_URL=postgresql://localhost/project_tacitus_test
CONGRESSGOV_API_KEY=[INSERTKEY]
ANTHROPIC_API_KEY=[INSERTKEY]
CONGRESSGOV_BILLS_LIST_ENDPOINT=https://api.congress.gov/v3/bill
CONGRESSGOV_BILL_DETAIL_ENDPOINT=https://api.congress.gov/v3/bill/{congress}/{billType}/{billNumber}
CONGRESSGOV_BILL_SUMMARY_ENDPOINT=https://api.congress.gov/v3/bill/{congress}/{billType}/{billNumber}/summaries
CONGRESSGOV_BILL_TEXT_ENDPOINT=https://api.congress.gov/v3/bill/{congress}/{billType}/{billNumber}/text
CONGRESSGOV_BILL_ACTIONS_ENDPOINT=https://api.congress.gov/v3/bill/{congress}/{billType}/{billNumber}/actions
CONGRESSGOV_MEMBER_LIST_ENDPOINT=https://api.congress.gov/v3/member
CONGRESSGOV_MEMBER_DETAIL_ENDPOINT=https://api.congress.gov/v3/member/{bioguideId}
FEC_CANDIDATE_ENDPOINT=https://api.open.fec.gov/v1/candidates
AI_PROCESSOR_ENDPOINT=anthropic
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

6. Set Up and Run Frontend

```bash
cd frontend
npm install
npm start
```

The frontend should now be accessible at `http://localhost:3000`.

7. Run the Flask API server

```bash
cd backend
source venv/bin/activate
python3 src/api.py
```

8. Populate local database

```bash
cd backend
source venv/bin/activate
python3 src/python/congressgov/bill_fetch/bill_fetch.py 
python3 src/python/congressgov/bill_fetch/bill_detail_fetch.py
python3 src/python/congressgov/bill_fetch/bill_enrichment.py
python3 src/python/congressgov/members_fetch/member_fetch.py
python3 src/python/congressgov/members_fetch/member_detail_fetch.py
python3 src/python/congressgov/members_fetch/member_bio.py
```

9. Validate at `http://localhost:3000`