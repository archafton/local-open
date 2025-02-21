#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection string
DB_CONNECTION_STRING = "postgresql://localhost/project_tacitus_test"

def main():
    print("Starting bill tag linking process...")
    conn = psycopg2.connect(DB_CONNECTION_STRING)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Get Policy Area tag type ID
        cur.execute("SELECT id FROM tag_types WHERE name = 'Policy Area'")
        policy_area_type = cur.fetchone()
        if not policy_area_type:
            raise Exception("Policy Area tag type not found")
        
        type_id = policy_area_type['id']
        print(f"Found Policy Area tag type (ID: {type_id})")

        # Get all Policy Area tags
        cur.execute("""
            SELECT id, name 
            FROM tags 
            WHERE type_id = %s
        """, (type_id,))
        policy_area_tags = {row['name']: row['id'] for row in cur.fetchall()}
        print(f"Found {len(policy_area_tags)} Policy Area tags")

        # Get all bills with their tags
        cur.execute("SELECT id, bill_number, tags FROM bills WHERE tags IS NOT NULL")
        bills = cur.fetchall()
        print(f"Found {len(bills)} bills with tags")

        total_links = 0
        for bill in bills:
            if not bill['tags']:
                continue

            # For each tag in the bill's tags array
            for tag in bill['tags']:
                tag = tag.strip()  # Remove any leading/trailing whitespace
                if tag in policy_area_tags:
                    # Check if relationship already exists
                    cur.execute("""
                        SELECT 1 FROM bill_tags 
                        WHERE bill_id = %s AND tag_id = %s
                    """, (bill['id'], policy_area_tags[tag]))
                    
                    if not cur.fetchone():
                        # Create new relationship
                        cur.execute("""
                            INSERT INTO bill_tags (bill_id, tag_id)
                            VALUES (%s, %s)
                        """, (bill['id'], policy_area_tags[tag]))
                        total_links += 1
                        print(f"Linked bill {bill['bill_number']} to tag '{tag}'")

        # Commit all changes
        conn.commit()
        print(f"\nCreated {total_links} new bill-tag relationships")
        print("Process completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error during process: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
