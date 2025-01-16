import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional

class DatabaseHandler:
    def __init__(self):
        self.conn_string = os.getenv('DATABASE_URL')
        self._test_connection()

    def _test_connection(self):
        """Test database connection"""
        try:
            with psycopg2.connect(self.conn_string) as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT 1')
        except Exception as e:
            raise Exception(f"Database connection failed: {str(e)}")

    async def get_bills_without_text(self) -> List[Dict]:
        """Fetch bills that need text processing"""
        query = """
            SELECT id, bill_number, congress, bill_title
            FROM bills
            WHERE bill_text_link IS NULL
            ORDER BY introduced_date DESC
            LIMIT 100
        """
        try:
            with psycopg2.connect(self.conn_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query)
                    return cur.fetchall()
        except Exception as e:
            raise Exception(f"Error fetching bills: {str(e)}")

    async def update_bill_links(self, bill_id: int, text_link: str, law_link: Optional[str] = None):
        """Update bill text and law links"""
        query = """
            UPDATE bills
            SET bill_text_link = %s,
                bill_law_link = %s
            WHERE id = %s
        """
        try:
            with psycopg2.connect(self.conn_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (text_link, law_link, bill_id))
                conn.commit()
        except Exception as e:
            raise Exception(f"Error updating bill links: {str(e)}")

    async def update_bill_summary(self, bill_id: int, summary: str):
        """Update bill summary"""
        query = """
            UPDATE bills
            SET summary = %s
            WHERE id = %s
        """
        try:
            with psycopg2.connect(self.conn_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (summary, bill_id))
                conn.commit()
        except Exception as e:
            raise Exception(f"Error updating bill summary: {str(e)}")

    async def update_bill_tags(self, bill_id: int, tags: List[str]):
        """Update bill tags"""
        query = """
            UPDATE bills
            SET tags = %s
            WHERE id = %s
        """
        try:
            with psycopg2.connect(self.conn_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (tags, bill_id))
                conn.commit()
        except Exception as e:
            raise Exception(f"Error updating bill tags: {str(e)}")

    async def get_bill_data(self, bill_id: int) -> Dict:
        """Get bill data by ID"""
        query = """
            SELECT id, bill_number, congress, bill_title, bill_text_link, bill_law_link
            FROM bills
            WHERE id = %s
        """
        try:
            with psycopg2.connect(self.conn_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (bill_id,))
                    return cur.fetchone()
        except Exception as e:
            raise Exception(f"Error fetching bill data: {str(e)}")
