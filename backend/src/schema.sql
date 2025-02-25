-- Add new columns to members table for member bios
ALTER TABLE members
ADD COLUMN IF NOT EXISTS profile_text TEXT,
ADD COLUMN IF NOT EXISTS bio_directory TEXT,
ADD COLUMN IF NOT EXISTS bio_update_date TIMESTAMP WITH TIME ZONE;

-- Enhance bill_cosponsors table
ALTER TABLE bill_cosponsors
ADD COLUMN IF NOT EXISTS cosponsor_date DATE,
ADD COLUMN IF NOT EXISTS cosponsor_chamber VARCHAR(50),
ADD COLUMN IF NOT EXISTS cosponsor_district INTEGER;

-- Enhance bills table
ALTER TABLE bills
ADD COLUMN IF NOT EXISTS bill_type VARCHAR(20),
ADD COLUMN IF NOT EXISTS policy_area VARCHAR(100),
ADD COLUMN IF NOT EXISTS api_url VARCHAR(255),
ADD COLUMN IF NOT EXISTS amendment_number VARCHAR(50);

-- Enhance bill_actions table
ALTER TABLE bill_actions
ADD COLUMN IF NOT EXISTS action_time TIME;

-- Rest of schema unchanged
-- Add new columns to members table for member details
ALTER TABLE members
ADD COLUMN IF NOT EXISTS direct_order_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS honorific_name VARCHAR(20),
ADD COLUMN IF NOT EXISTS inverted_order_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS update_date TIMESTAMP WITH TIME ZONE;

-- Create new table for member leadership positions if it doesn't exist
CREATE TABLE IF NOT EXISTS member_leadership (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    congress INTEGER NOT NULL,
    leadership_type VARCHAR(100) NOT NULL,
    UNIQUE (member_id, congress)
);

-- Create new table for member party history if it doesn't exist
CREATE TABLE IF NOT EXISTS member_party_history (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    party_name VARCHAR(50) NOT NULL,
    party_code VARCHAR(10),
    start_year INTEGER NOT NULL,
    UNIQUE (member_id, start_year)
);

-- Existing tables and modifications below this line
CREATE TABLE IF NOT EXISTS bills (
    id SERIAL PRIMARY KEY,
    bill_number VARCHAR(50) NOT NULL UNIQUE,
    bill_title TEXT NOT NULL,
    sponsor_id VARCHAR(50),
    introduced_date DATE,
    summary TEXT,
    congress INTEGER,
    status TEXT,
    bill_text TEXT
);

