Below you'll find detailed API documentation for both the **GovTrack.us API** and the **ProPublica Congress API**. Each section includes a breakdown of endpoints, parameters, and example `curl` and Python commands to help you get started.

---

## **GovTrack.us API Documentation**

The GovTrack.us API provides access to comprehensive data about federal legislation, legislators, committees, and votes. The API is RESTful and returns data in JSON format.

### **Base URL**

```
https://www.govtrack.us/api/v2/
```

### **Authentication**

No API key or authentication is required to use the GovTrack.us API.

### **Endpoints Overview**

1. **People (Legislators)**
2. **Bills**
3. **Votes**
4. **Committees**
5. **Roles**

---

### **1. People (Legislators)**

**Endpoint**

```
GET /person
```

**Description**

Retrieve information about members of Congress, including biographical data and roles.

**Parameters**

- `current`: (`true` or `false`) Filter for current members.
- `state`: (State abbreviation, e.g., `CA`) Filter by state.
- `party`: (`Democrat`, `Republican`, etc.) Filter by political party.
- `fields`: Comma-separated list of fields to return.

**Example**

Retrieve current members of Congress from California.

**cURL**

```bash
curl "https://www.govtrack.us/api/v2/person?current=true&state=CA"
```

**Python**

```python
import requests

params = {
    'current': 'true',
    'state': 'CA'
}

response = requests.get('https://www.govtrack.us/api/v2/person', params=params)
data = response.json()
print(data)
```

---

### **2. Bills**

**Endpoint**

```
GET /bill
```

**Description**

Access data on federal legislation, including bill summaries, statuses, and sponsors.

**Parameters**

- `congress`: (e.g., `117`) Filter by Congress number.
- `current_status`: (e.g., `passed`, `enacted`) Filter by bill status.
- `sponsor`: (Person ID) Filter by sponsor's GovTrack ID.
- `introduced_date`: (`YYYY-MM-DD`) Filter by introduction date.
- `fields`: Comma-separated list of fields to return.

**Example**

Retrieve bills introduced in the 117th Congress.

**cURL**

```bash
curl "https://www.govtrack.us/api/v2/bill?congress=117"
```

**Python**

```python
import requests

params = {
    'congress': '117'
}

response = requests.get('https://www.govtrack.us/api/v2/bill', params=params)
data = response.json()
print(data)
```

---

### **3. Votes**

**Endpoint**

```
GET /vote
```

**Description**

Retrieve voting records, including individual votes and summaries.

**Parameters**

- `congress`: (e.g., `117`) Filter by Congress number.
- `chamber`: (`house` or `senate`) Filter by chamber.
- `category`: (`passage`, `cloture`, etc.) Filter by vote category.
- `created__gte`: (`YYYY-MM-DD`) Votes created after a certain date.
- `fields`: Comma-separated list of fields to return.

**Example**

Retrieve recent votes in the House.

**cURL**

```bash
curl "https://www.govtrack.us/api/v2/vote?chamber=house&sort=-created"
```

**Python**

```python
import requests

params = {
    'chamber': 'house',
    'sort': '-created'
}

response = requests.get('https://www.govtrack.us/api/v2/vote', params=params)
data = response.json()
print(data)
```

---

### **4. Committees**

**Endpoint**

```
GET /committee
```

**Description**

Get information about congressional committees and subcommittees.

**Parameters**

- `obsolete`: (`true` or `false`) Filter out obsolete committees.
- `parent`: (Committee ID) Filter by parent committee.
- `fields`: Comma-separated list of fields to return.

**Example**

Retrieve current committees.

**cURL**

```bash
curl "https://www.govtrack.us/api/v2/committee?obsolete=false"
```

**Python**

```python
import requests

params = {
    'obsolete': 'false'
}

response = requests.get('https://www.govtrack.us/api/v2/committee', params=params)
data = response.json()
print(data)
```

---

### **5. Roles**

**Endpoint**

```
GET /role
```

**Description**

Access detailed information about the roles (terms) of members of Congress.

**Parameters**

- `current`: (`true` or `false`) Filter for current roles.
- `person`: (Person ID) Filter by legislator's GovTrack ID.
- `fields`: Comma-separated list of fields to return.

**Example**

Retrieve current roles.

**cURL**

```bash
curl "https://www.govtrack.us/api/v2/role?current=true"
```

**Python**

```python
import requests

params = {
    'current': 'true'
}

response = requests.get('https://www.govtrack.us/api/v2/role', params=params)
data = response.json()
print(data)
```

