import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')

def check_bill_numbers():
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Query to select all bill numbers
        cur.execute("SELECT bill_number FROM bills")
        
        # Fetch all results
        bill_numbers = cur.fetchall()
        
        print("Bill numbers in the database:")
        for (bill_number,) in bill_numbers:
            print(bill_number)
        
        print(f"\nTotal number of bills: {len(bill_numbers)}")
        
    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL or querying database: {error}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    check_bill_numbers()
