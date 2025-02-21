#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection string
DB_CONNECTION_STRING = "postgresql://localhost/project_tacitus_test"

def main():
    # Connect to the database
    print("Connecting to database...")
    conn = psycopg2.connect(DB_CONNECTION_STRING)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Get the Environment tag ID
        cur.execute("""
            SELECT id 
            FROM tags 
            WHERE normalized_name = 'environment' 
            AND type_id = (SELECT id FROM tag_types WHERE name = 'Policy Area')
        """)
        environment_tag = cur.fetchone()
        
        if not environment_tag:
            print("Error: Environment tag not found in the database")
            return
            
        environment_tag_id = environment_tag['id']
        print(f"Found Environment tag with ID: {environment_tag_id}")

        # Find bills with environment-related tags
        cur.execute("""
            SELECT id, bill_number, tags 
            FROM bills 
            WHERE tags && ARRAY['Public Lands and Natural Resources', 'Environmental Protection']
        """)
        env_bills = cur.fetchall()
        
        print(f"Found {len(env_bills)} bills with environment-related tags")

        # Add Environment tag to these bills
        for bill in env_bills:
            # Check if the bill already has this tag
            cur.execute("""
                SELECT 1 
                FROM bill_tags 
                WHERE bill_id = %s AND tag_id = %s
            """, (bill['id'], environment_tag_id))
            
            if not cur.fetchone():
                # Add the tag if it doesn't exist
                cur.execute("""
                    INSERT INTO bill_tags (bill_id, tag_id)
                    VALUES (%s, %s)
                """, (bill['id'], environment_tag_id))
                print(f"Added Environment tag to bill {bill['bill_number']}")
            else:
                print(f"Bill {bill['bill_number']} already has Environment tag")

        # Get the Healthcare tag ID
        cur.execute("""
            SELECT id 
            FROM tags 
            WHERE normalized_name = 'healthcare' 
            AND type_id = (SELECT id FROM tag_types WHERE name = 'Policy Area')
        """)
        healthcare_tag = cur.fetchone()
        
        if not healthcare_tag:
            print("Error: Healthcare tag not found in the database")
            return
            
        healthcare_tag_id = healthcare_tag['id']
        print(f"Found Healthcare tag with ID: {healthcare_tag_id}")

        # Find bills with health-related tags (case insensitive)
        cur.execute("""
            SELECT id, bill_number, tags 
            FROM bills 
            WHERE EXISTS (
                SELECT 1 
                FROM unnest(tags) tag 
                WHERE tag ILIKE '%health%'
            )
        """)
        health_bills = cur.fetchall()
        
        print(f"Found {len(health_bills)} bills with health-related tags")

        # Add Healthcare tag to these bills
        for bill in health_bills:
            # Check if the bill already has this tag
            cur.execute("""
                SELECT 1 
                FROM bill_tags 
                WHERE bill_id = %s AND tag_id = %s
            """, (bill['id'], healthcare_tag_id))
            
            if not cur.fetchone():
                # Add the tag if it doesn't exist
                cur.execute("""
                    INSERT INTO bill_tags (bill_id, tag_id)
                    VALUES (%s, %s)
                """, (bill['id'], healthcare_tag_id))
                print(f"Added Healthcare tag to bill {bill['bill_number']}")
            else:
                print(f"Bill {bill['bill_number']} already has Healthcare tag")

        # Commit all changes
        conn.commit()
        print("Successfully completed all tagging operations")

    except Exception as e:
        conn.rollback()
        print(f"Error: {str(e)}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
