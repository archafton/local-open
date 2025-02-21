## From congress.gov's github documentation:

- `<summaries>`
  - Container for bill summaries, written by CRS legislative analysts, on the bill or resolution. Read more [about bill summaries](https://www.congress.gov/help/legislative-glossary#glossary_billsummary) on Congress.gov.
  - A `<summaries>` element may include the following children:
    - `<count>` (e.g. 5)
      - The number of bill summaries on the bill or resolution.
    - `<url>` (e.g. <https://api.congress.gov/v3/bill/117/hr/3076/summaries>)
      - A referrer URL to the summaries level of the bill API. See below for more information about the summaries level.

#### Summaries Level

`<api-root>`

The `<api-root>` is only present in the XML format.

`<summaries>`

Parent container for bill summaries on the bill or resolution. Bill summaries are written by legislative analysts in CRS. Read more [about bill summaries](https://www.congress.gov/help/legislative-glossary#glossary_billsummary) on Congress.gov. Read more about the summaries endpoint [here](https://github.com/LibraryOfCongress/api.congress.gov/blob/main/Documentation/SummariesEndpoint.md).

A `<summaries>` element may include the following children:

- `<summary>`
  - Container for a bill summary on the bill or resolution. A `<summary>` element may include the following children:
    - `<versionCode>` (e.g. 00)
      - The internal code used by CRS to tag its summaries according to the action associated with the summary.
      - Click [here](#bill-summary-version-codes-action-descriptions-and-chamber) for a list of codes. Note that the version codes have varied over time.
    - `<actionDate>` (e.g. 2021-05-11)
      - The date of action associated with the bill summary.
    - `<actionDesc>` (e.g. Introduced in House)
      - The description of the action associated with the bill summary.
    - `<updateDate>` (e.g. 2021-06-07T20:24:30Z)
      - The update date for the bill summary on Congress.gov. This may be the date the summary was published or re-published. The `<updateDate>` is the date of the last update received for the legislative entity .  It’s not a date corresponding to the legislative date or legislative action date.  
    - `<text>` (e.g. `<![CDATA[ <p><strong>Postal Service Reform Act of 2021</strong></p> <p>This bill addresses the finances and operations of the U.S. Postal Service (USPS).</p> <p>The bill requires the Office of Personnel Management to establish the Postal Service Health Benefits Program for USPS employees and retirees and provides for coordinated enrollment of retirees under this program and Medicare. The bill repeals the requirement that the USPS annually prepay future retirement health benefits.</p> <p>Additionally, the USPS may establish a program to enter into agreements with an agency of any state government, local government, or tribal government, and with other government agencies, to provide certain nonpostal products and services that reasonably contribute to the costs of the USPS and meet other specified criteria.</p> <p>The USPS must develop and maintain a publicly available dashboard to track service performance and must report regularly on its operations and financial condition.</p> <p>The Postal Regulatory Commission must annually submit to the USPS a budget of its expenses. It must also conduct a study to identify the causes and effects of postal inefficiencies relating to flats (e.g., large envelopes).</p> <p>The USPS Office of Inspector General shall perform oversight of the Postal Regulatory Commission.</p> <ul> <ul> </ul> </ul> ]]>`)
      - The text of the bill summary.
      - Note that the text is encased in CDATA and contains HTML codes (e.g. `<p>`). The HTML codes may not be valid (see [#2](https://github.com/LibraryOfCongress/api.congress.gov/issues/2)); efforts are underway to improve the validity of the HTML codes.

##### Bill summary version codes, action descriptions, and chamber

| versionCode | actionDesc | chamber |
| ----------- | ---------- | ------- |
| 00 | Introduced in House | House |
| 00 | Introduced in Senate | Senate |
| 01 | Reported to Senate with amendment(s) | Senate |
| 02 | Reported to Senate amended, 1st committee reporting | Senate |
| 03 | Reported to Senate amended, 2nd committee reporting | Senate |
| 04 | Reported to Senate amended, 3rd committee reporting | Senate |
| 07 | Reported to House | House |
| 08 | Reported to House, Part I | House |
| 09 | Reported to House, Part II | House |
| 12 | Reported to Senate without amendment, 1st committee reporting | Senate |
| 13 | Reported to Senate without amendment, 2nd committee reporting | Senate |
| 17 | Reported to House with amendment(s) | House |
| 18 | Reported to House amended, Part I | House |
| 19 | Reported to House amended Part II | House |
| 20 | Reported to House amended, Part III | House |
| 21 | Reported to House amended, Part IV | House |
| 22 | Reported to House amended, Part V | House |
| 25 | Reported to Senate | Senate |
| 28 | Reported to House without amendment, Part I | House |
| 29 | Reported to House without amendment, Part II | House |
| 31 | Reported to House without amendment, Part IV | House |
| 33 | Laid on table in House | House |
| 34 | Indefinitely postponed in Senate | Senate |
| 35 | Passed Senate amended | Senate |
| 36 | Passed House amended | House |
| 37 | Failed of passage in Senate | Senate |
| 38 | Failed of passage in House | House |
| 39 | Senate agreed to House amendment with amendment | Senate |
| 40 | House agreed to Senate amendment with amendment | House |
| 43 | Senate disagreed to House amendment | Senate |
| 44 | House disagreed to Senate amendment | House |
| 45 | Senate receded and concurred with amendment | Senate |
| 46 | House receded and concurred with amendment | House |
| 47 | Conference report filed in Senate | Senate |
| 48 | Conference report filed in House | House |
| 49 | Public Law | |
| 51 | Line item veto by President | |
| 52 | Passed Senate amended, 2nd occurrence | Senate |
| 53 | Passed House | House |
| 54 | Passed House, 2nd occurrence | House |
| 55 | Passed Senate | Senate |
| 56 | Senate vitiated passage of bill after amendment | Senate |
| 58 | Motion to recommit bill as amended by Senate | Senate |
| 59 | House agreed to Senate amendment | House |
| 60 | Senate agreed to House amendment with amendment, 2nd occurrence | Senate |
| 62 | House agreed to Senate amendment with amendment, 2nd occurrence | House |
| 66 | House receded and concurred with amendment, 2nd occurrence | House |
| 70 | House agreed to Senate amendment without amendment | House |
| 71 | Senate agreed to House amendment without amendment | Senate |
| 74 | Senate agreed to House amendment | Senate |
| 77 | Discharged from House committee | House |
| 78 | Discharged from Senate committee | Senate |
| 79 | Reported to House without amendment | House |
| 80 | Reported to Senate without amendment | Senate |
| 81 | Passed House without amendment | House |
| 82 | Passed Senate without amendment | Senate |
| 83 | Conference report filed in Senate, 2nd conference report | Senate |
| 86 | Conference report filed in House, 2nd conference report | House |
| 87 | Conference report filed in House, 3rd conference report | House |

