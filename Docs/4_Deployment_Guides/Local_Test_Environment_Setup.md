# Local Test Environment Setup Guide for Project Tacitus
# arch says THIS IS NOT APPLICABLE.....YET 

## Prerequisites

- Python 3.8 or higher
- PostgreSQL
- Node.js and npm (for the frontend)
- Git (for cloning the project repository)

## Setup Steps

### 1. Install PostgreSQL

If you haven't installed PostgreSQL yet, follow these steps:

For macOS (using Homebrew):
```bash
brew install postgresql
brew services start postgresql
```

For other operating systems, please refer to the [official PostgreSQL documentation](https://www.postgresql.org/download/).

Status: COMPLETE

### 2. Clone the Repository and Create Local Test Directory

```bash
git clone https://github.com/archafton/local-open.git project_tacitus_local_test
cd project_tacitus_local_test
```

Status: COMPLETE

### 3. Set Up Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

Status: COMPLETE

### 4. Install Python Dependencies

```bash
pip install -r backend/requirements.txt
```

Status: COMPLETE

### 5. Set Up Local PostgreSQL Database

```bash
createdb project_tacitus_test
```

Status: COMPLETE

### 6. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
touch .env
```

Add the following content to the `.env` file:

```
DATABASE_URL=postgresql://localhost/project_tacitus_test
AWS_ACCESS_KEY_ID=dummy_access_key
AWS_SECRET_ACCESS_KEY=dummy_secret_key
AWS_REGION=us-west-2
```

Status: COMPLETE

### 7. Modify Configuration for Local Testing

Create a `config_local.py` file in the `backend/src` directory:

```python
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')

# Add other configuration variables as needed
```

Status: COMPLETE

### 8. Adapt Lambda Functions for Local Execution

Create a `run_local.py` script in the `backend/src/lambda_functions` directory:

```python
import importlib
import sys

def run_lambda_locally(function_name, event={}):
    try:
        module = importlib.import_module(f"{function_name}.{function_name}")
        handler = getattr(module, "lambda_handler")
        result = handler(event, None)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_local.py <function_name>")
        sys.exit(1)

    function_name = sys.argv[1]
    run_lambda_locally(function_name)
```

Status: COMPLETE

### 9. Set Up Local Database Schema

Run the SQL schema file to set up your local database:

```bash
psql -d project_tacitus_test -f backend/src/schema.sql
```

Status: COMPLETE

### 10. Run Lambda Functions Locally

To run a Lambda function locally:

```bash
python backend/src/lambda_functions/run_local.py fetch_bills
```

Status: INCOMPLETE

### 11. Set Up and Run Frontend Locally

```bash
cd frontend
npm install
npm start
```

The frontend should now be accessible at `http://localhost:3000`.

Status: INCOMPLETE

## Usage

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Run Lambda functions locally to populate the database:
   ```bash
   python backend/src/lambda_functions/run_local.py <function_name>
   ```

3. Start the frontend:
   ```bash
   cd frontend
   npm start
   ```

4. Access the application at `http://localhost:3000`

## Best Practices

1. Keep the `.env` file out of version control by adding it to `.gitignore`.
2. Regularly sync your local test environment with the main project repository.
3. Use this environment for quick iterations and testing, but ensure thorough testing in dev and staging environments before deploying to production.
4. Document any changes made specifically for the local environment to ensure they don't accidentally get pushed to the main project.

## Conclusion

This local test environment allows you to quickly iterate and test changes without affecting the main project environments. It provides a safe space for experimentation and debugging while maintaining separation from the dev, staging, and production setups.

Note: If you encounter any issues during the setup process, please refer to the error messages and consult the documentation of the specific tools or libraries causing the problem.
