import logging
from utils.database import get_db_cursor
from utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)

def get_bills_by_status(congress=None):
    """
    Get the distribution of bills across different status categories
    
    Args:
        congress (str, optional): Filter by congress number
        
    Returns:
        list: List of status counts and percentages
        
    Raises:
        DatabaseError: If a database error occurs
    """
    try:
        with get_db_cursor() as cur:
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
            
            return results
    except Exception as e:
        logger.error(f"Error in get_bills_by_status: {str(e)}")
        raise DatabaseError(f"Error retrieving bill status analytics: {str(e)}")

def get_passage_time_analytics(congress=None):
    """
    Get analytics about bill passage time through different stages
    
    Args:
        congress (str, optional): Filter by congress number
        
    Returns:
        dict: Dictionary with overall statistics, stage analysis, and outliers
        
    Raises:
        DatabaseError: If a database error occurs
    """
    try:
        with get_db_cursor() as cur:
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
            
            return {
                'overall_statistics': overall_stats,
                'stage_analysis': stage_analysis,
                'outliers': outliers
            }
    except Exception as e:
        logger.error(f"Error in get_passage_time_analytics: {str(e)}")
        raise DatabaseError(f"Error retrieving passage time analytics: {str(e)}")

def get_bills_per_congress():
    """
    Get the distribution of bills across congressional sessions
    
    Returns:
        list: List of bill counts per congress and status
        
    Raises:
        DatabaseError: If a database error occurs
    """
    try:
        with get_db_cursor() as cur:
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
            return results
    except Exception as e:
        logger.error(f"Error in get_bills_per_congress: {str(e)}")
        raise DatabaseError(f"Error retrieving bills per congress analytics: {str(e)}")
