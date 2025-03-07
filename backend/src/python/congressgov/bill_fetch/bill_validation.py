# bill_validation.py
import os
import psycopg2
import logging
import argparse
from dotenv import load_dotenv
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')

def is_historical_bill(congress):
    """Check if a bill is from a historical Congress (6th-42nd)."""
    try:
        congress_num = int(congress)
        return 6 <= congress_num <= 42
    except (ValueError, TypeError):
        return False

def check_missing_details():
    """
    Check for bills missing detailed information with historical awareness
    """
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Bills missing text versions
        cur.execute("""
            SELECT bill_number, congress
            FROM bills
            WHERE text_versions IS NULL OR text_versions = '[]'::jsonb
        """)
        missing_text = cur.fetchall()
        
        # Bills missing summaries (exclude historical bills)
        cur.execute("""
            SELECT bill_number, congress
            FROM bills
            WHERE summary IS NULL AND (congress::int > 42 OR congress::int < 6)
        """)
        missing_summary = cur.fetchall()
        
        # Bills missing policy area tags (exclude historical bills)
        cur.execute("""
            SELECT b.bill_number, b.congress
            FROM bills b
            LEFT JOIN bill_tags bt ON b.id = bt.bill_id
            LEFT JOIN tags t ON bt.tag_id = t.id
            LEFT JOIN tag_types tt ON t.type_id = tt.id
            WHERE (tt.name = 'Policy Area' OR tt.name IS NULL)
            AND (b.congress::int > 42 OR b.congress::int < 6)
            GROUP BY b.bill_number, b.congress
            HAVING COUNT(t.id) = 0
        """)
        missing_policy_area = cur.fetchall()
        
        # Historical bills (for informational purposes)
        cur.execute("""
            SELECT bill_number, congress
            FROM bills
            WHERE congress::int >= 6 AND congress::int <= 42
        """)
        historical_bills = cur.fetchall()
        
        return {
            'missing_text': missing_text,
            'missing_summary': missing_summary,
            'missing_policy_area': missing_policy_area,
            'historical_bills': historical_bills
        }
    
    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error while connecting to PostgreSQL or querying database: {error}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

def check_missing_enrichment():
    """
    Check for bills missing enrichment data with historical awareness
    """
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Bills missing actions
        cur.execute("""
            SELECT b.bill_number, b.congress
            FROM bills b
            LEFT JOIN bill_actions ba ON b.bill_number = ba.bill_number
            GROUP BY b.bill_number, b.congress
            HAVING COUNT(ba.id) = 0
        """)
        missing_actions = cur.fetchall()
        
        # Bills missing subjects (exclude historical bills)
        cur.execute("""
            SELECT b.bill_number, b.congress
            FROM bills b
            LEFT JOIN bill_subjects bs ON b.bill_number = bs.bill_number
            WHERE (b.congress::int > 42 OR b.congress::int < 6)
            GROUP BY b.bill_number, b.congress
            HAVING COUNT(bs.id) = 0
        """)
        missing_subjects = cur.fetchall()
        
        # Bills missing cosponsors (exclude historical bills)
        cur.execute("""
            SELECT b.bill_number, b.congress
            FROM bills b
            LEFT JOIN bill_cosponsors bc ON b.bill_number = bc.bill_number
            WHERE b.sponsor_id IS NOT NULL  -- Only check bills that have a sponsor
            AND (b.congress::int > 42 OR b.congress::int < 6)
            GROUP BY b.bill_number, b.congress
            HAVING COUNT(bc.id) = 0
        """)
        missing_cosponsors = cur.fetchall()
        
        return {
            'missing_actions': missing_actions,
            'missing_subjects': missing_subjects,
            'missing_cosponsors': missing_cosponsors
        }
    
    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error while connecting to PostgreSQL or querying database: {error}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

