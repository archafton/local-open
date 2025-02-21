LegiScan API Crash Course
One last thing, please take a minute and read...
Print this page
Query Limits
Public API keys have 30,000 queries to spend per month
The query counter resets on the first day of each month
Timing guidelines for each operation on Page 7 of the LegiScan API Manual should be followed
Recommend local caching of JSON response to minimize spend on replayability
Datasets
All individual getBill, getRollCall and getPerson JSON payloads in a single ZIP file for each legislative session
Created weekly on Sunday morning at 5am Eastern
Approximately 900 API queries for 3,500,000+ data records for 2010-current
ZIP archive files are Base64 encoded in their JSON transport
Texts & Documents
Bill documents are available via getBillText, getAmendment and getSupplement hooks
Necessary doc_id, amendment_id, supplement_id identifiers are availble in getBill payloads
Documents are Base64 encoded in their JSON transport
One-time ML training snapshot of 300GB text data available as separate service
Hashes
32-character hash values are available to detect data changes and optimize query spend
change_hash + bill_id for bill data; available in getBill, getMasterList, getSearch, getMasterListRaw, getSearchRaw
dataset_hash + session_id for dataset archives; available in getDatasetList, getDataset
Store and compare hash values, if hash is the same the data is the same so use local cache and avoid query spend
Work Loop
Typical loop driven by checking getMasterListRaw or getSearchRaw periodically
Use change_hash in the results to determine when to spend queries updating individual data
Repeat getMasterListRaw or getSearchRaw daily/weekly or as needed within query spend
Turnkey LegiScan API Client available to processes Pull, Push and Bulk data into a defined SQL schema
Housekeeping
Scraping legiscan.com front end site is prohibited and will result in suspended access
Creating multiple public service keys is prohibited and will result in suspended access
All data is licensed under Creative Commons Attribution 4.0; do as you like but you must give LegiScan attribution
Play nice!


-----

Created: 2025-02-20
Expires: Never

API Type: Pull (Free Public Service)
API Status: Available

Pull Throttle: Yes (30,000 monthly query limit)

February Requests: 0
Lifetime Requests: 0
Push & Pull API Subscription Services

Subscription Inquiry
Subscription Price List
API Documentation and Reference

LegiScan API Manual
LegiScan API Static Lookups
LegiScan API Weekly Datasets
LegiScan API Client Documentation
LegiScan API Client (legiscan-1.4.1.tar.gz)
LegiScan API by LegiScan LLC is licensed under CC BY 4.0

Sample Pull API Calls (Note document blobs and datasets are Base64 encoded for JSON transport):

getDatasetList	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getDatasetList&state=WA
getDataset	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getDataset&access_key=UShKXiOK6FJo22qUHcZer&id=2166
getSessionList	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getSessionList&state=WA
getSessionPeople	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getSessionPeople&id=2166
getMonitorListRaw	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getMonitorListRaw&record=current
getMonitorList	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getMonitorList&record=all
getMasterListRaw	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getMasterListRaw&id=2166
getMasterList	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getMasterList&id=2166
getBill	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getBill&id=1977770
getBillText	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getBillText&id=3133642
getAmendment	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getAmendment&id=230514
getSupplement	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getSupplement&id=524796
getRollCall	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getRollCall&id=1495098
getPerson	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getPerson&id=26386
getSearch	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getSearch&state=WA&query=tax
getSearchRaw	https://api.legiscan.com/?key=c752c951cc7e6f7df80d2ebc04673ed1&op=getSearchRaw&state=WA&query=tax