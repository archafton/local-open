-- Add new columns to members table for member bios
ALTER TABLE members
ADD COLUMN IF NOT EXISTS profile_text TEXT,
ADD COLUMN IF NOT EXISTS bio_directory TEXT,
ADD COLUMN IF NOT EXISTS bio_update_date TIMESTAMP WITH TIME ZONE;

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
    tags TEXT[],
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
    introduced_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS cosponsored_legislation (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    bill_id INTEGER REFERENCES bills(id),
    cosponsored_date DATE NOT NULL
);

-- Bill-related tables and modifications
ALTER TABLE bills
ADD COLUMN IF NOT EXISTS latest_action TEXT,
ADD COLUMN IF NOT EXISTS latest_action_date DATE,
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