---

### **Additional Notes**

- **Pagination**: The API supports pagination. Use `limit` and `offset` parameters to control the number of results.
- **Fields**: Use the `fields` parameter to specify which fields to include in the response.
- **Sorting**: Use the `sort` parameter to sort results (e.g., `sort=-created` for descending order).
- **Full Documentation**: For more details, visit the [GovTrack.us API Documentation](https://www.govtrack.us/developers/api).

---

## **ProPublica Congress API Documentation**

The ProPublica Congress API provides access to a wide range of congressional data, including bills, votes, members, and committees. An API key is required to use this service.

### **Base URL**

```
https://api.propublica.org/congress/v1/
```

### **Authentication**

- **API Key**: Obtain an API key by registering at [ProPublica Congress API](https://www.propublica.org/datastore/api/propublica-congress-api).
- **Headers**: Include your API key in the request header as `X-API-Key`.

### **Endpoints Overview**

1. **Members**
2. **Bills**
3. **Votes**
4. **Committees**
5. **Nominations**
6. **Statements**

---

### **1. Members**

#### **List Members of a Chamber**

**Endpoint**

```
GET /{congress}/{chamber}/members.json
```

- **{congress}**: Congress number (e.g., `117`)
- **{chamber}**: `house` or `senate`

**Example**

Retrieve current members of the Senate in the 117th Congress.

**cURL**

```bash
curl "https://api.propublica.org/congress/v1/117/senate/members.json" \
  -H "X-API-Key: YOUR_API_KEY"
```

**Python**

```python
import requests

url = 'https://api.propublica.org/congress/v1/117/senate/members.json'
headers = {'X-API-Key': 'YOUR_API_KEY'}

response = requests.get(url, headers=headers)
data = response.json()
print(data)
```

---

#### **Get Member Details**

**Endpoint**

```
GET /members/{member-id}.json
```

- **{member-id}**: ProPublica ID of the member (e.g., `A000360`)

**Example**

Retrieve details for Senator Tammy Baldwin.

**cURL**

```bash
curl "https://api.propublica.org/congress/v1/members/B001230.json" \
  -H "X-API-Key: YOUR_API_KEY"
```

**Python**

```python
import requests

url = 'https://api.propublica.org/congress/v1/members/B001230.json'
headers = {'X-API-Key': 'YOUR_API_KEY'}

response = requests.get(url, headers=headers)
data = response.json()
print(data)
```

---

### **2. Bills**

#### **Retrieve Recent Bills**

**Endpoint**

```
GET /{congress}/{chamber}/bills/{type}.json
```

- **{congress}**: Congress number (e.g., `117`)
- **{chamber}**: `house` or `senate`
- **{type}**: `introduced`, `updated`, `passed`, `enacted`, `vetoed`

**Example**

Retrieve bills recently introduced in the House.

**cURL**

```bash
curl "https://api.propublica.org/congress/v1/117/house/bills/introduced.json" \
  -H "X-API-Key: YOUR_API_KEY"
```

**Python**

```python
import requests

url = 'https://api.propublica.org/congress/v1/117/house/bills/introduced.json'
headers = {'X-API-Key': 'YOUR_API_KEY'}

response = requests.get(url, headers=headers)
data = response.json()
print(data)
```

---

#### **Get Bill Details**

**Endpoint**

```
GET /bills/{bill-id}.json
```

- **{bill-id}**: Bill identifier (e.g., `hr1234`)

**Example**

Retrieve details for bill H.R.1234.

**cURL**

```bash
curl "https://api.propublica.org/congress/v1/bills/hr1234.json" \
  -H "X-API-Key: YOUR_API_KEY"
```

**Python**

```python
import requests

url = 'https://api.propublica.org/congress/v1/bills/hr1234.json'
headers = {'X-API-Key': 'YOUR_API_KEY'}

response = requests.get(url, headers=headers)
data = response.json()
print(data)
```

---

### **3. Votes**

#### **Retrieve Recent Votes**

**Endpoint**

```
GET /{congress}/{chamber}/votes/recent.json
```

- **{congress}**: Congress number (e.g., `117`)
- **{chamber}**: `house` or `senate`

**Example**

Retrieve recent votes in the Senate.

**cURL**

```bash
curl "https://api.propublica.org/congress/v1/117/senate/votes/recent.json" \
  -H "X-API-Key: YOUR_API_KEY"
```

**Python**

```python
import requests

url = 'https://api.propublica.org/congress/v1/117/senate/votes/recent.json'
headers = {'X-API-Key': 'YOUR_API_KEY'}

response = requests.get(url, headers=headers)
data = response.json()
print(data)
```

---

#### **Get Roll Call Vote Details**

**Endpoint**

```
GET /{congress}/{chamber}/sessions/{session-number}/votes/{roll-call-number}.json
```

- **{congress}**: Congress number (e.g., `117`)
- **{chamber}**: `house` or `senate`
- **{session-number}**: Session number (`1` or `2`)
- **{roll-call-number}**: Roll call vote number

**Example**

Retrieve details for Senate roll call vote number 15 in session 1 of the 117th Congress.

**cURL**

```bash
curl "https://api.propublica.org/congress/v1/117/senate/sessions/1/votes/15.json" \
  -H "X-API-Key: YOUR_API_KEY"
```

**Python**

```python
import requests

url = 'https://api.propublica.org/congress/v1/117/senate/sessions/1/votes/15.json'
headers = {'X-API-Key': 'YOUR_API_KEY'}

response = requests.get(url, headers=headers)
data = response.json()
print(data)
```

---

### **4. Committees**

#### **List Committees**

**Endpoint**

```
GET /{congress}/{chamber}/committees.json
```

- **{congress}**: Congress number (e.g., `117`)
- **{chamber}**: `house`, `senate`, or `joint`

**Example**

Retrieve current House committees.

**cURL**

```bash
curl "https://api.propublica.org/congress/v1/117/house/committees.json" \
  -H "X-API-Key: YOUR_API_KEY"
```

**Python**

```python
import requests

url = 'https://api.propublica.org/congress/v1/117/house/committees.json'
headers = {'X-API-Key': 'YOUR_API_KEY'}

response = requests.get(url, headers=headers)
data = response.json()
print(data)
```

---

#### **Get Committee Details**

**Endpoint**

```
GET /committees/{committee-id}.json
```

- **{committee-id}**: Committee code (e.g., `HSAG` for House Agriculture Committee)

**Example**

Retrieve details for the Senate Armed Services Committee.

**cURL**

```bash
curl "https://api.propublica.org/congress/v1/committees/SSAS.json" \
  -H "X-API-Key: YOUR_API_KEY"
```

**Python**

```python
import requests

url = 'https://api.propublica.org/congress/v1/committees/SSAS.json'
headers = {'X-API-Key': 'YOUR_API_KEY'}

response = requests.get(url, headers=headers)
data = response.json()
print(data)
```

---

### **5. Nominations**

**Endpoint**

```
GET /{congress}/nominations/{type}.json
```

- **{congress}**: Congress number (e.g., `117`)
- **{type}**: `received`, `updated`, `confirmed`

**Example**

Retrieve recently confirmed nominations.

**cURL**

```bash
curl "https://api.propublica.org/congress/v1/117/nominations/confirmed.json" \
  -H "X-API-Key: YOUR_API_KEY"
```

**Python**

```python
import requests

url = 'https://api.propublica.org/congress/v1/117/nominations/confirmed.json'
headers = {'X-API-Key': 'YOUR_API_KEY'}

response = requests.get(url, headers=headers)
data = response.json()
print(data)
```

---

### **6. Statements**

**Endpoint**

```
GET /statements/latest.json
```

**Description**

Retrieve the latest statements from members of Congress.

**Example**

**cURL**

```bash
curl "https://api.propublica.org/congress/v1/statements/latest.json" \
  -H "X-API-Key: YOUR_API_KEY"
```

**Python**

```python
import requests

url = 'https://api.propublica.org/congress/v1/statements/latest.json'
headers = {'X-API-Key': 'YOUR_API_KEY'}

response = requests.get(url, headers=headers)
data = response.json()
print(data)
```

---

### **Additional Notes**

- **Rate Limits**: The API allows up to 5000 requests per day.
- **Errors**: If you exceed rate limits or provide incorrect parameters, the API will return an error message.
- **Data Updates**: The data is updated regularly to reflect the most recent congressional activities.
- **Full Documentation**: For more details and additional endpoints, visit the [ProPublica Congress API Documentation](https://projects.propublica.org/api-docs/congress-api/).

---

**Remember to replace `YOUR_API_KEY` with the actual API key you receive after registering with ProPublica.**

If you need further assistance with additional APIs or have questions about specific endpoints, feel free to ask!