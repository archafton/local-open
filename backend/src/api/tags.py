from flask import jsonify
import logging
from api import bp
from models.tag import get_all_tags
from utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)

@bp.route('/tags', methods=['GET'])
def tags():
    """Get all available tags with their types"""
    logging.info("GET /api/tags - Starting request")
    try:
        tags = get_all_tags()
        logging.info(f"GET /api/tags - Found {len(tags)} root tags")
        return jsonify({'tags': tags})
    except Exception as e:
        logging.error(f"GET /api/tags - Error: {str(e)}")
        return jsonify({'error': str(e)}), 500