CREATE TABLE IF NOT EXISTS members (
    id SERIAL PRIMARY KEY,
    bioguide_id VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    last_name VARCHAR(50) NOT NULL,
    suffix VARCHAR(10),
    nickname VARCHAR(50),
    full_name VARCHAR(100) NOT NULL,
    birth_year INTEGER,
    death_year INTEGER,
    party VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    district INTEGER,
    chamber VARCHAR(50) NOT NULL,
    current_member BOOLEAN NOT NULL,
    leadership_role VARCHAR(100),
    office_address TEXT,
    phone VARCHAR(20),
    url VARCHAR(255),
    photo_url VARCHAR(255),
    total_votes INTEGER DEFAULT 0,
    missed_votes INTEGER DEFAULT 0,
    total_present INTEGER DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS member_terms (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    congress INTEGER,
    chamber VARCHAR(50) NOT NULL,
    party VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    district INTEGER,
    start_date DATE NOT NULL,
    end_date DATE,
    UNIQUE (member_id, congress, chamber)
);

CREATE TABLE IF NOT EXISTS votes (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills(id),
    member_id INTEGER REFERENCES members(id),
    vote VARCHAR(10) NOT NULL,
    vote_date DATE NOT NULL,
    vote_type VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS committees (
    id SERIAL PRIMARY KEY,
    committee_name VARCHAR(255) NOT NULL,
    chamber VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS bill_committees (
    bill_id INTEGER REFERENCES bills(id),
    committee_id INTEGER REFERENCES committees(id),
    PRIMARY KEY (bill_id, committee_id)
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sponsored_legislation (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    bill_id INTEGER REFERENCES bills(id),
    introduced_date DATE NOT NULL,
    UNIQUE (member_id, bill_id)
);

CREATE TABLE IF NOT EXISTS cosponsored_legislation (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    bill_id INTEGER REFERENCES bills(id),
    cosponsored_date DATE NOT NULL,
    UNIQUE (member_id, bill_id)
);

-- Bill-related tables and modifications
ALTER TABLE bills
ADD COLUMN IF NOT EXISTS latest_action TEXT,
ADD COLUMN IF NOT EXISTS latest_action_date DATE,
ADD COLUMN IF NOT EXISTS normalized_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS official_title TEXT,
ADD COLUMN IF NOT EXISTS short_title TEXT,
ADD COLUMN IF NOT EXISTS related_bills TEXT[],
ADD COLUMN IF NOT EXISTS text_versions JSONB,
ADD COLUMN IF NOT EXISTS bill_text_link VARCHAR(255),
ADD COLUMN IF NOT EXISTS bill_law_link VARCHAR(255);

CREATE TABLE IF NOT EXISTS bill_actions (
    id SERIAL PRIMARY KEY,
    bill_number VARCHAR(50) REFERENCES bills(bill_number),
    action_date DATE NOT NULL,
    action_text TEXT NOT NULL,
    action_type VARCHAR(50),
    action_time TIME,
    UNIQUE (bill_number, action_date, action_text)
);

CREATE TABLE IF NOT EXISTS bill_cosponsors (
    id SERIAL PRIMARY KEY,
    bill_number VARCHAR(50) REFERENCES bills(bill_number),
    cosponsor_id VARCHAR(50) NOT NULL,
    cosponsor_name VARCHAR(100) NOT NULL,
    cosponsor_party VARCHAR(50),
    cosponsor_state VARCHAR(50),
    UNIQUE (bill_number, cosponsor_id)
);

CREATE TABLE IF NOT EXISTS bill_subjects (
    id SERIAL PRIMARY KEY,
    bill_number VARCHAR(50) REFERENCES bills(bill_number),
    subject_name TEXT NOT NULL,
    UNIQUE (bill_number, subject_name)
);

-- Existing ALTER TABLE statements
ALTER TABLE votes
ADD COLUMN IF NOT EXISTS member_id INTEGER REFERENCES members(id);

ALTER TABLE bills
ADD COLUMN IF NOT EXISTS sponsor_id VARCHAR(50);

-- Modify the state column in the members table
ALTER TABLE members
ALTER COLUMN state TYPE VARCHAR(50);

-- Modify the state column in the member_terms table
ALTER TABLE member_terms
ALTER COLUMN state TYPE VARCHAR(50);

-- Allow NULL values for congress in member_terms table
ALTER TABLE member_terms
ALTER COLUMN congress DROP NOT NULL;

-- Add unique constraint to member_terms table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'member_terms_member_id_congress_chamber_key'
    ) THEN
        ALTER TABLE member_terms
        ADD CONSTRAINT member_terms_member_id_congress_chamber_key
        UNIQUE (member_id, congress, chamber);
    END IF;
END $$;

-- Create tag system tables
CREATE TABLE IF NOT EXISTS tag_types (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    type_id INTEGER REFERENCES tag_types(id),
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,  -- lowercase, no spaces for consistent matching
    parent_id INTEGER REFERENCES tags(id),  -- for hierarchical structure
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(type_id, normalized_name)
);

CREATE TABLE IF NOT EXISTS bill_tags (
    bill_id INTEGER REFERENCES bills(id),
    tag_id INTEGER REFERENCES tags(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (bill_id, tag_id)
);

-- Add indexes for tag system performance
CREATE INDEX IF NOT EXISTS idx_tags_type_id ON tags(type_id);
CREATE INDEX IF NOT EXISTS idx_tags_parent_id ON tags(parent_id);
CREATE INDEX IF NOT EXISTS idx_bill_tags_tag_id ON bill_tags(tag_id);

-- Create API sync status tracking table
CREATE TABLE IF NOT EXISTS api_sync_status (
    endpoint VARCHAR(100) PRIMARY KEY,
    last_sync_timestamp TIMESTAMP WITH TIME ZONE,
    last_successful_offset INTEGER,
    last_error TEXT,
    status VARCHAR(50)
);

-- Add index for API sync status timestamp
CREATE INDEX IF NOT EXISTS idx_api_sync_last_sync ON api_sync_status(last_sync_timestamp);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers to update the updated_at column
DROP TRIGGER IF EXISTS update_tag_types_updated_at ON tag_types;
CREATE TRIGGER update_tag_types_updated_at
    BEFORE UPDATE ON tag_types
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_tags_updated_at ON tags;
CREATE TRIGGER update_tags_updated_at
    BEFORE UPDATE ON tags
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert initial tag types
INSERT INTO tag_types (name, description)
VALUES
    ('Policy Area', 'Main policy areas or domains that the bill addresses'),
    ('Bill Type', 'Type of legislative action or document'),
    ('Sponsorship', 'Information about political party sponsorship'),
    ('Committee', 'Congressional committees responsible for the bill'),
    ('Geographic Focus', 'Geographic scope or impact of the bill'),
    ('Beneficiaries', 'Groups or populations the bill aims to benefit'),
    ('Funding', 'Financial implications or budget impact'),
    ('Time Frame', 'Intended duration of the bill''s provisions'),
    ('Related Laws', 'Existing laws or programs the bill relates to'),
    ('Hot Topics', 'Popular or controversial topics addressed')
ON CONFLICT (name) DO NOTHING;

-- Insert official Congress.gov Policy Area tags
INSERT INTO tags (type_id, name, normalized_name, description)
SELECT 
    tt.id,
    t.name,
    LOWER(REGEXP_REPLACE(t.name, '[^a-zA-Z0-9]+', '_', 'g')), -- normalize name by converting to lowercase and replacing non-alphanumeric chars with underscore
    'Bills related to ' || t.name
FROM (
    VALUES
        ('Agriculture and Food'),
        ('Animals'),
        ('Armed Forces and National Security'),
        ('Arts, Culture, Religion'),
        ('Civil Rights and Liberties, Minority Issues'),
        ('Commerce'),
        ('Congress'),
        ('Crime and Law Enforcement'),
        ('Economics and Public Finance'),
        ('Education'),
        ('Emergency Management'),
        ('Energy'),
        ('Environmental Protection'),
        ('Families'),
        ('Finance and Financial Sector'),
        ('Foreign Trade and International Finance'),
        ('Government Operations and Politics'),
        ('Health'),
        ('Housing and Community Development'),
        ('Immigration'),
        ('International Affairs'),
        ('Labor and Employment'),
        ('Law'),
        ('Native Americans'),
        ('Public Lands and Natural Resources'),
        ('Science, Technology, Communications'),
        ('Social Welfare'),
        ('Sports and Recreation'),
        ('Taxation'),
        ('Transportation and Public Works'),
        ('Water Resources Development')
) AS t(name)
CROSS JOIN (SELECT id FROM tag_types WHERE name = 'Policy Area' LIMIT 1) tt
ON CONFLICT (type_id, normalized_name) DO UPDATE 
SET name = EXCLUDED.name,
    description = EXCLUDED.description;
