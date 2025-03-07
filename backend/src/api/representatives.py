from flask import jsonify, request
import logging
from api import bp
from models.representative import get_representatives, get_representative_detail, get_representative_bio
from utils.helpers import get_pagination_params, get_sort_params
from utils.exceptions import ResourceNotFoundError, DatabaseError

logger = logging.getLogger(__name__)

@bp.route('/representatives', methods=['GET'])
def representatives():
    """
    Get all representatives with filtering and pagination
    
    Query parameters:
        full_name (str): Filter by representative name (partial match)
        chamber (str): Filter by chamber ('Senate' or 'House')
        party (str): Filter by party code
        leadership_role (str): Filter by leadership role (partial match)
        state (str): Filter by state (partial match)
        district (str): Filter by district number
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 100)
        sort_key (str): Field to sort by (default: 'full_name')
        sort_direction (str): Sort direction ('asc' or 'desc', default: 'asc')
        
    Returns:
        JSON response with representatives data and pagination info
    """
    logger.info("Fetching representatives with filters")
    
    try:
        # Get filter parameters
        filters = {
            'full_name': request.args.get('full_name', ''),
            'chamber': request.args.get('chamber', ''),
            'party': request.args.get('party', ''),
            'leadership_role': request.args.get('leadership_role', ''),
            'state': request.args.get('state', ''),
            'district': request.args.get('district', '')
        }
        
        # Get sort parameters
        sort_params = get_sort_params(
            allowed_keys=['full_name', 'chamber', 'party', 'leadership_role', 'state', 'district', 
                          'total_votes', 'missed_votes', 'total_present'],
            default_key='full_name',
            default_direction='asc'
        )
        
        # Get pagination parameters
        pagination = get_pagination_params(default_per_page=100, max_per_page=500)
        
        # Get representatives
        result = get_representatives(filters, sort_params, pagination)
        
        # Rename 'items' to 'representatives' for backward compatibility
        result['representatives'] = result.pop('items')
        
        # Return JSON response
        return jsonify(result)
    except DatabaseError as e:
        logger.error(f"Database error in representatives endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in representatives endpoint: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@bp.route('/representatives/<bioguide_id>', methods=['GET'])
def representative_details(bioguide_id):
    """
    Get detailed information about a specific representative
    
    Path parameters:
        bioguide_id (str): The bioguide ID of the representative
        
    Returns:
        JSON response with representative details
    """
    logger.info(f"Fetching details for representative {bioguide_id}")
    
    try:
        # Get representative details
        representative = get_representative_detail(bioguide_id)
        
        # Return JSON response
        return jsonify(representative)
    except ResourceNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except DatabaseError as e:
        logger.error(f"Database error in representative_details endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in representative_details endpoint: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@bp.route('/representatives/<bioguide_id>/bio', methods=['GET'])
def representative_bio(bioguide_id):
    """
    Fetch biography from bioguide.congress.gov
    
    Path parameters:
        bioguide_id (str): The bioguide ID of the representative
        
    Returns:
        JSON response with biography information
    """
    logger.info(f"Fetching biography for representative {bioguide_id}")
    
    try:
        # Get representative biography
        bio_info = get_representative_bio(bioguide_id)
        
        # Return JSON response
        return jsonify(bio_info)
    except ResourceNotFoundError as e:
        return jsonify({'biography': 'Biography not available', 'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Unexpected error in representative_bio endpoint: {str(e)}")
        return jsonify({'biography': 'Biography not available', 'error': str(e)}), 500
