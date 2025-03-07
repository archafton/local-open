-- Add last_updated column to bills table
ALTER TABLE bills
ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP WITH TIME ZONE DEFAULT '2025-01-01 00:00:00 UTC';

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_bills_last_updated ON bills(last_updated);

-- Update existing records to have a last_updated value
UPDATE bills
SET last_updated = '2025-01-01 00:00:00 UTC'HR8308
