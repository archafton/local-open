from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import requests
import logging
import os

# Set up logging with absolute path
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api.log')
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Log startup message
logging.info("API server starting up")

app = Flask(__name__)
# Enable CORS with specific configuration
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3001"}}, supports_credentials=True)

@app.errorhandler(Exception)
def handle_error(error):
    logging.error(f"Error: {str(error)}")
    response = jsonify({'error': str(error)})
    response.status_code = 500
    return response

# Database connection string
DB_CONNECTION_STRING = "postgresql://localhost/project_tacitus_test"

def get_db_connection():
    logging.info(f"Connecting to database with connection string: {DB_CONNECTION_STRING}")
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        logging.info("Successfully connected to database")
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to database: {str(e)}")
        raise

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
    # Get filter and pagination parameters
    full_name = request.args.get('full_name', '')
    chamber = request.args.get('chamber', '')
    party = request.args.get('party', '')
    leadership_role = request.args.get('leadership_role', '')
    state = request.args.get('state', '')
    district = request.args.get('district', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))

    # Log the chamber value for debugging
    logging.info(f"Chamber filter value: '{chamber}'")

    # Get unique chamber values from database for debugging
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT DISTINCT chamber FROM members WHERE current_member = true ORDER BY chamber")
    unique_chambers = [row['chamber'] for row in cur.fetchall()]
    logging.info(f"Unique chamber values in database: {unique_chambers}")

    # If filtering by House, try both variations
    if chamber == 'House Of Representatives':
        cur.execute("SELECT COUNT(*) FROM members WHERE current_member = true AND chamber = 'House'")
        house_count = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) FROM members WHERE current_member = true AND chamber = 'House Of Representatives'")
        house_of_reps_count = cur.fetchone()['count']
        logging.info(f"Found {house_count} members with chamber='House' and {house_of_reps_count} with chamber='House Of Representatives'")

    cur.close()
    conn.close()

    # Calculate offset
    offset = (page - 1) * per_page

    # Build the WHERE clause dynamically
    where_clauses = ["current_member = true"]
    params = []

    if full_name:
        where_clauses.append("LOWER(full_name) LIKE LOWER(%s)")
        params.append(f"%{full_name}%")
    
    if chamber:
        where_clauses.append("chamber = %s")  # Exact match for chamber
        params.append(chamber)
    
    if party:
        where_clauses.append("party = %s")  # Exact match for party code
        params.append(party)
    
    if leadership_role:
        where_clauses.append("LOWER(leadership_role) LIKE LOWER(%s)")
        params.append(f"%{leadership_role}%")
    
    if state:
        where_clauses.append("LOWER(state) LIKE LOWER(%s)")
        params.append(f"%{state}%")
    
    if district:
        where_clauses.append("district = %s")
        params.append(district)

    # Base WHERE clause
    where_sql = " WHERE " + " AND ".join(where_clauses)

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get total count
    count_query = """
        SELECT COUNT(*) 
        FROM members
    """ + where_sql

    cur.execute(count_query, params)
    total_count = cur.fetchone()['count']

    # Get sort parameters
    sort_key = request.args.get('sort_key', 'full_name')
    sort_direction = request.args.get('sort_direction', 'asc')

    # Map frontend sort keys to SQL columns
    sort_column_map = {
        'full_name': 'full_name',
        'chamber': 'chamber',
        'party': 'party',
        'leadership_role': 'COALESCE(leadership_role, \'\')',  # Handle NULL values
        'state': 'state',
        'district': 'COALESCE(district, \'\')',  # Handle NULL values
        'total_votes': 'COALESCE(total_votes, 0)',  # Handle NULL values
        'missed_votes': 'COALESCE(missed_votes, 0)',  # Handle NULL values
        'total_present': 'COALESCE(total_present, 0)'  # Handle NULL values
    }

    # Get the SQL column name, defaulting to full_name if invalid key
    sort_column = sort_column_map.get(sort_key, 'full_name')
    
    # Validate sort direction
    if sort_direction not in ['asc', 'desc']:
        sort_direction = 'asc'

    # Get paginated data
    data_query = """
        SELECT chamber, full_name, party, leadership_role, state, district, 
               total_votes, missed_votes, total_present, bioguide_id 
        FROM members
    """ + where_sql + f"""
        ORDER BY {sort_column} {sort_direction.upper()} NULLS LAST
        LIMIT %s OFFSET %s
    """

    # Add pagination parameters
    cur.execute(data_query, params + [per_page, offset])
    representatives = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        'representatives': representatives,
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': (total_count + per_page - 1) // per_page
    })

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
        
        # Get sponsored bills with more details
        cur.execute("""
            SELECT b.bill_number, b.bill_title, b.introduced_date, 
                   b.status, b.normalized_status, b.congress,
                   b.latest_action, b.latest_action_date,
                   array_agg(DISTINCT s.subject_name) FILTER (WHERE s.subject_name IS NOT NULL) as subjects
            FROM bills b
            LEFT JOIN bill_subjects s ON b.bill_number = s.bill_number
            WHERE b.sponsor_id = %s
            GROUP BY b.bill_number, b.bill_title, b.introduced_date, 
                     b.status, b.normalized_status, b.congress,
                     b.latest_action, b.latest_action_date
            ORDER BY b.introduced_date DESC
        """, (bioguide_id,))
        representative['sponsored_bills'] = cur.fetchall()
        
        # Get cosponsored bills with more details
        cur.execute("""
            SELECT b.bill_number, b.bill_title, b.introduced_date,
                   b.status, b.normalized_status, b.congress,
                   b.latest_action, b.latest_action_date,
                   array_agg(DISTINCT s.subject_name) FILTER (WHERE s.subject_name IS NOT NULL) as subjects,
                   m_sponsor.full_name as sponsor_name,
                   m_sponsor.party as sponsor_party
            FROM bills b
            JOIN bill_cosponsors bc ON b.bill_number = bc.bill_number
            LEFT JOIN bill_subjects s ON b.bill_number = s.bill_number
            LEFT JOIN members m_sponsor ON b.sponsor_id = m_sponsor.bioguide_id
            WHERE bc.cosponsor_id = %s
            GROUP BY b.bill_number, b.bill_title, b.introduced_date,
                     b.status, b.normalized_status, b.congress,
                     b.latest_action, b.latest_action_date,
                     m_sponsor.full_name, m_sponsor.party
            ORDER BY b.introduced_date DESC
        """, (bioguide_id,))
        representative['cosponsored_bills'] = cur.fetchall()
    
    cur.close()
    conn.close()
    
    if representative is None:
        return jsonify({'error': 'Representative not found'}), 404
        
    return jsonify(representative)

@app.route('/api/tags', methods=['GET'])
def get_tags():
    """Get all available tags with their types"""
    logging.info("GET /api/tags - Starting request")
    conn = None
    cur = None
    try:
        logging.info("GET /api/tags - Getting database connection")
        conn = get_db_connection()
        logging.info("GET /api/tags - Creating cursor")
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all tags with their types
        query = """
            SELECT t.id, t.name, t.normalized_name, t.parent_id, t.description,
                   tt.name as type, tt.id as type_id
            FROM tags t
            JOIN tag_types tt ON t.type_id = tt.id
            ORDER BY tt.name, t.name
        """
        logging.info(f"GET /api/tags - Executing query: {query}")
        cur.execute(query)
        
        logging.info("GET /api/tags - Fetching results")
        tags = cur.fetchall()
        logging.info(f"GET /api/tags - Found {len(tags)} tags")
        
        # Build hierarchical structure
        logging.info("GET /api/tags - Building hierarchical structure")
        tag_map = {}
        for tag in tags:
            tag['children'] = []
            tag_map[tag['id']] = tag
        logging.info(f"GET /api/tags - Created tag map with {len(tag_map)} entries")
        
        # Organize tags into hierarchy
        logging.info("GET /api/tags - Organizing tags into hierarchy")
        root_tags = []
        for tag in tags:
            if tag['parent_id'] is None:
                root_tags.append(tag)
            else:
                parent = tag_map.get(tag['parent_id'])
                if parent:
                    parent['children'].append(tag)
        logging.info(f"GET /api/tags - Found {len(root_tags)} root tags")
        
        logging.info(f"GET /api/tags - Found {len(root_tags)} root tags")
        return jsonify({'tags': root_tags})
    except Exception as e:
        logging.error(f"GET /api/tags - Error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

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
    logging.info("GET /api/bills - Fetching bills with filters")
    # Get filter and pagination parameters
    bill_number = request.args.get('bill_number', '')
    bill_title = request.args.get('bill_title', '')
    status = request.args.get('status', '')
    sponsor = request.args.get('sponsor', '')
    congress = request.args.get('congress', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))

    # Parse tag filters
    tag_operator = request.args.get('tag_operator', '')
    tags = []
    try:
        tags_str = request.args.get('tags', '[]')
        logging.info(f"GET /api/bills - Raw tags parameter: {tags_str}")
        tags = json.loads(tags_str)
        logging.info(f"GET /api/bills - Parsed tags: {tags}")
    except json.JSONDecodeError as e:
        logging.error(f"GET /api/bills - Failed to parse tags: {e}")

    # Calculate offset
    offset = (page - 1) * per_page

    # Build the WHERE clause dynamically
    where_clauses = []
    params = []

    if request.args.get('date_from'):
        where_clauses.append("DATE(b.introduced_date) >= %s")
        params.append(request.args.get('date_from'))
    
    if request.args.get('date_to'):
        where_clauses.append("DATE(b.introduced_date) <= %s")
        params.append(request.args.get('date_to'))

    if bill_number:
        where_clauses.append("LOWER(b.bill_number) LIKE LOWER(%s)")
        params.append(f"%{bill_number}%")
    
    if bill_title:
        where_clauses.append("LOWER(b.bill_title) LIKE LOWER(%s)")
        params.append(f"%{bill_title}%")
    
    if status:
        where_clauses.append("b.normalized_status = %s")
        params.append(status)
    
    if sponsor:
        where_clauses.append("(LOWER(m.full_name) LIKE LOWER(%s) OR LOWER(b.sponsor_id) LIKE LOWER(%s))")
        params.extend([f"%{sponsor}%", f"%{sponsor}%"])
    
    # Handle tag filtering
    if tags and tag_operator:
        tag_ids = [str(tag['id']) for tag in tags]
        logging.info(f"GET /api/bills - Tag IDs: {tag_ids}, Operator: {tag_operator}")
        if tag_ids:
            if tag_operator == 'is':
                # Must have exactly these tags
                where_clauses.append("""
                    EXISTS (
                        SELECT 1 FROM bill_tags bt 
                        WHERE bt.bill_id = b.id AND bt.tag_id = %s
                    )
                """)
                params.append(int(tag_ids[0]))  # 'is' operator only uses first tag
            elif tag_operator == 'is_not':
                # Must not have this tag
                where_clauses.append("""
                    NOT EXISTS (
                        SELECT 1 FROM bill_tags bt 
                        WHERE bt.bill_id = b.id AND bt.tag_id = %s
                    )
                """)
                params.append(int(tag_ids[0]))  # 'is_not' operator only uses first tag
            elif tag_operator == 'is_one_of':
                # Must have at least one of these tags
                where_clauses.append("""
                    EXISTS (
                        SELECT 1 FROM bill_tags bt 
                        WHERE bt.bill_id = b.id AND bt.tag_id = ANY(%s)
                    )
                """)
                params.append([int(id) for id in tag_ids])
            elif tag_operator == 'is_not_one_of':
                # Must not have any of these tags
                where_clauses.append("""
                    NOT EXISTS (
                        SELECT 1 FROM bill_tags bt 
                        WHERE bt.bill_id = b.id AND bt.tag_id = ANY(%s)
                    )
                """)
                params.append([int(id) for id in tag_ids])
    
    if congress:
        where_clauses.append("b.congress = %s")
        params.append(congress)

    # Base WHERE clause for both count and data queries
    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    logging.info(f"GET /api/bills - WHERE clause: {where_sql}")
    logging.info(f"GET /api/bills - Parameters: {params}")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get total count
    count_query = """
        SELECT COUNT(DISTINCT b.id) 
        FROM bills b
        LEFT JOIN members m ON b.sponsor_id = m.bioguide_id
    """ + where_sql

    cur.execute(count_query, params)
    total_count = cur.fetchone()['count']

    # Get sort parameters
    sort_key = request.args.get('sort_key', 'introduced_date')
    sort_direction = request.args.get('sort_direction', 'desc')

    # Map frontend sort keys to SQL columns
    sort_column_map = {
        'bill_number': 'b.bill_number',
        'bill_title': 'b.bill_title',
        'sponsor': 'COALESCE(m.full_name, \'\')',  # Handle NULL sponsors
        'introduced_date': 'b.introduced_date',
        'status': 'b.status',
        'congress': 'b.congress',
        'tags': 'tags'
    }

    # Get the SQL column name, defaulting to introduced_date if invalid key
    sort_column = sort_column_map.get(sort_key, 'b.introduced_date')
    
    # Validate sort direction
    if sort_direction not in ['asc', 'desc']:
        sort_direction = 'desc'

    data_query = """
        SELECT DISTINCT ON (b.id) b.id, b.bill_number, b.bill_title, b.sponsor_id, 
               m.full_name as sponsor_name, m.party as sponsor_party,
               b.introduced_date, b.status, b.congress,
               b.latest_action, b.latest_action_date,
               COALESCE(
                   jsonb_agg(
                       DISTINCT jsonb_build_object(
                           'id', t.id,
                           'name', t.name,
                           'normalized_name', t.normalized_name,
                           'type', tt.name,
                           'type_id', tt.id
                       )
                   ) FILTER (WHERE t.id IS NOT NULL),
                   '[]'::jsonb
               ) as tags
        FROM bills b
        LEFT JOIN members m ON b.sponsor_id = m.bioguide_id
        LEFT JOIN bill_tags bt ON b.id = bt.bill_id
        LEFT JOIN tags t ON bt.tag_id = t.id
        LEFT JOIN tag_types tt ON t.type_id = tt.id
    """ + where_sql + f"""
        GROUP BY b.id, b.bill_number, b.bill_title, b.sponsor_id, 
                 m.full_name, m.party, b.introduced_date, b.status,
                 b.congress, b.latest_action, b.latest_action_date
        ORDER BY b.id, {sort_column} {sort_direction.upper()} NULLS LAST
        LIMIT %s OFFSET %s
    """

    # Add pagination parameters
    cur.execute(data_query, params + [per_page, offset])
    bills = cur.fetchall()
    
    cur.close()
    conn.close()

    result = {
        'bills': bills,
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': (total_count + per_page - 1) // per_page
    }
    logging.info(f"GET /api/bills - Found {total_count} bills")
    return jsonify(result)

