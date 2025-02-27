import json
import logging
from datetime import date, datetime
from flask import request
from typing import Dict, List, Any, Tuple, Optional, Union

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

def validate_pagination_params(page=None, per_page=None, max_per_page=100) -> Tuple[int, int]:
    """
    Validate and normalize pagination parameters
    
    Args:
        page: Page number (default: 1)
        per_page: Items per page (default: 20)
        max_per_page: Maximum allowed items per page
        
    Returns:
        tuple: (page, per_page) with validated values
    """
    try:
        page = int(page) if page is not None else 1
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
        
    try:
        per_page = int(per_page) if per_page is not None else 20
        if per_page < 1:
            per_page = 20
        if per_page > max_per_page:
            per_page = max_per_page
    except (ValueError, TypeError):
        per_page = 20
        
    return page, per_page

def get_pagination_params(default_per_page=100, max_per_page=500) -> Dict[str, int]:
    """
    Extract and validate pagination parameters from request
    
    Returns:
        dict: Dictionary with validated 'page', 'per_page', and 'offset' values
    """
    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', default_per_page)
    
    page, per_page = validate_pagination_params(page, per_page, max_per_page)
    offset = (page - 1) * per_page
    
    return {
        'page': page,
        'per_page': per_page,
        'offset': offset
    }

def validate_sort_params(
    sort_key=None, 
    sort_direction=None, 
    allowed_keys=None, 
    default_key='id', 
    default_direction='asc'
) -> Tuple[str, str]:
    """
    Validate sorting parameters
    
    Args:
        sort_key: Field to sort by
        sort_direction: Direction to sort ('asc' or 'desc')
        allowed_keys: List of allowed sort keys
        default_key: Default key to sort by if sort_key is invalid
        default_direction: Default direction if sort_direction is invalid
        
    Returns:
        tuple: (sort_key, sort_direction) with validated values
    """
    if not allowed_keys:
        allowed_keys = [default_key]
        
    # Validate sort key
    if sort_key not in allowed_keys:
        sort_key = default_key
        
    # Validate sort direction
    if sort_direction not in ['asc', 'desc']:
        sort_direction = default_direction
        
    return sort_key, sort_direction

def get_sort_params(allowed_keys=None, default_key='id', default_direction='asc') -> Dict[str, str]:
    """
    Extract and validate sort parameters from request
    
    Returns:
        dict: Dictionary with validated 'sort_key' and 'sort_direction' values
    """
    sort_key = request.args.get('sort_key', default_key)
    sort_direction = request.args.get('sort_direction', default_direction)
    
    sort_key, sort_direction = validate_sort_params(
        sort_key, 
        sort_direction,
        allowed_keys,
        default_key,
        default_direction
    )
    
    return {
        'sort_key': sort_key,
        'sort_direction': sort_direction
    }

def build_pagination_result(items, total_count, page, per_page) -> Dict[str, Any]:
    """
    Create standardized pagination result dictionary
    
    Args:
        items: The list of items for the current page
        total_count: Total number of items across all pages
        page: Current page number
        per_page: Number of items per page
        
    Returns:
        dict: Standardized pagination result
    """
    total_pages = (total_count + per_page - 1) // per_page if per_page > 0 else 0
    
    return {
        'items': items,
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages
    }

def serialize_dates(data, date_fields=None) -> Any:
    """
    Convert date objects to ISO format strings for JSON serialization
    
    Args:
        data: The data to process (dict or list of dicts)
        date_fields: List of field names that contain dates
        
    Returns:
        The processed data with dates converted to strings
    """
    if not date_fields:
        return data
        
    if isinstance(data, dict):
        for field in date_fields:
            if field in data and data[field]:
                if isinstance(data[field], (date, datetime)):
                    data[field] = data[field].isoformat()
    elif isinstance(data, list):
        for item in data:
            serialize_dates(item, date_fields)
            
    return data

def build_filter_clause(filters: Dict[str, Any]) -> Tuple[str, List[Any]]:
    """
    Build a SQL WHERE clause from a dictionary of filters
    
    Args:
        filters: Dictionary mapping column names to filter values
                Each value can be:
                - A string (exact match or LIKE with % wildcards)
                - A tuple ('operator', value) for custom operators
                - A list [val1, val2, ...] for IN operator
                
    Returns:
        tuple: (WHERE clause as string, list of parameter values)
        
    Example:
        filters = {
            'status': 'active',                     # status = 'active'
            'name': '%john%',                       # name LIKE '%john%'
            'age': ('>', 21),                       # age > 21
            'state': ('IN', ['CA', 'NY', 'TX']),    # state IN ('CA', 'NY', 'TX')
            'created_at': ('BETWEEN', ('2020-01-01', '2020-12-31'))
        }
    """
    clauses = []
    params = []
    
    for col, value in filters.items():
        if value is None or value == '':
            continue
            
        if isinstance(value, tuple) and len(value) == 2:
            operator, val = value
            operator = operator.upper()
            
            if operator == 'IN' and isinstance(val, list):
                if not val:  # Empty list
                    continue
                placeholders = ', '.join(['%s'] * len(val))
                clauses.append(f"{col} IN ({placeholders})")
                params.extend(val)
            elif operator == 'BETWEEN' and isinstance(val, tuple) and len(val) == 2:
                clauses.append(f"{col} BETWEEN %s AND %s")
                params.extend(val)
            else:
                clauses.append(f"{col} {operator} %s")
                params.append(val)
        elif isinstance(value, list):
            if not value:  # Empty list
                continue
            placeholders = ', '.join(['%s'] * len(value))
            clauses.append(f"{col} IN ({placeholders})")
            params.extend(value)
        elif isinstance(value, str) and '%' in value:
            clauses.append(f"LOWER({col}) LIKE LOWER(%s)")
            params.append(value)
        else:
            clauses.append(f"{col} = %s")
            params.append(value)
    
    if not clauses:
        return "", []
        
    where_clause = " WHERE " + " AND ".join(clauses)
    return where_clause, params

def get_logger(name):
    """
    Get a logger with consistent formatting
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger