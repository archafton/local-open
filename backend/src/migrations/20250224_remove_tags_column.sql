-- First, ensure any existing tags are migrated to the new system
DO $$
DECLARE
    policy_area_type_id INTEGER;
    bill_record RECORD;
    tag_id INTEGER;
BEGIN
    -- Get Policy Area tag type ID
    SELECT id INTO policy_area_type_id FROM tag_types WHERE name = 'Policy Area';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Policy Area tag type not found';
    END IF;

    -- Process each bill's tags
    FOR bill_record IN SELECT id, tags FROM bills WHERE tags IS NOT NULL AND array_length(tags, 1) > 0
    LOOP
        -- For each tag in the array
        FOR i IN 1..array_length(bill_record.tags, 1)
        LOOP
            -- Get or create tag
            WITH tag_insert AS (
                INSERT INTO tags (type_id, name, normalized_name, description)
                VALUES (
                    policy_area_type_id,
                    bill_record.tags[i],
                    LOWER(REGEXP_REPLACE(bill_record.tags[i], '[^a-zA-Z0-9]+', '_', 'g')),
                    'Bills related to ' || bill_record.tags[i]
                )
                ON CONFLICT (type_id, normalized_name) DO UPDATE
                    SET name = EXCLUDED.name
                RETURNING id
            )
            SELECT id INTO tag_id FROM tag_insert;

            -- Create bill-tag relationship
            INSERT INTO bill_tags (bill_id, tag_id)
            VALUES (bill_record.id, tag_id)
            ON CONFLICT (bill_id, tag_id) DO NOTHING;
        END LOOP;
    END LOOP;
END;
$$;

-- Now remove the tags column from bills table
ALTER TABLE bills DROP COLUMN IF EXISTS tags;
