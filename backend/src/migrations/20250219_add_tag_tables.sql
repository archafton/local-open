-- Create tag types table
CREATE TABLE tag_types (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create tags table with hierarchical structure
CREATE TABLE tags (
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

-- Create bill-tag associations table
CREATE TABLE bill_tags (
    bill_id INTEGER REFERENCES bills(id),
    tag_id INTEGER REFERENCES tags(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (bill_id, tag_id)
);

-- Add indexes for performance
CREATE INDEX idx_tags_type_id ON tags(type_id);
CREATE INDEX idx_tags_parent_id ON tags(parent_id);
CREATE INDEX idx_bill_tags_tag_id ON bill_tags(tag_id);

-- Insert initial tag types from Tags.md
INSERT INTO tag_types (name, description) VALUES
('Policy Area', 'Main policy areas or domains that the bill addresses'),
('Bill Type', 'Type of legislative action or document'),
('Sponsorship', 'Information about political party sponsorship'),
('Committee', 'Congressional committees responsible for the bill'),
('Geographic Focus', 'Geographic scope or impact of the bill'),
('Beneficiaries', 'Groups or populations the bill aims to benefit'),
('Funding', 'Financial implications or budget impact'),
('Time Frame', 'Intended duration of the bill''s provisions'),
('Related Laws', 'Existing laws or programs the bill relates to'),
('Hot Topics', 'Popular or controversial topics addressed');

-- Add some initial example tags
INSERT INTO tags (type_id, name, normalized_name, description) VALUES
-- Policy Area tags
(1, 'Healthcare', 'healthcare', 'Healthcare related bills'),
(1, 'Education', 'education', 'Education related bills'),
(1, 'Environment', 'environment', 'Environmental policy bills'),

-- Bill Type tags
(2, 'Appropriations', 'appropriations', 'Bills that provide funding'),
(2, 'Authorization', 'authorization', 'Bills that authorize programs or activities'),
(2, 'Resolution', 'resolution', 'Formal expressions of opinion'),

-- Sponsorship tags
(3, 'Bipartisan', 'bipartisan', 'Bills with sponsors from multiple parties'),
(3, 'Democratic Sponsored', 'democratic_sponsored', 'Bills sponsored by Democrats'),
(3, 'Republican Sponsored', 'republican_sponsored', 'Bills sponsored by Republicans');

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers to update the updated_at column
CREATE TRIGGER update_tag_types_updated_at
    BEFORE UPDATE ON tag_types
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tags_updated_at
    BEFORE UPDATE ON tags
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
