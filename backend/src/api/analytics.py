from flask import jsonify, request
import logging
from api import bp
from models.analytics import get_bills_by_status, get_passage_time_analytics, get_bills_per_congress
from utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)

@bp.route('/analytics/bills-by-status', methods=['GET'])
def bills_by_status():
    """Get the distribution of bills across different status categories"""
    try:
        # Get optional congress filter from query params
        congress = request.args.get('congress')
        results = get_bills_by_status(congress)
        return jsonify(results)
    except DatabaseError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in bills_by_status endpoint: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@bp.route('/analytics/passage-time', methods=['GET'])
def passage_time_analytics():
    """Get analytics about bill passage time through different stages"""
    try:
        # Get optional congress filter from query params
        congress = request.args.get('congress')
        results = get_passage_time_analytics(congress)
        return jsonify(results)
    except DatabaseError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in passage_time_analytics endpoint: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@bp.route('/analytics/bills-per-congress', methods=['GET'])
def bills_per_congress():
    """Get the distribution of bills across congressional sessions"""
    try:
        results = get_bills_per_congress()
        return jsonify(results)
    except DatabaseError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in bills_per_congress endpoint: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500
