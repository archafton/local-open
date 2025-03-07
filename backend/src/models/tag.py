import logging
from utils.database import get_db_cursor
from utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)

def get_all_tags():
    """
    Get all available tags organized in a hierarchical structure
    
    Returns:
        list: List of tag dictionaries organized in a hierarchy
        
    Raises:
        DatabaseError: If a database error occurs
    """
    logger.info("Getting all tags")
    try:
        with get_db_cursor() as cur:
            # Get all tags with their types
            query = """
                SELECT t.id, t.name, t.normalized_name, t.parent_id, t.description,
                       tt.name as type, tt.id as type_id
                FROM tags t
                JOIN tag_types tt ON t.type_id = tt.id
                ORDER BY tt.name, t.name
            """
            cur.execute(query)
            
            tags = cur.fetchall()
            logger.info(f"Found {len(tags)} tags")
            
            # Build hierarchical structure
            tag_map = {}
            for tag in tags:
                tag['children'] = []
                tag_map[tag['id']] = tag
            
            # Organize tags into hierarchy
            root_tags = []
            for tag in tags:
                if tag['parent_id'] is None:
                    root_tags.append(tag)
                else:
                    parent = tag_map.get(tag['parent_id'])
                    if parent:
                        parent['children'].append(tag)
            
            return root_tags
    except Exception as e:
        logger.error(f"Error getting tags: {str(e)}")
        raise DatabaseError(f"Error retrieving tags: {str(e)}")
