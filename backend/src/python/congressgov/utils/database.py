"""
Database utilities for connecting to PostgreSQL and handling transactions.
"""

import os
import logging
from typing import Callable, Any
from contextlib import contextmanager
from functools import wraps
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

# Set up logging
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection(dict_cursor: bool = False):
    """
    Context manager for database connections.
    
    Args:
        dict_cursor: If True, use RealDictCursor to return results as dictionaries
        
    Yields:
        Database connection
    """
    conn = None
    cursor_factory = RealDictCursor if dict_cursor else None
    
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=cursor_factory)
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")

@contextmanager
def get_db_cursor(dict_cursor: bool = False):
    """
    Context manager for database cursors.
    
    Args:
        dict_cursor: If True, use RealDictCursor to return results as dictionaries
        
    Yields:
        Database cursor
    """
    with get_db_connection(dict_cursor) as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database operation error: {e}")
            raise
        finally:
            cursor.close()

def with_db_transaction(func: Callable) -> Callable:
    """
    Decorator for functions that need a database transaction.
    Automatically handles connections, commits, and rollbacks.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                result = func(cursor, *args, **kwargs)
                conn.commit()
                return result
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction error in {func.__name__}: {e}")
                raise
            finally:
                cursor.close()
    return wrapper

def execute_query(query: str, params: tuple = None, fetchone: bool = False, dict_cursor: bool = False) -> Any:
    """
    Execute a single query and return results.
    
    Args:
        query: SQL query
        params: Query parameters
        fetchone: If True, return a single row instead of all rows
        dict_cursor: If True, return results as dictionaries
        
    Returns:
        Query results
    """
    with get_db_cursor(dict_cursor) as cursor:
        cursor.execute(query, params or ())
        if fetchone:
            return cursor.fetchone()
        return cursor.fetchall()

def execute_batch(query: str, param_sets: list) -> int:
    """
    Execute a batch query with multiple parameter sets.
    
    Args:
        query: SQL query
        param_sets: List of parameter tuples
        
    Returns:
        Number of rows affected
    """
    if not param_sets:
        return 0
        
    with get_db_cursor() as cursor:
        from psycopg2.extras import execute_batch
        execute_batch(cursor, query, param_sets)
        return cursor.rowcount