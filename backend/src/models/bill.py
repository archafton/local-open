import json
import logging
from utils.database import get_db_cursor
from utils.helpers import parse_json_field, build_pagination_result, serialize_dates
from utils.exceptions import ResourceNotFoundError, DatabaseError

logger = logging.getLogger(__name__)

def get_all_congresses():
    """
    Get list of all congresses with bills
    
    Returns:
        list: List of congress numbers
        
    Raises:
        DatabaseError: If a database error occurs
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT DISTINCT congress 
                FROM bills 
                WHERE congress IS NOT NULL 
                ORDER BY congress DESC
            """)
            congresses = [row['congress'] for row in cur.fetchall()]
            return congresses
    except Exception as e:
        logger.error(f"Error in get_all_congresses: {str(e)}")
        raise DatabaseError(f"Error retrieving congresses: {str(e)}")

def get_bills(filters, sort_params, pagination):
    """
    Get bills with filtering, sorting, and pagination
    
    Args:
        filters (dict): Dictionary of filter parameters
        sort_params (dict): Dictionary with sort_key and sort_direction
        pagination (dict): Dictionary with page and per_page
    
    Returns:
        dict: Dictionary with bills data and pagination info
    
    Raises:
        DatabaseError: If a database error occurs
    """
    logger.info("Getting bills with filters")
    
    try:
        # Extract filter parameters
        bill_number = filters.get('bill_number', '')
        bill_title = filters.get('bill_title', '')
        status = filters.get('status', '')
        sponsor = filters.get('sponsor', '')
        congress = filters.get('congress', '')
        date_from = filters.get('date_from')
        date_to = filters.get('date_to')
        tag_operator = filters.get('tag_operator', '')
        tags = filters.get('tags', [])
        
        # Extract pagination parameters
        page = pagination.get('page', 1)
        per_page = pagination.get('per_page', 100)
        offset = (page - 1) * per_page

        # Extract sort parameters
        sort_key = sort_params.get('sort_key', 'introduced_date')
        sort_direction = sort_params.get('sort_direction', 'desc')

        # Map frontend sort keys to SQL columns
        sort_column_map = {
            'bill_number': 'b.bill_number',
            'bill_title': 'b.bill_title',
            'sponsor': 'COALESCE(m.full_name, \'\')',
            'introduced_date': 'b.introduced_date',
            'status': 'b.status',
            'congress': 'b.congress'
        }

        # Get the SQL column name
        sort_column = sort_column_map.get(sort_key, 'b.introduced_date')
        
        # Validate sort direction
        if sort_direction not in ['asc', 'desc']:
            sort_direction = 'desc'

        # Build the WHERE clause dynamically
        where_clauses = []
        params = []

        if date_from:
            where_clauses.append("DATE(b.introduced_date) >= %s")
            params.append(date_from)
        
        if date_to:
            where_clauses.append("DATE(b.introduced_date) <= %s")
            params.append(date_to)

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
            logger.info(f"Tag IDs: {tag_ids}, Operator: {tag_operator}")
            if tag_ids:
                if tag_operator == 'is':
                    # Must have exactly this tag
                    where_clauses.append("""
                        EXISTS (
                            SELECT 1 FROM bill_tags bt 
                            WHERE bt.bill_id = b.id AND bt.tag_id = %s
                        )
                    """)
                    params.append(int(tag_ids[0]))
                elif tag_operator == 'is_not':
                    # Must not have this tag
                    where_clauses.append("""
                        NOT EXISTS (
                            SELECT 1 FROM bill_tags bt 
                            WHERE bt.bill_id = b.id AND bt.tag_id = %s
                        )
                    """)
                    params.append(int(tag_ids[0]))
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

        # Base WHERE clause
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        logger.info(f"WHERE clause: {where_sql}")

        with get_db_cursor() as cur:
            # Get total count
            count_query = f"""
                SELECT COUNT(DISTINCT b.id) 
                FROM bills b
                LEFT JOIN members m ON b.sponsor_id = m.bioguide_id
                {where_sql}
            """

            cur.execute(count_query, params)
            total_count = cur.fetchone()['count']

            # Get paginated data with tags
            data_query = f"""
                SELECT b.id, b.bill_number, b.bill_title, b.sponsor_id, 
                       m.full_name as sponsor_name, m.party as sponsor_party,
                       b.introduced_date, b.status, b.congress,
                       b.latest_action, b.latest_action_date,
                       COALESCE(
                           array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL),
                           ARRAY[]::text[]
                       ) as tags
                FROM bills b
                LEFT JOIN members m ON b.sponsor_id = m.bioguide_id
                LEFT JOIN bill_tags bt ON b.id = bt.bill_id
                LEFT JOIN tags t ON bt.tag_id = t.id
                {where_sql}
                GROUP BY b.id, b.bill_number, b.bill_title, b.sponsor_id, 
                         m.full_name, m.party, b.introduced_date, b.status,
                         b.congress, b.latest_action, b.latest_action_date
                ORDER BY {sort_column} {sort_direction.upper()} NULLS LAST
                LIMIT %s OFFSET %s
            """

            # Add pagination parameters
            cur.execute(data_query, params + [per_page, offset])
            bills = cur.fetchall()
            
            # Serialize dates
            date_fields = ['introduced_date', 'latest_action_date']
            bills = serialize_dates(bills, date_fields)

        # Build pagination result
        return build_pagination_result(
            items=bills,
            total_count=total_count,
            page=page,
            per_page=per_page
        )
    except Exception as e:
        logger.error(f"Error in get_bills: {str(e)}")
        raise DatabaseError(f"Error retrieving bills: {str(e)}")

def get_bill_detail(bill_number):
    """
    Get detailed information about a specific bill
    
    Args:
        bill_number (str): The bill number
        
    Returns:
        dict: Bill details with related data
        
    Raises:
        ResourceNotFoundError: If the bill is not found
        DatabaseError: If a database error occurs
    """
    try:
        with get_db_cursor() as cur:
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
            
            if not bill:
                raise ResourceNotFoundError("Bill", bill_number)
            
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
            bill = serialize_dates(bill, ['introduced_date', 'latest_action_date'])
            bill['actions'] = serialize_dates(bill['actions'], ['action_date'])

            # Handle JSON fields
            bill['summary'] = parse_json_field(bill['summary'], [])
            bill['text_versions'] = parse_json_field(bill['text_versions'], [])
            
            return bill
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error in get_bill_detail: {str(e)}")
        raise DatabaseError(f"Error retrieving bill details: {str(e)}")
