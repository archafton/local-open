import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from flask import current_app
from contextlib import contextmanager

def get_db_connection():
    """Create and return a database connection"""
    connection_string = current_app.config['DB_CONNECTION_STRING']
    logging.info(f"Connecting to database with connection string: {connection_string}")
    try:
        conn = psycopg2.connect(connection_string)
        logging.info("Successfully connected to database")
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to database: {str(e)}")
        raise

@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager that provides a database cursor and handles connections.
    
    Args:
        commit (bool): Whether to commit the transaction before closing
                      Default is False (for read operations)
    
    Yields:
        cursor: A database cursor with RealDictCursor factory
    
    Example:
        with get_db_cursor(commit=True) as cur:
            cur.execute("INSERT INTO table VALUES (%s)", [value])
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        if conn and commit:
            conn.rollback()
        logging.error(f"Database error: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@contextmanager
def transaction():
    """
    Context manager for database transactions.
    Ensures that a group of operations either all succeed or all fail.
    
    Example:
        with transaction() as cur:
            cur.execute("UPDATE accounts SET balance = balance - 100 WHERE id = %s", [1])
            cur.execute("UPDATE accounts SET balance = balance + 100 WHERE id = %s", [2])
    """
    with get_db_cursor(commit=True) as cursor:
        yield cursor