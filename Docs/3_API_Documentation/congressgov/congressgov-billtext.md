## From congress.gov's github documentation:

- `<textVersions>`
  - Container for text of the bill or resolution. Read more [About Legislation Text](https://www.congress.gov/help/legislation-text) on Congress.gov.
  - A `<textVersions>` element may include the following children:
    - `<count>` (e.g. 7)
      - The number of texts for the bill or resolution.
    - `<url>` (e.g. <https://api.congress.gov/v3/bill/117/hr/3076/text>)
      - A referrer URL to the text level of the bill API. See below for more information about the text level.

#### Text Level

`<api-root>`

The `<api-root>` is only present in the XML format.

`<textVersions>`

Parent container for text versions associated with the bill or resolution. Read more about bill text at [About Legislation Text of the U.S. Congress](https://www.congress.gov/help/legislation-text). A `<textVersions>` element may include the following children:

- `<item>`
  - Container for a text version associated with the bill or resolution. An `<item>` element is repeatable and may include the following children:
    - `<type>` (e.g. Introduced in House)
      - The bill text version type.
    - `<date>` (e.g. 2021-05-11T04:00:00Z)
      - The date associated with the text version. This date is associated with the date of action, not the printing date.
    - `<formats>`
      - Container for formats of the text version. A `<formats>` element may include the following children:
        - `<item>`
          - Container for a format of the text version. An `<item>` element is repeatable and may include the following children:
            - `<url>` (e.g. <https://www.congress.gov/117/bills/hr3076/BILLS-117hr3076ih.xml>)
              - The URL for the text version format in Congress.gov.
            - `<type>` (e.g. Formatted XML)
              - The type of bill text version format.
              - Possible values are "Formatted Text", "PDF", and "Formatted XML". Note that not all format types are available for all text versions.

## From Congress.gov API docs

GET /bill/:congress/:billType/:billNumber/text

Example Request

https://api.congress.gov/v3/bill/117/hr/3076/text?api_key=[INSERT_KEY]

Example Response

 {
    "textVersions": [
        {
            "date": null,
            "formats": [
                {
                    "type": "Formatted Text",
                    "url": "https://www.congress.gov/117/bills/hr3076/BILLS-117hr3076enr.htm"
                },
                {
                    "type": "PDF",
                    "url": "https://www.congress.gov/117/bills/hr3076/BILLS-117hr3076enr.pdf"
                },
                {
                    "type": "Formatted XML",
                    "url": "https://www.congress.gov/117/bills/hr3076/BILLS-117hr3076enr.xml"
                }
            ],
            "type": "Enrolled Bill"
        },
        {
            "date": "2022-02-15T05:00:00Z",
            "formats": [
                {
                    "type": "Formatted Text",
                    "url": "https://www.congress.gov/117/bills/hr3076/BILLS-117hr3076pcs2.htm"
                },
                {
                    "type": "PDF",
                    "url": "https://www.congress.gov/117/bills/hr3076/BILLS-117hr3076pcs2.pdf"
                },
                {
                    "type": "Formatted XML",
                    "url": "https://www.congress.gov/117/bills/hr3076/BILLS-117hr3076pcs2.xml"
                }
            ],
            "type": "Placed on Calendar Senate"
        },
    ]
 }
Parameters

Name	Description
congress *
integer
(path)
The congress number. For example, the value can be 117.

billType *
string
(path)
The type of bill. Value can be hr, s, hjres, sjres, hconres, sconres, hres, or sres.

billNumber *
integer
(path)
The bill’s assigned number. For example, the value can be 3076.

format
string
(query)
The data format. Value can be xml or json.

offset
integer
(query)
The starting record returned. 0 is the first record.

limit
integer
(query)
The number of records returned. The maximum limit is 250.