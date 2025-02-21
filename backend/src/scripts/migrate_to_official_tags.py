#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Database connection string
DB_CONNECTION_STRING = "postgresql://localhost/project_tacitus_test"

# Official Congress.gov Policy Areas
OFFICIAL_POLICY_AREAS = [
    'Agriculture and Food',
    'Animals',
    'Armed Forces and National Security',
    'Arts, Culture, Religion',
    'Civil Rights and Liberties, Minority Issues',
    'Commerce',
    'Congress',
    'Crime and Law Enforcement',
    'Economics and Public Finance',
    'Education',
    'Emergency Management',
    'Energy',
    'Environmental Protection',
    'Families',
    'Finance and Financial Sector',
    'Foreign Trade and International Finance',
    'Government Operations and Politics',
    'Health',
    'Housing and Community Development',
    'Immigration',
    'International Affairs',
    'Labor and Employment',
    'Law',
    'Native Americans',
    'Public Lands and Natural Resources',
    'Science, Technology, Communications',
    'Social Welfare',
    'Sports and Recreation',
    'Taxation',
    'Transportation and Public Works',
    'Water Resources Development'
]

def normalize_name(name):
    """Convert a name to its normalized form (lowercase, underscores for spaces and special chars)"""
    return name.lower().replace(' ', '_').replace(',', '_').replace('&', 'and').replace('-', '_')

def main():
    import sys
    sys.stdout.reconfigure(line_buffering=True)
    print("Starting tag migration process...", flush=True)
    print(f"Connecting to database: {DB_CONNECTION_STRING}", flush=True)
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
    except Exception as e:
        print(f"Failed to connect to database: {str(e)}")
        return
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Get Policy Area tag type ID
        cur.execute("SELECT id FROM tag_types WHERE name = 'Policy Area'")
        policy_area_type = cur.fetchone()
        if not policy_area_type:
            raise Exception("Policy Area tag type not found")
        
        type_id = policy_area_type['id']
        print(f"Found Policy Area tag type (ID: {type_id})")

        # First, let's map our existing tags to their official counterparts
        tag_mapping = {
            'healthcare': 'Health',
            'environment': 'Environmental Protection',
            'education': 'Education'  # This one stays the same but included for completeness
        }

        # Insert all official policy areas
        print("\nInserting official policy areas...")
        for area in OFFICIAL_POLICY_AREAS:
            normalized_name = normalize_name(area)
            cur.execute("""
                INSERT INTO tags (type_id, name, normalized_name, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (type_id, normalized_name) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    description = EXCLUDED.description
                RETURNING id, name;
            """, (type_id, area, normalized_name, f'Bills related to {area}'))
            tag = cur.fetchone()
            print(f"Processed tag: {tag['name']} (ID: {tag['id']})", flush=True)

        # Update bill_tags relationships for each mapping
        print("\nUpdating bill_tags relationships...")
        for old_normalized_name, new_name in tag_mapping.items():
            new_normalized_name = normalize_name(new_name)
            
            # Get old and new tag IDs
            cur.execute("""
                SELECT id, name FROM tags 
                WHERE normalized_name = %s AND type_id = %s
            """, (old_normalized_name, type_id))
            old_tag = cur.fetchone()
            
            cur.execute("""
                SELECT id, name FROM tags 
                WHERE normalized_name = %s AND type_id = %s
            """, (new_normalized_name, type_id))
            new_tag = cur.fetchone()

            if old_tag and new_tag:
                # Update bill_tags to point to new tag
                cur.execute("""
                    UPDATE bill_tags 
                    SET tag_id = %s 
                    WHERE tag_id = %s 
                    RETURNING bill_id
                """, (new_tag['id'], old_tag['id']))
                updated_rows = cur.fetchall()
                print(f"Migrated {len(updated_rows)} bills from '{old_tag['name']}' to '{new_tag['name']}'", flush=True)

                # Delete old tag if it's different from the new one
                if old_normalized_name != new_normalized_name:
                    cur.execute("DELETE FROM tags WHERE id = %s", (old_tag['id'],))
                    print(f"Deleted old tag: {old_tag['name']}", flush=True)

        # Clean up any remaining non-official Policy Area tags
        cur.execute("""
            DELETE FROM tags 
            WHERE type_id = %s 
            AND normalized_name NOT IN %s
            RETURNING name
        """, (type_id, tuple(normalize_name(area) for area in OFFICIAL_POLICY_AREAS)))
        deleted_tags = cur.fetchall()
        if deleted_tags:
            print("\nCleaned up non-official tags:", flush=True)
            for tag in deleted_tags:
                print(f"- {tag['name']}", flush=True)

        # Commit all changes
        conn.commit()
        print("\nMigration completed successfully!", flush=True)

    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
