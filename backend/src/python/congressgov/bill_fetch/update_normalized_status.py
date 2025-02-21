import os
import psycopg2
from dotenv import load_dotenv
from bill_fetch import normalize_status

# Load environment variables
load_dotenv()

# Get database connection string
DATABASE_URL = os.getenv('DATABASE_URL')

def update_normalized_statuses():
    """
    One-time script to populate normalized_status for all existing bills
    """
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # First, get all bills and their current status
        cur.execute("SELECT bill_number, status FROM bills")
        bills = cur.fetchall()
        
        print(f"Found {len(bills)} bills to update")
        
        # Update each bill's normalized status
        for bill_number, status in bills:
            normalized = normalize_status(status)
            if normalized:
                cur.execute("""
                    UPDATE bills 
                    SET normalized_status = %s 
                    WHERE bill_number = %s
                """, (normalized, bill_number))
                print(f"Updated {bill_number}: {status} -> {normalized}")
            else:
                print(f"Could not normalize status for {bill_number}: {status}")

        conn.commit()
        print("Successfully updated normalized statuses")
        
    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL or updating database: {error}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    update_normalized_statuses()