def export_validation_results(results, output_format='text'):
    """
    Export validation results to a file with historical bill awareness
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"bill_validation_{timestamp}.{output_format}"
    
    if output_format == 'json':
        import json
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
    else:
        with open(filename, 'w') as f:
            f.write("Bill Validation Results\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Historical bills note
            f.write("HISTORICAL BILLS NOTE\n")
            f.write("---------------------\n")
            f.write("Bills from the 6th-42nd Congresses (1799-1873) have limited metadata.\n")
            f.write("They typically have text, titles, and some actions, but do not have sponsors,\n")
            f.write("cosponsors, summaries, amendments, committees, and related bill information.\n")
            f.write("Bills from 1799 (6th Congress) to 1817 (14th Congress) were not numbered.\n\n")
            
            # Historical bills count
            historical_count = len(results['missing_details'].get('historical_bills', []))
            f.write(f"Historical Bills Count: {historical_count}\n\n")
            
            # Missing details
            f.write("BILLS MISSING DETAILS\n")
            f.write("--------------------\n")
            
            f.write("\nMissing Text Versions:\n")
            for bill in results['missing_details']['missing_text']:
                congress_note = " (HISTORICAL)" if is_historical_bill(bill[1]) else ""
                f.write(f"  {bill[0]} (Congress: {bill[1]}{congress_note})\n")
            
            f.write("\nMissing Summaries (excluding historical bills):\n")
            for bill in results['missing_details']['missing_summary']:
                f.write(f"  {bill[0]} (Congress: {bill[1]})\n")
            
            f.write("\nMissing Policy Area Tags (excluding historical bills):\n")
            for bill in results['missing_details']['missing_policy_area']:
                f.write(f"  {bill[0]} (Congress: {bill[1]})\n")
            
            # Missing enrichment
            f.write("\n\nBILLS MISSING ENRICHMENT\n")
            f.write("------------------------\n")
            
            f.write("\nMissing Actions:\n")
            for bill in results['missing_enrichment']['missing_actions']:
                congress_note = " (HISTORICAL)" if is_historical_bill(bill[1]) else ""
                f.write(f"  {bill[0]} (Congress: {bill[1]}{congress_note})\n")
            
            f.write("\nMissing Subjects (excluding historical bills):\n")
            for bill in results['missing_enrichment']['missing_subjects']:
                f.write(f"  {bill[0]} (Congress: {bill[1]})\n")
            
            f.write("\nMissing Cosponsors (excluding historical bills):\n")
            for bill in results['missing_enrichment']['missing_cosponsors']:
                f.write(f"  {bill[0]} (Congress: {bill[1]})\n")
    
    logger.info(f"Validation results exported to {filename}")
    return filename

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Validate bill data in the database')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--include-historical', action='store_true', 
                        help='Include historical bills (6th-42nd Congresses) in validation reports')
    args = parser.parse_args()
    
    try:
        # Run validation checks
        logger.info("Checking for bills missing details...")
        missing_details = check_missing_details()
        
        logger.info("Checking for bills missing enrichment...")
        missing_enrichment = check_missing_enrichment()
        
        # Combine results
        results = {
            'missing_details': missing_details,
            'missing_enrichment': missing_enrichment,
            'timestamp': datetime.now().isoformat()
        }
        
        # Count historical bills
        historical_count = len(missing_details.get('historical_bills', []))
        
        # Print summary
        total_missing_details = sum(len(v) for k, v in missing_details.items() if k != 'historical_bills')
        total_missing_enrichment = sum(len(v) for v in missing_enrichment.values())
        
        logger.info(f"Found {historical_count} historical bills (6th-42nd Congresses)")
        logger.info(f"Found {total_missing_details} bills missing details")
        logger.info(f"Found {total_missing_enrichment} bills missing enrichment")
        
        # Export results
        output_file = args.output if args.output else export_validation_results(results, args.format)
        logger.info(f"Results exported to {output_file}")
        
        # Return lists of bills needing processing
        bills_needing_details = []
        bills_needing_enrichment = []
        
        # Add bills missing text versions (all bills)
        bills_needing_details.extend([b[0] for b in missing_details['missing_text']])
        
        # Add bills missing actions (all bills)
        bills_needing_enrichment.extend([b[0] for b in missing_enrichment['missing_actions']])
        
        # For non-historical bills, add other missing data
        for b in missing_details['missing_summary'] + missing_details['missing_policy_area']:
            if not is_historical_bill(b[1]):
                bills_needing_details.append(b[0])
                
        for b in missing_enrichment['missing_subjects'] + missing_enrichment['missing_cosponsors']:
            if not is_historical_bill(b[1]):
                bills_needing_enrichment.append(b[0])
        
        return {
            'bills_needing_details': list(set(bills_needing_details)),
            'bills_needing_enrichment': list(set(bills_needing_enrichment)),
            'historical_bills': [b[0] for b in missing_details.get('historical_bills', [])]
        }

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()