@app.route('/api/analytics/bills-by-status', methods=['GET'])
def get_bills_by_status():
    """Get the distribution of bills across different status categories"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get optional congress filter from query params
    congress = request.args.get('congress')
    
    # Base query
    query = """
        SELECT 
            normalized_status as status,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
        FROM bills
    """
    
    params = []
    if congress:
        query += " WHERE congress = %s"
        params.append(congress)
    
    query += """
        GROUP BY normalized_status
        ORDER BY count DESC
    """
    
    cur.execute(query, params)
    results = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify(results)

@app.route('/api/analytics/passage-time', methods=['GET'])
def get_passage_time_analytics():
    """Get analytics about bill passage time through different stages"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get optional congress filter from query params
    congress = request.args.get('congress')
    
    # Base query conditions
    where_clauses = ["b.introduced_date IS NOT NULL", "b.latest_action_date IS NOT NULL"]
    params = []
    if congress:
        where_clauses.append("b.congress = %s")
        params.append(congress)

    where_clause = "WHERE " + " AND ".join(where_clauses)

    # Calculate overall passage time statistics
    cur.execute(f"""
        WITH bill_timelines AS (
            SELECT 
                b.bill_number,
                b.introduced_date,
                b.latest_action_date,
                EXTRACT(DAY FROM (b.latest_action_date::timestamp - b.introduced_date::timestamp)) as total_days,
                b.status,
                b.normalized_status
            FROM bills b
            {where_clause}
        )
        SELECT 
            COUNT(*) as total_bills,
            ROUND(AVG(total_days)) as avg_days,
            MIN(total_days) as min_days,
            MAX(total_days) as max_days,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_days)) as median_days
        FROM bill_timelines
    """, params)
    
    overall_stats = cur.fetchone()

    # Calculate time spent in each stage
    cur.execute(f"""
        WITH stage_durations AS (
            SELECT 
                b.bill_number,
                a1.action_date as stage_start,
                LEAD(a1.action_date::timestamp) OVER (PARTITION BY b.bill_number ORDER BY a1.action_date) as stage_end,
                a1.action_type as stage_name
            FROM bills b
            JOIN bill_actions a1 ON b.bill_number = a1.bill_number
            {where_clause}
        )
        SELECT 
            stage_name,
            COUNT(*) as bills_in_stage,
            ROUND(AVG(EXTRACT(DAY FROM (stage_end::timestamp - stage_start::timestamp)))) as avg_days_in_stage
        FROM stage_durations
        WHERE stage_end IS NOT NULL
        GROUP BY stage_name
        ORDER BY avg_days_in_stage DESC
    """, params)
    
    stage_analysis = cur.fetchall()

    # Get bills with longest processing times
    cur.execute(f"""
        SELECT 
            b.bill_number,
            b.bill_title,
            b.introduced_date,
            b.latest_action_date,
            b.status,
            EXTRACT(DAY FROM (b.latest_action_date::timestamp - b.introduced_date::timestamp)) as days_to_process
        FROM bills b
        {where_clause}
        ORDER BY (b.latest_action_date - b.introduced_date) DESC
        LIMIT 10
    """, params)
    
    outliers = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify({
        'overall_statistics': overall_stats,
        'stage_analysis': stage_analysis,
        'outliers': outliers
    })

