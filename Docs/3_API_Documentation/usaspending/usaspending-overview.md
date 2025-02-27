Pull all agency names, toptier agency codes, contracts counts, grants counts, payments counts, loans counts, etc. per agency.

Try count: curl 'https://api.usaspending.gov/api/v2/agency/awards/count/?fiscal_year=2020&page=1&limit=100'

curl 'https://api.usaspending.gov/api/v2/reporting/agencies/overview/?fiscal_year=2024&page=1&limit=100' > test4.json

# awards/counts API endpoint documentation:
FORMAT: 1A
HOST: https://api.usaspending.gov

# Count of awards for Agencies [/api/v2/agency/awards/count{?fiscal_year,group}]

Returns the count of Awards grouped by Award Type under Agencies

## GET

+ Request (application/json)
    + Schema

            {
                "$schema": "http://json-schema.org/draft-04/schema#",
                "type": "number"
            }
    + Parameters
        + `group` (optional, enum[string])
            Use `cfo` to get results where CFO designated agencies are returned. Otherwise use `all`.
            + Default: `all`
            + Members
                + `cfo`
                + `all`
        + `fiscal_year` (optional, number)
            The desired appropriations fiscal year. Defaults to the current FY
        + `order` (optional, enum[string])
            Indicates what direction results should be sorted by. Valid options include asc for ascending order or desc for descending order.
            + Default: `desc`
            + Members
                + `desc`
                + `asc`
        + `sort` (optional, enum[string])
            Optional parameter indicating what value results should be sorted by.
            + Default: `obligated_amount`
            + Members
                + `name`
                + `obligated_amount`
                + `gross_outlay_amount`
        + `page` (optional, number)
            The page number that is currently returned.
            + Default: 1
        + `limit` (optional, number)
            How many results are returned
            + Default: 10

+ Response 200 (application/json)
    + Attributes
        + `page_metadata` (required, PageMetadata, fixed-type)
            Information used for pagination of results.
        + `results` (required, array[AgencyResult], fixed-type)
        + `messages` (required, array[string], fixed-type)
            An array of warnings or instructional directives to aid consumers of this endpoint with development and debugging.

    + Body

            {
                "page_metadata": {
                    "limit": 1,
                    "page": 1,
                    "next": 2,
                    "previous": null,
                    "hasNext": false,
                    "hasPrevious": false,
                    "count": 10
                },
                "results": [
                    {
                    "awarding_toptier_agency_name": "Department of Defense",
                    "awarding_toptier_agency_code": "079",
                    "contracts": 2724,
                    "idvs": 45,
                    "grants": 0,
                    "direct_payments": 0,
                    "loans": 0,
                    "other": 0
                    }
                ],
                "messages": []
            }

# Data Structures

## AgencyResult (object)
+ `award_types` (required, AwardTypes, fixed-type)
+ `awarding_toptier_agency_name` (required, string)
+ `awarding_toptier_agency_code` (required, string)

## AwardTypes (object)
+ `grants` (required, number)
+ `loans` (required, number)
+ `contracts` (required, number)
+ `direct_payments` (required, number)
+ `other` (required, number)
+ `idvs` (required, number)

## PageMetadata (object)
+ `limit` (required, number)
+ `page` (required, number)
+ `next` (required, number, nullable)
+ `previous` (required, number, nullable)
+ `hasNext` (required, boolean)
+ `hasPrevious` (required, boolean)
+ `total` (required, number)
--------------------

# Agency Reporting

## Definitions and usage
### TAS
TAS stands for Treasury Account Symbol, which is a code that identifies a Treasury account. It's used to track and report federal spending. 
How is a TAS used?
The Treasury Department creates a TAS for each appropriations account created by Congress. 
All federal government financial transactions are classified by TAS. 
The TAS links a Treasury payment to a budget line item. 
What are the elements of a TAS? 
Agency Identifier (AID): A 3-digit code that identifies the agency responsible for the account
Main Account Code (MAC): A 4-digit code that identifies the account type and purpose
Sub Account Code (SAC): A 3-digit code that identifies a subdivision of the account
Allocation Transfer Agency ID (ATA): A 3-digit code that identifies the agency that receives funds through an allocation transfer
Beginning Period of Availability (BPOA): A 4-digit code that identifies the first year that an account can incur new obligations
The TAS is used to report to the Department of the Treasury and OMB. 

