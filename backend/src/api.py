from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import requests

app = Flask(__name__)
# Enable CORS for all domains on all routes
CORS(app)

# Database connection string
DB_CONNECTION_STRING = "postgresql://localhost/project_tacitus_test"

def get_db_connection():
    return psycopg2.connect(DB_CONNECTION_STRING)

def parse_json_field(value, default=None):
    """Safely parse a JSON field, returning default if parsing fails"""
    if value is None:
        return default
    try:
        if isinstance(value, str):
            return json.loads(value)
        return value  # Already parsed by psycopg2
    except (json.JSONDecodeError, TypeError):
        return default

@app.route('/api/representatives', methods=['GET'])
def get_representatives():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT chamber, full_name, party, leadership_role, state, district, 
               total_votes, missed_votes, total_present, bioguide_id 
        FROM members 
        WHERE current_member = true
    """)
    representatives = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(representatives)

@app.route('/api/representatives/<bioguide_id>/bio', methods=['GET'])
def get_representative_bio(bioguide_id):
    """Fetch biography from bioguide.congress.gov"""
    url = f"https://bioguide.congress.gov/search/bio/{bioguide_id}.json"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return jsonify({
            'biography': data.get('profileText', 'Biography not available')
        })
    except Exception as e:
        return jsonify({
            'biography': 'Biography not available',
            'error': str(e)
        }), 404

@app.route('/api/representatives/<bioguide_id>', methods=['GET'])
def get_representative_details(bioguide_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get representative details including new fields
    cur.execute("""
        SELECT m.*, 
               array_agg(DISTINCT c.committee_name) FILTER (WHERE c.committee_name IS NOT NULL) as committees
        FROM members m
        LEFT JOIN bill_committees bc ON bc.committee_id IN (
            SELECT id FROM committees WHERE chamber = m.chamber
        )
        LEFT JOIN committees c ON bc.committee_id = c.id
        WHERE m.bioguide_id = %s
        GROUP BY m.id
    """, (bioguide_id,))
    representative = cur.fetchone()
    
    if representative:
        # Get leadership history
        cur.execute("""
            SELECT congress, leadership_type as type
            FROM member_leadership
            WHERE member_id = (SELECT id FROM members WHERE bioguide_id = %s)
            ORDER BY congress DESC
        """, (bioguide_id,))
        representative['leadership_history'] = cur.fetchall()
        
        # Get party history
        cur.execute("""
            SELECT party_name, party_code, start_year
            FROM member_party_history
            WHERE member_id = (SELECT id FROM members WHERE bioguide_id = %s)
            ORDER BY start_year DESC
        """, (bioguide_id,))
        representative['party_history'] = cur.fetchall()
        
        # Get sponsored bills
        cur.execute("""
            SELECT b.bill_number, b.bill_title, b.introduced_date
            FROM sponsored_legislation sl
            JOIN bills b ON sl.bill_id = b.id
            JOIN members m ON sl.member_id = m.id
            WHERE m.bioguide_id = %s
            ORDER BY b.introduced_date DESC
        """, (bioguide_id,))
        representative['sponsored_bills'] = cur.fetchall()
        
        # Get cosponsored bills
        cur.execute("""
            SELECT b.bill_number, b.bill_title
            FROM bill_cosponsors bc
            JOIN bills b ON bc.bill_number = b.bill_number
            WHERE bc.cosponsor_id = %s
            ORDER BY b.introduced_date DESC
        """, (bioguide_id,))
        representative['cosponsored_bills'] = cur.fetchall()
    
    cur.close()
    conn.close()
    
    if representative is None:
        return jsonify({'error': 'Representative not found'}), 404
        
    return jsonify(representative)

@app.route('/api/bills/congresses', methods=['GET'])
def get_congresses():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT DISTINCT congress 
        FROM bills 
        WHERE congress IS NOT NULL 
        ORDER BY congress DESC
    """)
    congresses = [row['congress'] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(congresses)

@app.route('/api/bills', methods=['GET'])
def get_bills():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT b.id, b.bill_number, b.bill_title, b.sponsor_id, 
               m.full_name as sponsor_name, m.party as sponsor_party,
               b.introduced_date, b.status, b.tags, b.congress,
               b.latest_action, b.latest_action_date
        FROM bills b
        LEFT JOIN members m ON b.sponsor_id = m.bioguide_id
        ORDER BY b.introduced_date DESC
    """)
    bills = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(bills)

@app.route('/api/bills/<bill_number>', methods=['GET'])
def get_bill_details(bill_number):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get bill details with sponsor information
    cur.execute("""
        SELECT b.*, 
               m.full_name as sponsor_name, m.party as sponsor_party,
               m.chamber as sponsor_chamber
        FROM bills b
        LEFT JOIN members m ON b.sponsor_id = m.bioguide_id
        WHERE b.bill_number = %s
    """, (bill_number,))
    bill = cur.fetchone()
    
    if bill:
        # Get bill actions for timeline
        cur.execute("""
            SELECT action_date, action_text, action_type
            FROM bill_actions
            WHERE bill_number = %s
            ORDER BY action_date
        """, (bill_number,))
        bill['actions'] = cur.fetchall()
        
        # Get cosponsors with member details
        cur.execute("""
            SELECT bc.*, m.full_name, m.party, m.chamber
            FROM bill_cosponsors bc
            LEFT JOIN members m ON bc.cosponsor_id = m.bioguide_id
            WHERE bc.bill_number = %s
        """, (bill_number,))
        bill['cosponsors'] = cur.fetchall()
        
        # Get subjects
        cur.execute("""
            SELECT subject_name
            FROM bill_subjects
            WHERE bill_number = %s
        """, (bill_number,))
        bill['subjects'] = [row['subject_name'] for row in cur.fetchall()]

        # Convert action dates to strings for JSON serialization
        for action in bill['actions']:
            if action['action_date']:
                action['action_date'] = action['action_date'].isoformat()

        # Handle JSON fields
        bill['summary'] = parse_json_field(bill['summary'], [])
        bill['text_versions'] = parse_json_field(bill['text_versions'], [])
    
    cur.close()
    conn.close()
    
    if bill is None:
        return jsonify({'error': 'Bill not found'}), 404
        
    return jsonify(bill)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