@app.route('/api/analytics/bills-per-congress', methods=['GET'])
def get_bills_per_congress():
    """Get the distribution of bills across congressional sessions"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT 
            congress,
            CASE 
                WHEN status LIKE 'Referred to%' OR status LIKE '%Committee%' OR status = 'Reported' THEN 'In Committee'
                WHEN status LIKE '%passed%' OR status LIKE '%Passed%' OR status LIKE '%agreed to%' OR status LIKE '%Agreed to%' THEN 'Passed Chamber'
                WHEN status LIKE '%conference%' OR status LIKE '%Conference%' OR status = 'Resolving Differences' THEN 'Resolving Differences'
                WHEN status LIKE '%President%' OR status = 'To President' THEN 'To President'
                WHEN status = 'Became Law' OR status LIKE '%enacted%' OR status LIKE '%Enacted%' THEN 'Became Law'
                WHEN status = 'Failed' OR status LIKE '%failed%' OR status LIKE '%Failed%' OR status LIKE '%rejected%' OR status LIKE '%Rejected%' THEN 'Failed'
                ELSE 'Other'
            END as status,
            COUNT(*) as bill_count
        FROM bills
        GROUP BY 
            congress,
            CASE 
                WHEN status LIKE 'Referred to%' OR status LIKE '%Committee%' OR status = 'Reported' THEN 'In Committee'
                WHEN status LIKE '%passed%' OR status LIKE '%Passed%' OR status LIKE '%agreed to%' OR status LIKE '%Agreed to%' THEN 'Passed Chamber'
                WHEN status LIKE '%conference%' OR status LIKE '%Conference%' OR status = 'Resolving Differences' THEN 'Resolving Differences'
                WHEN status LIKE '%President%' OR status = 'To President' THEN 'To President'
                WHEN status = 'Became Law' OR status LIKE '%enacted%' OR status LIKE '%Enacted%' THEN 'Became Law'
                WHEN status = 'Failed' OR status LIKE '%failed%' OR status LIKE '%Failed%' OR status LIKE '%rejected%' OR status LIKE '%Rejected%' THEN 'Failed'
                ELSE 'Other'
            END
        ORDER BY congress DESC, bill_count DESC
    """)
    
    results = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify(results)

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
