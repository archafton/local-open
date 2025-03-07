import logging
import requests
from utils.database import get_db_cursor, transaction
from utils.helpers import serialize_dates, build_filter_clause, build_pagination_result
from utils.exceptions import ResourceNotFoundError, DatabaseError

logger = logging.getLogger(__name__)

def get_representatives(filters, sort_params, pagination):
    """
    Get representatives with filtering, sorting, and pagination
    
    Args:
        filters (dict): Dictionary of filter parameters
        sort_params (dict): Dictionary with sort_key and sort_direction
        pagination (dict): Dictionary with page and per_page
    
    Returns:
        dict: Dictionary with representatives data and pagination info
    
    Raises:
        DatabaseError: If a database error occurs
    """
    try:
        # Extract filter parameters
        filter_dict = {
            'full_name': filters.get('full_name', '') if filters.get('full_name') else None,
            'chamber': filters.get('chamber', ''),
            'party': filters.get('party', ''),
            'leadership_role': filters.get('leadership_role', '') if filters.get('leadership_role') else None,
            'state': filters.get('state', '') if filters.get('state') else None,
            'district': filters.get('district', '')
        }
        
        # Add wildcards to string fields for LIKE queries
        if filter_dict['full_name']:
            filter_dict['full_name'] = f"%{filter_dict['full_name']}%"
        if filter_dict['leadership_role']:
            filter_dict['leadership_role'] = f"%{filter_dict['leadership_role']}%"
        if filter_dict['state']:
            filter_dict['state'] = f"%{filter_dict['state']}%"
        
        # Add current_member filter
        base_filters = {"current_member": True}
        
        # Extract pagination parameters
        page = pagination.get('page', 1)
        per_page = pagination.get('per_page', 100)
        offset = (page - 1) * per_page

        # Extract sort parameters
        sort_key = sort_params.get('sort_key', 'full_name')
        sort_direction = sort_params.get('sort_direction', 'asc')

        # Map frontend sort keys to SQL columns
        sort_column_map = {
            'full_name': 'full_name',
            'chamber': 'chamber',
            'party': 'party',
            'leadership_role': 'COALESCE(leadership_role, \'\')',
            'state': 'state',
            'district': 'COALESCE(district, \'\')',
            'total_votes': 'COALESCE(total_votes, 0)',
            'missed_votes': 'COALESCE(missed_votes, 0)',
            'total_present': 'COALESCE(total_present, 0)'
        }

        # Get the SQL column name, defaulting to full_name if invalid key
        sort_column = sort_column_map.get(sort_key, 'full_name')
        
        # Validate sort direction
        if sort_direction not in ['asc', 'desc']:
            sort_direction = 'asc'

        # Debug log chamber values
        with get_db_cursor() as cur:
            # Log the chamber value for debugging
            logger.info(f"Chamber filter value: '{filter_dict['chamber']}'")

            # Get unique chamber values from database for debugging
            cur.execute("SELECT DISTINCT chamber FROM members WHERE current_member = true ORDER BY chamber")
            unique_chambers = [row['chamber'] for row in cur.fetchall()]
            logger.info(f"Unique chamber values in database: {unique_chambers}")

            # If filtering by House, try both variations
            if filter_dict['chamber'] == 'House Of Representatives':
                cur.execute("SELECT COUNT(*) FROM members WHERE current_member = true AND chamber = 'House'")
                house_count = cur.fetchone()['count']
                cur.execute("SELECT COUNT(*) FROM members WHERE current_member = true AND chamber = 'House Of Representatives'")
                house_of_reps_count = cur.fetchone()['count']
                logger.info(f"Found {house_count} members with chamber='House' and {house_of_reps_count} with chamber='House Of Representatives'")
        
            # Build WHERE clause and parameters
            where_clause, params = build_filter_clause(base_filters)
            
            # Add custom filters
            custom_clauses = []
            
            if filter_dict['full_name']:
                custom_clauses.append("LOWER(full_name) LIKE LOWER(%s)")
                params.append(filter_dict['full_name'])
            
            if filter_dict['chamber']:
                custom_clauses.append("chamber = %s")
                params.append(filter_dict['chamber'])
            
            if filter_dict['party']:
                custom_clauses.append("party = %s")
                params.append(filter_dict['party'])
            
            if filter_dict['leadership_role']:
                custom_clauses.append("LOWER(leadership_role) LIKE LOWER(%s)")
                params.append(filter_dict['leadership_role'])
            
            if filter_dict['state']:
                custom_clauses.append("LOWER(state) LIKE LOWER(%s)")
                params.append(filter_dict['state'])
            
            if filter_dict['district']:
                custom_clauses.append("district = %s")
                params.append(filter_dict['district'])
            
            # Add custom clauses to WHERE clause
            if custom_clauses:
                where_clause += " AND " + " AND ".join(custom_clauses)

            # Get total count
            count_query = f"SELECT COUNT(*) FROM members {where_clause}"
            cur.execute(count_query, params)
            total_count = cur.fetchone()['count']

            # Get paginated data with sorting
            data_query = f"""
                SELECT chamber, full_name, party, leadership_role, state, district, 
                       total_votes, missed_votes, total_present, bioguide_id 
                FROM members
                {where_clause}
                ORDER BY {sort_column} {sort_direction.upper()} NULLS LAST
                LIMIT %s OFFSET %s
            """

            # Add pagination parameters
            cur.execute(data_query, params + [per_page, offset])
            representatives = cur.fetchall()

        # Build pagination result
        return build_pagination_result(
            items=representatives,
            total_count=total_count,
            page=page,
            per_page=per_page
        )
    except Exception as e:
        logger.error(f"Error in get_representatives: {str(e)}")
        raise DatabaseError(f"Error retrieving representatives: {str(e)}")

def get_representative_detail(bioguide_id):
    """
    Get detailed information about a specific representative
    
    Args:
        bioguide_id (str): The bioguide ID of the representative
        
    Returns:
        dict: Representative details with related data
        
    Raises:
        ResourceNotFoundError: If the representative is not found
        DatabaseError: If a database error occurs
    """
    try:
        with get_db_cursor() as cur:
            # Get representative details including committees
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
            
            if not representative:
                raise ResourceNotFoundError("Representative", bioguide_id)
            
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
            
            # Serialize dates for JSON response
            date_fields = ['introduced_date', 'latest_action_date']
            representative['sponsored_bills'] = serialize_dates(representative['sponsored_bills'], date_fields)
            representative['cosponsored_bills'] = serialize_dates(representative['cosponsored_bills'], date_fields)
            
            return representative
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error in get_representative_detail: {str(e)}")
        raise DatabaseError(f"Error retrieving representative details: {str(e)}")

def get_representative_bio(bioguide_id):
    """
    Fetch biography from bioguide.congress.gov
    
    Args:
        bioguide_id (str): The bioguide ID of the representative
        
    Returns:
        dict: Biography information
        
    Raises:
        ResourceNotFoundError: If the biography is not found
    """
    url = f"https://bioguide.congress.gov/search/bio/{bioguide_id}.json"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            'biography': data.get('profileText', 'Biography not available')
        }
    except requests.RequestException as e:
        logger.warning(f"Error fetching biography for {bioguide_id}: {str(e)}")
        raise ResourceNotFoundError("Biography", bioguide_id, 
                                   payload={"details": str(e)})
