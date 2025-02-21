Actions Level
<api-root>

The <api-root> is only present in the XML format.

<actions>

Parent container for all actions taken on a bill or resolution. Actions may come from the House, Senate, or Library of Congress. An <actions> element may include the following children:

<item>
Container for an action taken on a bill or resolution. An <item> element is repeatable and may include the following children:
<actionDate> (e.g. 2022-03-08)
The date of the action taken on a bill or resolution.
<actionTime>
The time of the action taken on a bill or resolution. Certain actions taken by the House contain this element.
<text> (e.g. Passed Senate without amendment by Yea-Nay Vote. 79 - 19. Record Vote Number: 71.)
The text of the action taken on a bill or resolution.
<type> (e.g. Floor)
A short name representing legislative process stages or categories of more detailed actions. Most types condense actions into sets. Some types are used for data processing and do not represent House or Senate legislative process activities.
Possible values are "Committee", "Calendars", "Floor", "BecameLaw", "IntroReferral", "President", "ResolvingDifferences", "Discharge", "NotUsed", and "Veto".
<actionCode>
An action code associated with the action taken on a bill or resolution.
The <actionCode> element will be present only for actions where the <sourceSystem> is 2 (House) or 9 (Library of Congress).
Action Codes is an authoritative list of values where the <sourceSystem> is 9 (Library of Congress).
An authoritative list of action codes where the <sourceSystem> is 2 (House) does not exist.
Various code sets are used by multiple systems in the House, Senate, and Library of Congress by legislative clerks and data editors for functions independent of this data set. As new codes and systems were developed, there was no coordinated effort to retroactively apply new codes to old records. Many codes are concatenated with other codes or elements or utilize free text. Codes in one set may be redundant with a different code in another code set. Additionally, some codes may have been used and re-used over the years for different purposes further complicating the ability to create an authoritative list. View the original code set of U.S. Congress legislative status steps.
<sourceSystem>
Container for the source system where the action was entered. A <sourceSystem> element may include the following children:
<code> (e.g. 0)
A code for the source system that entered the action.
Possible values are "0", "1", "2", or "9".
"0" is for Senate, "1" and "2" are for House, and "9" is Library of Congress.
<name> (e.g. Senate)
The name of the source system that entered the action.
Possible values are "Senate", "House committee actions", "House floor actions", and "Library of Congress".
<committees>
Container for committees associated with the action. A <committees> element may include the following children:
<item>
Container for a committee associated with the action. An <item> element is repeatable and may include the following children:
<url>
A referrer URL to the committee or subcommittee item in the API. Documentation for the committee endpoint is available here.
<systemCode>
A code associated with the committee or subcommittee used to match items in Congress.gov with the committee or subcommittee.
<name>
The name of the committee or subcommittee associated with the action.
<recordedVotes>
Container for recorded (roll call) votes associated with the action. Read more about roll call votes on Congress.gov. More information can also be found at the Roll Call Votes by the U.S. Congress and Votes in the House and Senate pages on Congress.gov.
A <recordedVotes> element may include the following children:
<recordedVote>
Container for a recorded (roll call) vote associated with the action. A <recordedVote> element may include the following children:
<rollNumber> (e.g. 70)
The recorded (roll call) vote number.
<url> (e.g. https://www.senate.gov/legislative/LIS/roll_call_votes/vote1172/vote_117_2_00070.xml)
The url to the recorded (roll call) vote on Senate.gov or Clerk.House.gov.
Note that the provided URL is for the XML format of the recorded (roll call) vote.
<chamber> (e.g. Senate)
The chamber where the recorded (roll call) vote took place.
Possible values are "House" and "Senate".
<congress> (e.g. 117)
The congress during which the recorded (roll call) vote took place.
<date> (e.g. 2022-03-08T22:45:05Z)
The date of the recorded (roll call) vote.
<sessionNumber> (e.g. 2)
The session of congress during which the recorded (roll call) vote took place.
<calendarNumber>
Container for calendar information associated with the action. Read more about calendars on Congress.gov.
A <calendarNumber> element may include the following children:
<calendar>
The calendar name (e.g. Senate Calendar of Business, U00171) associated with the action.
<number>
The Senate calendar number. Actions from the House associated with a calendar will not have a number value populated in this field.

-----

GET /bill/:congress/:billType/:billNumber/actions

Example Request

https://api.congress.gov/v3/bill/117/hr/3076/actions?api_key=[INSERT_KEY]

Example Request

{
    "actions": [
        {
            "actionCode": "36000",
            "actionDate": "2022-04-06",
            "sourceSystem": {
                "code": 9,
                "name": "Library of Congress"
            },
            "text": "Became Public Law No: 117-108.",
            "type": "BecameLaw"
        },
        {
            "actionCode": "E30000",
            "actionDate": "2022-04-06",
            "sourceSystem": {
                "code": 9,
                "name": "Library of Congress"
            },
            "text": "Signed by President.",
            "type": "President"
        },
    ],
}
Parameters
Try it out
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

