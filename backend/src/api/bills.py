from flask import jsonify, request
import json
import logging
from api import bp
from models.bill import get_bills, get_bill_detail, get_all_congresses
from utils.helpers import get_pagination_params, get_sort_params
from utils.exceptions import ResourceNotFoundError, DatabaseError, ValidationError

logger = logging.getLogger(__name__)

@bp.route('/bills/congresses', methods=['GET'])
def congresses():
    """
    Get list of all congresses with bills
    
    Returns:
        JSON response with list of congress numbers
    """
    try:
        congresses = get_all_congresses()
        return jsonify(congresses)
    except DatabaseError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in congresses endpoint: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@bp.route('/bills', methods=['GET'])
def bills():
    """
    Get all bills with filtering and pagination
    
    Query parameters:
        bill_number (str): Filter by bill number (partial match)
        bill_title (str): Filter by bill title (partial match)
        status (str): Filter by normalized status
        sponsor (str): Filter by sponsor name or ID (partial match)
        congress (str): Filter by congress number
        date_from (str): Filter by introduced date (from)
        date_to (str): Filter by introduced date (to)
        tag_operator (str): Tag filter operator ('is', 'is_not', 'is_one_of', 'is_not_one_of')
        tags (str): JSON string of tag objects with IDs
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 100)
        sort_key (str): Field to sort by (default: 'introduced_date')
        sort_direction (str): Sort direction ('asc' or 'desc', default: 'desc')
        
    Returns:
        JSON response with bills data and pagination info
    """
    logger.info("Fetching bills with filters")
    
    try:
        # Parse tag filters
        tag_operator = request.args.get('tag_operator', '')
        tags = []
        try:
            tags_str = request.args.get('tags', '[]')
            logger.info(f"Raw tags parameter: {tags_str}")
            tags = json.loads(tags_str)
            logger.info(f"Parsed tags: {tags}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tags: {e}")
            raise ValidationError(f"Invalid tags format: {e}")
        
        # Get filter parameters
        filters = {
            'bill_number': request.args.get('bill_number', ''),
            'bill_title': request.args.get('bill_title', ''),
            'status': request.args.get('status', ''),
            'sponsor': request.args.get('sponsor', ''),
            'congress': request.args.get('congress', ''),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'tag_operator': tag_operator,
            'tags': tags
        }
        
        # Validate date format if provided
        for date_param in ['date_from', 'date_to']:
            if filters[date_param] and not is_valid_date(filters[date_param]):
                raise ValidationError(f"Invalid date format for {date_param}. Use YYYY-MM-DD format.")
        
        # Get sort parameters
        sort_params = get_sort_params(
            allowed_keys=['bill_number', 'bill_title', 'sponsor', 'introduced_date', 'status', 'congress'],
            default_key='introduced_date',
            default_direction='desc'
        )
        
        # Get pagination parameters
        pagination = get_pagination_params(default_per_page=100, max_per_page=500)
        
        # Get bills
        result = get_bills(filters, sort_params, pagination)
        
        # Rename 'items' to 'bills' for backward compatibility
        result['bills'] = result.pop('items')
        
        logger.info(f"Found {result['total']} bills")
        return jsonify(result)
    except ValidationError as e:
        return jsonify(e.to_dict()), e.status_code
    except DatabaseError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in bills endpoint: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@bp.route('/bills/<bill_number>', methods=['GET'])
def bill_details(bill_number):
    """
    Get detailed information about a specific bill
    
    Path parameters:
        bill_number (str): The bill number
        
    Returns:
        JSON response with bill details
    """
    try:
        bill = get_bill_detail(bill_number)
        return jsonify(bill)
    except ResourceNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except DatabaseError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in bill_details endpoint: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

def is_valid_date(date_str):
    """
    Validate date string format (YYYY-MM-DD)
    
    Args:
        date_str (str): Date string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    import re
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', date_str))
