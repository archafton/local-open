# Tag System Design

## Schema Design

```sql
-- Tag Types (e.g., Policy Area, Bill Type, etc.)
CREATE TABLE tag_types (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tags with hierarchical structure
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

-- Bill-Tag associations
CREATE TABLE bill_tags (
    bill_id INTEGER REFERENCES bills(id),
    tag_id INTEGER REFERENCES tags(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (bill_id, tag_id)
);

-- Indexes for performance
CREATE INDEX idx_tags_type_id ON tags(type_id);
CREATE INDEX idx_tags_parent_id ON tags(parent_id);
CREATE INDEX idx_bill_tags_tag_id ON bill_tags(tag_id);
```

## Implementation Status

### Phase 1: Simple Tag Filter (Completed)
- Single dropdown showing "Tag (Tag Type)"
- Basic operators:
  - is
  - is not
  - is one of
  - is not one of
- Allow mixing tag types in multi-select operations
- URL state persistence for filters

Example UI:
```
[Tag ▼] [Operator ▼] [Selected Tags ▼]
Healthcare (Policy Area)
Resolution (Bill Type)    [x]  -- Selected tags with remove option
Veterans (Beneficiary)    [x]
```

### Phase 2: Advanced Tag Filter (Next Steps)
- Click "Advanced" to expand advanced filtering
- Tag builder interface for complex queries
- Support for AND/OR operations
- Hierarchical tag selection

Example Advanced UI:
```
WHERE
  [Policy Area ▼] [is ▼] [Healthcare ▼]
  AND
  [Bill Type ▼] [is not ▼] [Resolution ▼]
  AND
  [Beneficiary ▼] [is one of ▼] [Veterans, Seniors ▼]
```

## API Design

### GET /api/tags
Returns all available tags with their types:
```json
{
  "tags": [
    {
      "id": 1,
      "name": "Healthcare",
      "type": "Policy Area",
      "parent_id": null,
      "children": [
        {
          "id": 2,
          "name": "Mental Health",
          "type": "Policy Area",
          "parent_id": 1
        }
      ]
    }
  ]
}
```

### GET /api/bills with tag filtering
Query parameters:
- `tags`: Comma-separated list of tag IDs
- `tag_operator`: "is", "is_not", "is_one_of", "is_not_one_of"
- `advanced_tag_filter`: JSON string for complex queries (Phase 2)

Example advanced filter JSON:
```json
{
  "operator": "AND",
  "conditions": [
    {
      "type": "Policy Area",
      "operator": "is",
      "value": "Healthcare"
    },
    {
      "type": "Bill Type",
      "operator": "is_not",
      "value": "Resolution"
    }
  ]
}
```

## Frontend Components

### TagFilter.js (Phase 1)
- Simple tag filter with operator selection
- Multi-select dropdown for tags
- Clear selection functionality
- URL state management

### AdvancedTagFilter.js (Phase 2)
- Complex query builder
- Hierarchical tag selection
- AND/OR condition builder
- Save/Load filter presets

## Migration Strategy (In Progress)

### Completed:
1. Created new schema tables
2. Added initial tag types and example tags
3. Added API endpoints for tag management
4. Implemented basic tag filtering UI

### Next Steps:

1. Create new schema tables while keeping existing tags column
2. Migrate existing tags to new structure
3. Update API to support both old and new tag formats
4. Gradually transition frontend to new tag system
5. Remove old tags column after complete migration

## Future Considerations (Upcoming)

1. Tag Analytics
   - Most used tags
   - Tag co-occurrence
   - Tag usage over time

2. Tag Management UI
   - Add/Edit/Disable tags
   - Merge similar tags
   - Tag usage statistics

3. Tag Validation
   - Prevent duplicate tags
   - Validate hierarchical relationships
   - Tag naming conventions

4. Tag-based Features
   - Bill recommendations
   - Related bills by tags
   - Tag-based visualizations

## Current Implementation Details

### Database Schema
The tag system is currently implemented with the following tables:
- `tag_types`: Stores different categories of tags (Policy Area, Bill Type, etc.)
- `tags`: Stores individual tags with hierarchical relationships
- `bill_tags`: Associates bills with their tags

### API Endpoints
1. GET /api/tags
   - Returns all available tags with their types
   - Supports hierarchical tag structure
   - Used by the tag filter component

2. GET /api/bills (updated)
   - Supports tag filtering with operators:
     * is: Exact match for a single tag
     * is_not: Exclude bills with specific tag
     * is_one_of: Match any of selected tags
     * is_not_one_of: Exclude bills with any selected tags

### Frontend Components
1. TagFilter.js
   - Operator selection dropdown
   - Tag selection with type display
   - Selected tags display with remove option
   - URL state persistence

2. Integration with BillsFilters.js
   - Tag filter takes 2 columns in the filter grid
   - Updates parent state with selected tags and operator
   - Resets to page 1 when filter changes

## How to Start Phase 2
To begin implementing the advanced tag filter:
1. Create new AdvancedTagFilter.js component
2. Add "Advanced" toggle button to BillsFilters.js
3. Implement complex query builder interface
4. Update API to support complex tag queries
5. Add filter preset functionality