### TAFS

Per OMB Circular A-11 Section 20, “…TAFS refers to the separate Treasury accounts for each appropriation title based on the availability of the resources in the account. The TAFS is a combination of federal account symbol and availability code (e.g., annual, multi-year, or no-year).” TAFS and appropriations accounts are exactly the same.

### TAS v TAFS

The terms Treasury Appropriation Fund Symbol (TAFS) and Treasury Account Symbol (TAS) are integral to federal financial management, each serving distinct roles in the classification and reporting of government funds.

Treasury Appropriation Fund Symbol (TAFS):

Definition: TAFS represents individual appropriation accounts established by Congress, encompassing details such as the responsible agency, account purpose, and the time frame during which funds are available for obligation and expenditure. It combines the federal account symbol with an availability code indicating whether the funds are annual, multi-year, or no-year. 
FED SPENDING TRANSPARENCY
Treasury Account Symbol (TAS):

Definition: TAS is a comprehensive identification code assigned by the Department of the Treasury to track all financial transactions of the federal government. While it includes the components of TAFS, TAS also incorporates additional elements, notably the sub-account code, allowing for more granular tracking of funds within a main appropriation account. 
FED SPENDING TRANSPARENCY
Importance of Both TAFS and TAS in Federal Spending Reporting:

Utilizing both TAFS and TAS is crucial for accurate and transparent federal spending reporting:

Comprehensive Tracking: TAFS provides a broad overview of appropriations, while TAS offers detailed insights into specific allocations and expenditures within those appropriations, including sub-accounts. This dual-level tracking ensures that all financial activities are accurately recorded and reported.

Enhanced Transparency and Accountability: The inclusion of sub-account information in TAS allows for precise monitoring of how funds are utilized, facilitating greater transparency and accountability in government spending.

Standardization Across Agencies: The consistent use of TAFS and TAS across federal agencies standardizes financial reporting, enabling cohesive aggregation and analysis of data government-wide.

In summary, both TAFS and TAS are essential components of federal financial management. Their combined use ensures a detailed, transparent, and standardized approach to tracking and reporting government spending, thereby supporting effective oversight and informed decision-making.

## API Endpoint

Try: curl 'https://api.usaspending.gov/api/v2/reporting/agencies/overview/?fiscal_year=2024&page=1&limit=100'


FORMAT: 1A
HOST: https://api.usaspending.gov

# Agencies Reporting Overview [/api/v2/reporting/agencies/overview/{?fiscal_year,fiscal_period,filter,page,limit,order,sort}]

This endpoint is used to power USAspending.gov's About the Data \| Agencies Overview table. This data can be used to better understand the ways agencies submit data.

## GET

This endpoint returns an overview list of government agencies submission data.

+ Parameters

    + `fiscal_year`: 2020 (required, number)
        The fiscal year.
    + `fiscal_period`: 10 (required, number)
        The fiscal period. Valid values: 2-12 (2 = November ... 12 = September)
        For retriving quarterly data, provide the period which equals 'quarter * 3' (e.g. Q2 = P6)
    + `filter` (optional, string)
        The agency name or abbreviation to filter on (partial match, case insesitive).
    + `page` (optional, number)
        The page of results to return based on the limit.
        + Default: 1
    + `limit` (optional, number)
        The number of results to include per page.
        + Default: 10
    + `order` (optional, enum[string])
        The direction (`asc` or `desc`) that the `sort` field will be sorted in.
        + Default: `desc`
        + Members
            + `asc`
            + `desc`
    + `sort` (optional, enum[string])
        A data field that will be used to sort the response array.
        + Default: `current_total_budget_authority_amount`
        + Members
            + `toptier_code`
            + `current_total_budget_authority_amount`
            + `tas_accounts_total`
            + `missing_tas_accounts_count`
            + `agency_name`
            + `obligation_difference`
            + `recent_publication_date`
            + `recent_publication_date_certified`
            + `tas_obligation_not_in_gtas_total`
            + `unlinked_contract_award_count`
            + `unlinked_assistance_award_count`

