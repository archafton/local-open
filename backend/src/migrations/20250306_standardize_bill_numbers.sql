-- Migration: Standardize bill numbers to uppercase across all tables
-- Date: 2025-03-06

BEGIN;

-- Update bills table
UPDATE bills
SET bill_number = UPPER(bill_number)
WHERE bill_number != UPPER(bill_number);

-- Update bill_actions table
UPDATE bill_actions
SET bill_number = UPPER(bill_number)
WHERE bill_number != UPPER(bill_number);

-- Update bill_cosponsors table
UPDATE bill_cosponsors
SET bill_number = UPPER(bill_number)
WHERE bill_number != UPPER(bill_number);

-- Update bill_subjects table
UPDATE bill_subjects
SET bill_number = UPPER(bill_number)
WHERE bill_number != UPPER(bill_number);

-- Log the migration
INSERT INTO api_sync_status (endpoint, last_sync_timestamp, status, last_error)
VALUES ('migration_standardize_bill_numbers', CURRENT_TIMESTAMP, 'success', NULL)
ON CONFLICT (endpoint) DO UPDATE
SET last_sync_timestamp = CURRENT_TIMESTAMP,
    status = 'success',
    last_error = NULL;

COMMIT;
