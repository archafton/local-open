import os
import requests
import psycopg2
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Import the configuration
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_local import DATABASE_URL

def get_env_variable(var_name):
    value = os.getenv(var_name)
    if value is None:
        logger.error(f"Environment variable {var_name} is not set")
        raise ValueError(f"Environment variable {var_name} is not set")
    return value

def api_request(url):
    logger.debug(f"Making API request to: {url}")
    try:
        api_key = get_env_variable('PROPUBLICA_API_KEY')
        headers = {'X-API-Key': api_key}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.debug("API request successful")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error making API request: {str(e)}")
        raise

def get_db_connection():
    logger.debug(f"Attempting to connect to the database: {DATABASE_URL}")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        logger.debug("Database connection successful")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Error connecting to the database: {str(e)}")
        raise

def insert_bill(cur, bill):
    logger.debug(f"Inserting bill: {bill['bill_id']}")
    try:
        cur.execute("""
            INSERT INTO bills (bill_id, title, introduced_date, sponsor)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (bill_id) DO UPDATE
            SET title = EXCLUDED.title,
                introduced_date = EXCLUDED.introduced_date,
                sponsor = EXCLUDED.sponsor
        """, (bill['bill_id'], bill['title'], bill['introduced_date'], bill['sponsor']))
        logger.debug(f"Successfully inserted/updated bill: {bill['bill_id']}")
    except psycopg2.Error as e:
        logger.error(f"Error inserting bill: {str(e)}")
        raise

def lambda_handler(event, context):
    try:
        logger.info("Starting fetch_bills lambda function")
        
        # Fetch recent bills from ProPublica API
        api_endpoint = get_env_variable('PROPUBLICA_BILLS_ENDPOINT')
        data = api_request(api_endpoint)

        conn = get_db_connection()
        cur = conn.cursor()

        for bill in data['results'][0]['bills']:
            insert_bill(cur, bill)

        conn.commit()
        cur.close()
        conn.close()

        logger.info("Successfully processed bills data")
        return {
            'statusCode': 200,
            'body': 'Bills data processed successfully'
        }
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': f'Error processing bills data: {str(e)}'
        }

if __name__ == "__main__":
    result = lambda_handler({}, None)
    print(f"Lambda handler result: {result}")