+ Response 200 (application/json)

    + Attributes (object)
        + `page_metadata` (required, PaginationMetadata, fixed-type)
        + `results` (required, array[AgencyData], fixed-type)
        + `messages` (optional, array[string])
            An array of warnings or instructional directives to aid consumers of this endpoint with development and debugging.

    + Body

            {
                "page_metadata": {
                    "page": 1,
                    "next": 2,
                    "previous": 0,
                    "hasNext": false,
                    "hasPrevious": false,
                    "total": 2,
                    "limit": 10
                },
                "results": [
                    {
                        "agency_name": "Department of Health and Human Services",
                        "abbreviation": "DHHS",
                        "toptier_code": "020",
                        "agency_id": 123,
                        "current_total_budget_authority_amount": 8361447130497.72,
                        "recent_publication_date": "2020-01-10T11:59:21Z",
                        "recent_publication_date_certified": false,
                        "tas_account_discrepancies_totals": {
                            "gtas_obligation_total": 55234,
                            "tas_accounts_total": 23923,
                            "tas_obligation_not_in_gtas_total": 11543,
                            "missing_tas_accounts_count": 20
                        },
                        "obligation_difference": 436376232652.87,
                        "unlinked_contract_award_count": 3,
                        "unlinked_assistance_award_count": 2,
                        "assurance_statement_url": "https://files-nonprod.usaspending.gov/agency_submissions/Raw%20DATA%20Act%20Files/2020/P09/075%20-%20Department%20of%20Health%20and%20Human%20Services%20(HHS)/2020-P09-075_Department%20of%20Health%20and%20Human%20Services%20(HHS)-Assurance_Statement.txt"
                    },
                    {
                        "agency_name": "Department of Treasury",
                        "abbreviation": "DOT",
                        "toptier_code": "021",
                        "agency_id": 789,
                        "current_total_budget_authority_amount": 8361447130497.72,
                        "recent_publication_date": null,
                        "recent_publication_date_certified": true,
                        "tas_account_discrepancies_totals": {
                            "gtas_obligation_total": 66432,
                            "tas_accounts_total": 23913,
                            "tas_obligation_not_in_gtas_total": 11543,
                            "missing_tas_accounts_count": 10
                        },
                        "obligation_difference": 436376232652.87,
                        "unlinked_contract_award_count": 0,
                        "unlinked_assistance_award_count": 0,
                        "assurance_statement_url": "https://files-nonprod.usaspending.gov/agency_submissions/Raw%20DATA%20Act%20Files/2020/P09/020%20-%20Department%20of%20the%20Treasury%20(TREAS)/2020-P09-020_Department%20of%20the%20Treasury%20(TREAS)-Assurance_Statement.txt"
                    }
                ]
            }

# Data Structures

## PaginationMetadata (object)
+ `page` (required, number)
+ `next` (required, number, nullable)
+ `previous` (required, number, nullable)
+ `hasNext` (required, boolean)
+ `hasPrevious` (required, boolean)
+ `total` (required, number)
+ `limit` (required, number)

## TASTotals (object)
+ `gtas_obligation_total` (required, number, nullable)
+ `tas_accounts_total` (required, number, nullable)
+ `tas_obligation_not_in_gtas_total` (required, number, nullable)
+ `missing_tas_accounts_count` (required, number, nullable)

## AgencyData (object)
+ `agency_name` (required, string)
+ `abbreviation` (required, string)
+ `toptier_code` (required, string)
+ `agency_id` (required, number, nullable)
+ `current_total_budget_authority_amount` (required, number, nullable)
+ `recent_publication_date` (required, string, nullable)
+ `recent_publication_date_certified` (required, boolean)
+ `tas_account_discrepancies_totals` (required, array[TASTotals], fixed-type)
+ `obligation_difference` (required, number, nullable)
    The difference in File A and File B obligations.
+ `unlinked_contract_award_count` (required, number, nullable)
+ `unlinked_assistance_award_count` (required, number, nullable)
+ `assurance_statement_url` (required, string, nullable)