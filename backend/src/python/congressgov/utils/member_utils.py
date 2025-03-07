"""
Member-related utilities for processing Congress.gov data.
"""

import re
import logging
from datetime import datetime, date
from typing import Dict, Any, Tuple, Optional, List

# Set up logging
logger = logging.getLogger(__name__)

def parse_member_name(name: str) -> Dict[str, str]:
    """
    Parse a member name into components.
    
    Args:
        name: Member name (e.g., "Smith, John", "Johnson, John Q.")
        
    Returns:
        Dictionary with name components (last_name, first_name, middle_name)
    """
    if not name:
        return {"last_name": "", "first_name": "", "middle_name": ""}
    
    # Handle name format: "Last, First Middle"
    parts = name.split(', ', 1)
    last_name = parts[0].strip() if parts else ""
    
    first_name = ""
    middle_name = ""
    
    if len(parts) > 1:
        first_parts = parts[1].split(' ', 1)
        first_name = first_parts[0].strip() if first_parts else ""
        
        if len(first_parts) > 1:
            middle_name = first_parts[1].strip()
    
    return {
        "last_name": last_name,
        "first_name": first_name,
        "middle_name": middle_name
    }

def format_full_name(first_name: str, middle_name: str, last_name: str, suffix: str = None) -> str:
    """
    Format name components into a full name.
    
    Args:
        first_name: First name
        middle_name: Middle name or initial
        last_name: Last name
        suffix: Name suffix (e.g., Jr., III)
        
    Returns:
        Formatted full name
    """
    name_parts = [part for part in [first_name, middle_name, last_name] if part]
    full_name = " ".join(name_parts)
    
    if suffix:
        full_name = f"{full_name}, {suffix}"
    
    return full_name

def format_display_name(member_data: Dict[str, Any]) -> str:
    """
    Format member data into a display name based on available fields.
    
    Args:
        member_data: Dictionary with member data
        
    Returns:
        Formatted display name
    """
    if 'full_name' in member_data and member_data['full_name']:
        return member_data['full_name']
    
    if 'short_title' in member_data and member_data['short_title']:
        title = member_data['short_title']
    elif 'chamber' in member_data:
        title = "Sen." if member_data['chamber'].lower() == 'senate' else "Rep."
    else:
        title = ""
    
    name_parts = []
    if title:
        name_parts.append(title)
    
    if 'first_name' in member_data and member_data['first_name']:
        name_parts.append(member_data['first_name'])
    
    if 'last_name' in member_data and member_data['last_name']:
        name_parts.append(member_data['last_name'])
    
    if not name_parts:
        return "Unknown Member"
    
    return " ".join(name_parts)

def normalize_state_code(state: str) -> str:
    """
    Normalize state code to two-letter uppercase format.
    
    Args:
        state: State name or code
        
    Returns:
        Two-letter state code
    """
    if not state:
        return ""
    
    # State name to code mapping
    state_map = {
        "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", 
        "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
        "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID", 
        "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
        "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD", 
        "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
        "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV", 
        "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
        "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", 
        "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
        "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT", 
        "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
        "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
        "american samoa": "AS", "guam": "GU", "northern mariana islands": "MP",
        "puerto rico": "PR", "virgin islands": "VI"
    }
    
    # If already a 2-letter code
    if len(state) == 2:
        return state.upper()
    
    # Try lookup by name
    state_key = state.lower().strip()
    if state_key in state_map:
        return state_map[state_key]
    
    # Return original if unknown
    logger.warning(f"Unknown state: {state}")
    return state

def get_district_display(state: str, district: Optional[int], chamber: str) -> str:
    """
    Format state and district for display.
    
    Args:
        state: State code
        district: District number or None for Senate
        chamber: 'senate' or 'house'
        
    Returns:
        Formatted district display (e.g., "TX-10", "WY-AL")
    """
    if not state:
        return ""
    
    state_code = normalize_state_code(state)
    
    # For senators or at-large representatives
    if chamber.lower() == 'senate' or district is None:
        return state_code
    
    # Regular district
    if district == 0:
        return f"{state_code}-AL"  # At-large
    else:
        return f"{state_code}-{district}"

