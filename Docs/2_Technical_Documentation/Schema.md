# Database Schema Documentation

This documentation provides an overview of the main tables in the Tacitus data schema, along with their columns and descriptions. The schema is designed to store information about bills, representatives, votes, committees, tags, and users.

The bills table serves as the central entity, storing details about each legislative bill. The representatives table contains information about elected representatives, while the votes table captures the voting records of representatives on specific bills.

The committees table stores information about congressional committees, and the bill_committees table represents the many-to-many relationship between bills and committees, indicating which committees are associated with each bill.

The tag_types and tag tables stores available tags in a hierarchical structure. The bill_tags table contains the many-to-many relationship between bills and tags.

Lastly, the users table stores information about the registered users of the Tacitus platform, including their username, email, and hashed password.

The schema utilizes primary keys (id columns) to uniquely identify records in each table and foreign keys to establish relationships between tables. For example, the bill_id and representative_id columns in the votes table reference the id columns in the bills and representatives tables, respectively.

This schema provides a foundation for storing and organizing the data required by the Tacitus platform. It can be further extended or modified based on additional requirements or future enhancements, but **this document must be updated to reflect those enhancements or changes.**

## Tables schema:

### bills: Stores information about legislative bills.
    id:                 Auto-incrementing unique identifier for each bill (primary key).
    bill_number:        The official bill number assigned by the legislature.
    bill_title:         The title or short description of the bill.
    sponsor_id:         The unique identifier of the bill's sponsor (foreign key referencing representatives.id).
    introduced_date:    The date when the bill was introduced.
    summary:            The LLM-generated summary of the bill.
    congress:           The number of the Congress in which the bill was introduced.
    status:             The current status of the bill (e.g., "Introduced", "Passed House", "Enacted").
    normalized_status:  The standardized status for consistent filtering.
    bill_text:          The full text of the bill.
    latest_action:      The most recent action taken on the bill.
    latest_action_date: The date of the most recent action.

### representatives: Stores information about elected representatives.
    id:                 Auto-incrementing unique identifier for each representative (primary key).
    first_name:         The first name of the representative.
    last_name:          The last name of the representative.
    party:              The political party affiliation of the representative.
    state:              The state the representative represents.
    district:           The congressional district the representative represents (null for senators).
    role:               The role of the representative (e.g., "Senator", "Representative").
    term_start:         The start date of the representative's current term.
    term_end:           The end date of the representative's current term.

### votes: Stores information about the votes cast by representatives on bills.
    id:                 Auto-incrementing unique identifier for each vote record (primary key).
    bill_id:            The unique identifier of the associated bill (foreign key referencing bills.id).
    representative_id:  The unique identifier of the representative who cast the vote (foreign key referencing representatives.id).
    vote:               The vote cast by the representative (e.g., "Yes", "No", "Abstain").
    vote_date:          The date when the vote was cast.
    vote_type:          The type of vote (e.g., "Roll Call", "Voice Vote", "Unanimous Consent").

### committees: Stores information about congressional committees.
    id:                 Auto-incrementing unique identifier for each committee (primary key).
    committee_name:     The name of the congressional committee.
    chamber:            The chamber of Congress (e.g., "House", "Senate", "Joint").

### bill_committees: Represents the many-to-many relationship between bills and committees.
    bill_id:            The unique identifier of the associated bill (foreign key referencing bills.id).
    committee_id:       The unique identifier of the associated committee (foreign key referencing committees.id).
                            *The combination of bill_id and committee_id forms the primary key.

### users: Stores information about the users of the Tacitus platform.
    id:                 Auto-incrementing unique identifier for each user (primary key).
    username:           The unique username of the user.
    email:              The email address of the user.
    password_hash:      The hashed password of the user.
    created_at:         The timestamp indicating when the user account was created (defaults to the current timestamp).

### tag_types: Stores categories for organizing tags.
    id:                 Auto-incrementing unique identifier for each tag type (primary key).
    name:               The name of the tag type (e.g., "Policy Area", "Bill Type").
    description:        A description of what this tag type represents.
    created_at:         The timestamp when the tag type was created.
    updated_at:         The timestamp when the tag type was last updated.

### tags: Stores individual tags that can be applied to bills.
    id:                 Auto-incrementing unique identifier for each tag (primary key).
    type_id:            The type of this tag (foreign key referencing tag_types.id).
    name:               The display name of the tag.
    normalized_name:    A standardized version of the name for consistent lookups.
    parent_id:          Optional reference to a parent tag for hierarchical organization (self-referencing foreign key).
    description:        A description of what this tag represents.
    created_at:         The timestamp when the tag was created.
    updated_at:         The timestamp when the tag was last updated.

### bill_tags: Represents the many-to-many relationship between bills and tags.
    bill_id:            The unique identifier of the associated bill (foreign key referencing bills.id).
    tag_id:             The unique identifier of the associated tag (foreign key referencing tags.id).
    created_at:         The timestamp when the association was created.
                       *The combination of bill_id and tag_id forms the primary key.

------
# Tag System Overview

The tag system uses a hierarchical structure to organize and categorize bills. Here's how the components work together:

### Hierarchical Organization
- Tags can have parent-child relationships
- Enables organizing tags from general to specific
- Example hierarchy:
  ```
  Policy Area (type)
  └── Healthcare (parent tag)
      ├── Mental Health
      ├── Public Health
      └── Healthcare Access
  ```

### Tag Relationships
- Bills can have multiple tags
- Tags can belong to different types
- One bill might have:
  - Policy Area: Healthcare
  - Bill Type: Authorization
  - Geographic Focus: National
  - Time Frame: Permanent

This structured approach enables:
- Precise bill categorization
- Flexible search and filtering
- Clear organization of legislative topics
- Easy navigation of related bills

### Tag Types
Tag types provide high-level categories for organizing tags. The system includes several predefined types:

1. Policy Area
   - Main policy domains (e.g., Healthcare, Education, Environment)
   - Helps categorize bills by their primary focus

2. Bill Type
   - Legislative action types (e.g., Appropriations, Authorization, Resolution)
   - Indicates the nature of the legislative document

3. Sponsorship
   - Political affiliation info (e.g., Bipartisan, Democratic Sponsored)
   - Shows the political context of the bill

4. Committee
   - Congressional committees (e.g., House Judiciary, Senate Finance)
   - Links bills to their reviewing committees

5. Geographic Focus
   - Spatial scope (e.g., State-Specific, National, International)
   - Indicates the geographic impact

6. Beneficiaries
   - Target groups (e.g., Veterans, Small Businesses, Students)
   - Shows who the bill aims to help

7. Funding
   - Budget implications (e.g., Budget Increase, Revenue Neutral)
   - Indicates financial impact

8. Time Frame
   - Duration info (e.g., Short-Term, Permanent)
   - Shows intended timeline

9. Related Laws
   - Connections to existing legislation
   - Links bills to relevant legal framework

10. Hot Topics
    - Current issues (e.g., Climate Change, Cybersecurity)
    - Highlights trending subjects

See [Tags Addendum](Schema_Tags.md) for a list of current and future tags.
