"""
Tag-related utilities for bill categorization.
"""

import logging
from typing import Optional

# Set up logging
logger = logging.getLogger(__name__)

def normalize_tag_name(name: str) -> Optional[str]:
    """
    Convert a tag name to its normalized form.
    
    Args:
        name: Tag name
        
    Returns:
        Normalized tag name or None if input is None
    """
    if not name:
        return None
    return name.lower().replace(' ', '_').replace(',', '_').replace('&', 'and').replace('-', '_')

def get_or_create_policy_area_tag(cur, policy_area_name: str) -> Optional[int]:
    """
    Get or create a policy area tag, ensuring it exists in the hierarchical tag system.
    
    Args:
        cur: Database cursor
        policy_area_name: Name of the policy area
        
    Returns:
        Tag ID or None if policy_area_name is None
    """
    if not policy_area_name:
        return None

    # First, get the Policy Area tag type ID
    cur.execute("SELECT id FROM tag_types WHERE name = 'Policy Area'")
    result = cur.fetchone()
    if not result:
        logger.error("Policy Area tag type not found")
        return None
    
    type_id = result[0]
    normalized_name = normalize_tag_name(policy_area_name)

    # Try to find existing tag
    cur.execute("""
        SELECT id FROM tags 
        WHERE type_id = %s AND normalized_name = %s
    """, (type_id, normalized_name))
    result = cur.fetchone()
    
    if result:
        return result[0]

    # Create new tag if it doesn't exist
    cur.execute("""
        INSERT INTO tags (type_id, name, normalized_name, description)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (
        type_id,
        policy_area_name,
        normalized_name,
        f'Bills related to {policy_area_name}'
    ))
    return cur.fetchone()[0]

def update_bill_tags(cur, bill_id: int, tag_id: int) -> None:
    """
    Update bill-tag relationships in the bill_tags table.
    
    Args:
        cur: Database cursor
        bill_id: Bill ID
        tag_id: Tag ID
    """
    if not tag_id:
        return

    cur.execute("""
        INSERT INTO bill_tags (bill_id, tag_id)
        VALUES (%s, %s)
        ON CONFLICT (bill_id, tag_id) DO NOTHING
    """, (bill_id, tag_id))
    
    logger.debug(f"Associated bill {bill_id} with tag {tag_id}")

def get_tags_by_type(cur, type_name: str) -> list:
    """
    Get all tags of a specific type.
    
    Args:
        cur: Database cursor
        type_name: Tag type name
        
    Returns:
        List of (id, name, normalized_name) tuples
    """
    cur.execute("""
        SELECT t.id, t.name, t.normalized_name
        FROM tags t
        JOIN tag_types tt ON t.type_id = tt.id
        WHERE tt.name = %s
        ORDER BY t.name
    """, (type_name,))
    return cur.fetchall()