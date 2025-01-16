Data flow for local POC of Project Tacitus, focusing on how legislative data, particularly bills, are processed from API retrieval to storage and analysis. This description will incorporate the use of python functions, local postgresql database, and the Anthropic API for bill summarization.

Data Flow:

1. API Data Retrieval:
   - Python functions are used to pull data from the first API, Congress.gov API for legislative data (bills, representatives)

2. Initial Data Storage:
   - For smaller datasets, the python functions directly store the retrieved data in the PostgreSQL database.
   - For larger documents, particularly bills, the process is as follows:
     a. Python functions retrieve the bill data from the API.
     b. The full bill text and metadata are stored in an a "raw" directory locally.
     c. The "raw" directory is organized to mirror the structure of the API endpoint it came from.
     d. A hyperlink to the full bill text is also stored alongside the bill data.

3. Bill Processing and Summarization:
   - Another set of Python functions handle the bill summarization process:
     a. These functions retrieve the full bill text from the "raw" directory.
     b. The bill text is sent to the Anthropic API for summarization, a list of the possible "tags" from the schema, and asks the Anthropic API to summarize the text, and return a list of tags from the list that are appropriate.
     c. The Anthropic API processes the text and returns a summary and a list of tags.

4. Database Update:
   - After receiving the summary from the Anthropic API, the Python function:
     a. Updates the PostgreSQL database with the bill summary.
     b. Stores a link to the full bill text alongside the summary in the database.
     c. Adds the tags to the row from the tags list.

5. Data Access for Frontend:
   - The React frontend accesses this processed and summarized data through API calls to the backend services.
   - These backend services query the PostgreSQL database to retrieve the summarized bill information, representative data, and other analytical data for display in the various dashboards.