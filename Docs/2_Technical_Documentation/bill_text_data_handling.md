# Bill Text Data Handling

## Special Cases

### 1. Null Dates
Text versions sometimes come with null dates, particularly for "Enrolled Bill" versions:
```json
{
  "date": null,
  "type": "Enrolled Bill",
  "formats": [...]
}
```

**Handling Strategy:**
- Store null date versions with introduced_date from bill details
- Display at top of timeline
- Mark as "Initial Version" or actual type (e.g., "Enrolled Bill")

### 2. Multiple Versions per Date
Example from SJRES33 (2021-12-14):
```json
[
  {
    "date": "2021-12-14T05:00:00Z",
    "type": "Engrossed in Senate"
  },
  {
    "date": "2021-12-14T05:00:00Z",
    "type": "Placed on Calendar Senate"
  }
]
```

**Handling Strategy:**
- Sort by type importance:
  1. Public Law
  2. Enrolled Bill
  3. Engrossed in Senate/House
  4. Placed on Calendar
- Display all versions for same date in timeline
- Use type as secondary sort key

### 3. Format Types
Different format types and their display:
```json
"formats": [
  {
    "type": "Formatted Text",  // Display as "HTML"
    "url": "...enr.htm"
  },
  {
    "type": "PDF",            // Keep as "PDF"
    "url": "...enr.pdf"
  },
  {
    "type": "Formatted XML",  // Display as "XML"
    "url": "...enr.xml"
  }
]
```

**Handling Strategy:**
- Map display names:
  * "Formatted Text" → "HTML"
  * "Formatted XML" → "XML"
  * Keep "PDF" as is
- Consistent button/link styling per format
- Handle different XML suffixes (`_uslm.xml` vs `.xml`)

### 4. URL Patterns
Different URL patterns for bills vs laws:
```javascript
// Bill version URL
"https://www.congress.gov/117/bills/sjres33/BILLS-117sjres33enr.htm"

// Public Law URL
"https://www.congress.gov/117/plaws/publ73/PLAW-117publ73.htm"
```

**Handling Strategy:**
- Validate URLs before storage
- Store complete URLs rather than constructing them
- Consider caching frequently accessed formats

## Data Processing

### 1. Date Handling
```javascript
// Normalize dates for comparison
const normalizeDate = (date) => {
  if (!date) return null;
  return new Date(date).toISOString().split('T')[0];
};

// Sort versions by date
const sortTextVersions = (versions) => {
  return versions.sort((a, b) => {
    if (!a.date) return -1;  // null dates first
    if (!b.date) return 1;
    return new Date(b.date) - new Date(a.date);
  });
};
```

### 2. Action Matching
```javascript
// Match text versions with actions
const findMatchingAction = (textVersion, actions) => {
  const date = normalizeDate(textVersion.date);
  return actions.find(action => 
    normalizeDate(action.actionDate) === date &&
    actionTypeMatches(action.type, textVersion.type)
  );
};

// Match action types with text version types
const actionTypeMatches = (actionType, versionType) => {
  const matches = {
    'BecameLaw': 'Public Law',
    'President': 'Enrolled Bill',
    'Floor': ['Engrossed in Senate', 'Engrossed in House']
  };
  return matches[actionType]?.includes(versionType) || false;
};
```

### 3. Database Storage
```sql
-- Example structure for text_versions JSONB
{
  "versions": [
    {
      "date": "2021-12-16",
      "type": "Public Law",
      "formats": [
        {
          "type": "HTML",
          "url": "..."
        }
      ],
      "action_id": "123"  -- Reference to matching action
    }
  ]
}
```

### 4. Frontend Display
```javascript
// Timeline entry component
const TimelineEntry = ({ action, textVersion }) => (
  <div className="timeline-entry">
    <div className="date">{formatDate(action.date)}</div>
    <div className="action">{action.text}</div>
    {textVersion && (
      <div className="text-version">
        {textVersion.formats.map(format => (
          <a 
            href={format.url}
            key={format.type}
            className={`format-link ${format.type.toLowerCase()}`}
          >
            View {formatType(format.type)}
          </a>
        ))}
      </div>
    )}
  </div>
);

// Format type display mapping
const formatType = (type) => {
  const displayNames = {
    'Formatted Text': 'HTML',
    'Formatted XML': 'XML',
    'PDF': 'PDF'
  };
  return displayNames[type] || type;
};
```

## Processing Pipeline

### 1. Data Fetching
```python
def fetch_text_versions(congress, bill_type, bill_number):
    """Fetch text versions from Congress.gov API"""
    url = f"{API_BASE_URL}/{congress}/{bill_type}/{bill_number}/text"
    response = requests.get(url, params={'api_key': API_KEY})
    return response.json()
```

### 2. Data Processing
```python
def process_text_versions(text_data, actions):
    """Process text versions and match with actions"""
    versions = text_data['textVersions']
    
    # Handle null dates
    for version in versions:
        if version['date'] is None:
            intro_action = next(
                (a for a in actions if a['type'] == 'Introduction'),
                None
            )
            if intro_action:
                version['date'] = intro_action['actionDate']
    
    # Match versions with actions
    for version in versions:
        matching_action = find_matching_action(version, actions)
        if matching_action:
            version['action_id'] = matching_action['id']
    
    return versions
```

### 3. Database Update
```python
def update_text_versions(cur, bill_number, versions):
    """Update text versions in database"""
    cur.execute("""
        UPDATE bills 
        SET text_versions = %s::jsonb 
        WHERE bill_number = %s
    """, (json.dumps(versions), bill_number))
```

## Related Documentation
- [Bill Text Implementation](bill_text_implementation.md) - Current status and issues
- [Bill Text Architecture](bill_text_architecture.md) - Proposed new architecture and storage details
