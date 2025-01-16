# archafton 4/7/2024 - Tags added below schema

This documentation provides an overview of the main tables in the Tacitus data schema, along with their columns and descriptions. The schema is designed to store information about bills, representatives, votes, committees, and users.

The bills table serves as the central entity, storing details about each legislative bill. The representatives table contains information about elected representatives, while the votes table captures the voting records of representatives on specific bills.

The committees table stores information about congressional committees, and the bill_committees table represents the many-to-many relationship between bills and committees, indicating which committees are associated with each bill.

Lastly, the users table stores information about the registered users of the Tacitus platform, including their username, email, and hashed password.

The schema utilizes primary keys (id columns) to uniquely identify records in each table and foreign keys to establish relationships between tables. For example, the bill_id and representative_id columns in the votes table reference the id columns in the bills and representatives tables, respectively.

This schema provides a foundation for storing and organizing the data required by the Tacitus platform. It can be further extended or modified based on additional requirements or future enhancements.

## Tables schema:

### bills: Stores information about legislative bills.
    id:                 Auto-incrementing unique identifier for each bill (primary key).
    bill_number:        The official bill number assigned by the legislature.
    bill_title:         The title or short description of the bill.
    sponsor_id:         The unique identifier of the bill's sponsor (foreign key referencing representatives.id).
    introduced_date:    The date when the bill was introduced.
    summary:            The LLM-generated summary of the bill.
    tags:               The LLM-generated categorical tags.
    congress:           The number of the Congress in which the bill was introduced.
    status:             The current status of the bill (e.g., "Introduced", "Passed House", "Enacted").
    bill_text:          The full text of the bill.

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

------
# Tags addendum, this list isn't comprehensive, a running list of ideas to help searching and visualizations.

### Policy Area:
Ex: Healthcare, Education, Environment, Transportation, Agriculture, Defense, Immigration, etc.
These tags indicate the main policy areas or domains that the bill addresses.

### Bill Type:
Ex: Appropriations, Authorization, Amendment, Resolution, Concurrent Resolution, etc.
These tags specify the type of legislative action or document the bill represents.

### Sponsorship:
Ex: Sponsored by Democrats, Sponsored by Republicans, Bipartisan Sponsorship, etc.
These tags provide information about the political party or parties sponsoring the bill.

### Committee:
Ex: House Judiciary Committee, Senate Finance Committee, Joint Economic Committee, etc.
These tags indicate the congressional committee(s) responsible for reviewing and handling the bill.

### Geographic Focus:
Ex: State-Specific, Regional, National, International, etc.
These tags highlight the geographic scope or impact of the bill.

### Beneficiaries or Affected Groups:
Ex: Veterans, Small Businesses, Students, Seniors, Low-Income Families, etc.
These tags identify the specific groups or populations that the bill aims to benefit or impact.

### Funding or Budget:
Ex: Budget Increase, Budget Cut, Revenue Neutral, etc.
These tags provide information about the financial implications or budget impact of the bill.

### Time Frame:
Ex: Short-Term, Long-Term, Permanent, Temporary, etc.
These tags indicate the intended duration or time frame of the bill's provisions.

### Related Laws or Programs:
Ex: Affordable Care Act, No Child Left Behind Act, Voting Rights Act, etc.
These tags link the bill to existing laws, programs, or initiatives that it relates to or aims to modify.

### Hot Topics or Buzzwords:
Ex: Climate Change, Gun Control, LGBT Rights, Cybersecurity, Infrastructure, etc.
These tags highlight popular or controversial topics that the bill addresses, making it easier to identify bills related to specific issues.