def parse_party_name(party: str) -> Tuple[str, str]:
    """
    Parse party name into standardized name and code.
    
    Args:
        party: Party name
        
    Returns:
        Tuple of (party_name, party_code)
    """
    if not party:
        return ("", "")
    
    party_lower = party.lower().strip()
    
    # Map common variations to standard values
    party_map = {
        "republican": ("Republican", "R"),
        "r": ("Republican", "R"),
        "gop": ("Republican", "R"),
        
        "democrat": ("Democrat", "D"),
        "democratic": ("Democrat", "D"),
        "d": ("Democrat", "D"),
        
        "independent": ("Independent", "I"),
        "i": ("Independent", "I"),
        
        "libertarian": ("Libertarian", "L"),
        "l": ("Libertarian", "L"),
        
        "green": ("Green", "G"),
        "g": ("Green", "G")
    }
    
    if party_lower in party_map:
        return party_map[party_lower]
    
    # Check for partial matches
    for key, value in party_map.items():
        if key in party_lower:
            return value
    
    # If no match, return original with uppercase first letter as code
    return (party, party[0].upper() if party else "")

def get_current_congress() -> int:
    """
    Get the current Congress number based on the current date.
    
    Returns:
        Current Congress number
    """
    # First Congress: March 4, 1789
    # Each Congress is 2 years
    # 117th Congress: January 3, 2021 - January 3, 2023
    
    today = date.today()
    
    # Base calculation on 117th Congress in 2021-2022
    current_year = today.year
    congress_offset = (current_year - 2021) // 2
    
    # Check if we're in first or second year of Congress
    if current_year % 2 == 1:
        # Odd year, definitely new Congress
        return 117 + congress_offset
    else:
        # Even year
        if today.month > 1 or (today.month == 1 and today.day >= 3):
            # After January 3rd, still same Congress
            return 117 + congress_offset
        else:
            # Before January 3rd, previous Congress
            return 117 + congress_offset - 1

def year_to_date(year: Optional[str]) -> Optional[date]:
    """
    Convert a year to a date object (January 1st of that year).
    
    Args:
        year: Year as string or None
        
    Returns:
        Date object or None
    """
    if year is None:
        return None
    try:
        return date(int(year), 1, 1)
    except ValueError:
        return None

def get_leadership_title(position: str) -> str:
    """
    Format a leadership position into a display title.
    
    Args:
        position: Leadership position
        
    Returns:
        Formatted leadership title
    """
    if not position:
        return ""
    
    # Standard leadership titles
    title_map = {
        "speaker": "Speaker of the House",
        "majority leader": "Majority Leader",
        "minority leader": "Minority Leader",
        "majority whip": "Majority Whip",
        "minority whip": "Minority Whip",
        "president pro tempore": "President Pro Tempore",
        "conference chair": "Conference Chair",
        "policy committee chair": "Policy Committee Chair"
    }
    
    position_lower = position.lower().strip()
    
    if position_lower in title_map:
        return title_map[position_lower]
    
    # Check for partial matches
    for key, value in title_map.items():
        if key in position_lower:
            return value
    
    # If no match, return original with first letter capitalized
    return position.strip()

def get_member_url(bioguide_id: str) -> str:
    """
    Generate a URL for viewing a member on Congress.gov.
    
    Args:
        bioguide_id: Bioguide ID
        
    Returns:
        URL string
    """
    return f"https://www.congress.gov/member/{bioguide_id}"

def get_member_committees(bioguide_id: str) -> List[Dict[str, Any]]:
    """
    Get committee assignments for a member.
    This would typically fetch from database but is stubbed for now.
    
    Args:
        bioguide_id: Bioguide ID
        
    Returns:
        List of committee dictionaries
    """
    # This would be implemented to fetch from database
    return []