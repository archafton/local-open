# Python Package Structure Guide for Project Tacitus

This guide explains the Python package structure for Project Tacitus, how to use it for local development, and how to prepare for AWS Lambda deployment.

## Package Structure

The congressgov package is structured as follows:

```
backend/
├── setup.py                  # Package installation configuration
└── src/
    └── python/
        ├── __init__.py       # Python package marker
        └── congressgov/
            ├── __init__.py   # congressgov package marker
            ├── bill_fetch/
            │   ├── __init__.py
            │   ├── bill_fetch_core.py
            │   ├── bill_detail_processor.py
            │   ├── bill_batch_processor.py
            │   └── ...
            ├── members_fetch/
            │   ├── __init__.py
            │   ├── member_fetch_core.py
            │   └── ...
            ├── bill_summary/
            │   ├── __init__.py
            │   └── ...
            └── utils/
                ├── __init__.py
                ├── api.py
                ├── database.py
                └── ...
```

## Installation for Local Development

To install the package in development mode:

```bash
cd /path/to/project/backend
pip install -e .
```

This makes the package available in your Python environment while still allowing you to edit the code.

## Running Scripts

After installation, you can run the scripts in multiple ways:

### 1. Using Entry Points

The setup.py file defines entry points for the main scripts, allowing you to run them directly:

```bash
# Run bill fetching
bill-fetch --start-date 2023-01-01 --end-date 2023-12-31

# Run member fetching
member-fetch --force-full

# Run bill detail processing
bill-detail --limit 50
```

### 2. Using Python Module Syntax

You can run the scripts as Python modules:

```bash
python -m congressgov.bill_fetch.bill_fetch_core --start-date 2023-01-01 --end-date 2023-12-31
python -m congressgov.members_fetch.member_fetch_core --force-full
```

### 3. Original Method (Unchanged)

You can still run the scripts directly from their directories:

```bash
cd /path/to/project/backend/src/python/congressgov/bill_fetch
python bill_fetch_core.py --start-date 2023-01-01 --end-date 2023-12-31
```

The scripts have been modified to handle imports correctly regardless of how they're run.

## Import Handling

The scripts use a try/except pattern to handle imports in different environments:

```python
try:
    # Try the direct import first (works when package is installed)
    from congressgov.utils.logging_config import setup_logging
    # ...
except ImportError:
    # If that fails, add the parent directory to the path
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from utils.logging_config import setup_logging
    # ...
```

This allows the scripts to work in both development and production environments without modification.

## AWS Lambda Deployment

Each script includes a `lambda_handler` function that can be used as an AWS Lambda entry point. For example:

```python
def lambda_handler(event, context):
    """AWS Lambda handler for bill fetching."""
    # ...
```

### Creating a Lambda Deployment Package

To create a deployment package for Lambda:

```bash
# Create a deployment directory
mkdir -p lambda_package

# Install dependencies
pip install -r backend/requirements.txt -t lambda_package

# Copy the congressgov package
cp -r backend/src/python/congressgov lambda_package/

# Create a zip file
cd lambda_package
zip -r ../lambda_deployment.zip .
```

### Lambda Configuration

When configuring your Lambda function:

1. **Handler**: Set the handler to the appropriate function, e.g., `congressgov.bill_fetch.bill_fetch_core.lambda_handler`
2. **Runtime**: Use Python 3.8 or higher
3. **Environment Variables**: Set the necessary environment variables, such as `DATABASE_URL` and `CONGRESSGOV_API_KEY`

### Lambda Event Format

The Lambda handler expects an event with parameters similar to the command-line arguments:

```json
{
  "force_full": false,
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "days": 7
}
```

## Best Practices

1. **Use Virtual Environments**: Always use a virtual environment for development to avoid package conflicts
2. **Keep Dependencies Updated**: Regularly update the requirements.txt file to include all necessary dependencies
3. **Test Lambda Handlers Locally**: Test the Lambda handlers locally before deployment
4. **Use Environment Variables**: Store configuration in environment variables rather than hardcoding values
5. **Monitor Lambda Execution**: Set up CloudWatch Logs and Metrics to monitor Lambda execution

## Troubleshooting

### Import Errors

If you encounter import errors:

1. Make sure you've installed the package in development mode
2. Check that all directories have `__init__.py` files
3. Try running the script using the Python module syntax

### Lambda Deployment Issues

If you encounter issues with Lambda deployment:

1. Make sure all dependencies are included in the deployment package
2. Check that the handler path is correct
3. Verify that the Lambda execution role has the necessary permissions
4. Check CloudWatch Logs for error messages
