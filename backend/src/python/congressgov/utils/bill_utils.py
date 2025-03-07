"""
Bill-specific utilities for processing bill data.
"""

import re
from typing import Tuple, Optional

def normalize_bill_status(action_text: str) -> Optional[str]:
    """
    Map action text to a normalized status value.
    
    Args:
        action_text: Text of the latest action
        
    Returns:
        Normalized status string
    """
    if not action_text:
        return None
        
    action_text = action_text.lower()
    
    # Direct matches first
    if any(term in action_text for term in ['became public law', 'became law']):
        return 'Became Law'
    elif any(term in action_text for term in ['enacted', 'approved by president']):
        return 'Enacted'
    elif 'passed' in action_text:
        if 'house' in action_text:
            return 'Passed House'
        elif 'senate' in action_text:
            return 'Passed Senate'
    
    # Calendar placements indicate progress beyond committee
    if 'placed on' in action_text and 'calendar' in action_text:
        if 'senate' in action_text:
            return 'Reported'  # Senate calendar placement typically follows committee reporting
        elif 'union calendar' in action_text:
            return 'Reported'  # House Union Calendar is for reported bills
        
    # Committee actions
    if any(term in action_text for term in ['reported', 'ordered to be reported']):
        return 'Reported'
    elif any(term in action_text for term in ['referred to', 'committee']):
        return 'In Committee'
    elif 'held at the desk' in action_text:
        return 'In Committee'  # Bills held at the desk are awaiting committee referral
        
    # Introduction status
    if any(term in action_text for term in ['introduced', 'introduction']):
        return 'Introduced'
    
    # Motion outcomes often indicate passage
    if 'motion to reconsider laid on the table agreed to' in action_text:
        if 'house' in action_text:
            return 'Passed House'
        elif 'senate' in action_text:
            return 'Passed Senate'
    
    return None

def parse_bill_number(bill_number: str) -> Tuple[str, str]:
    """
    Parse a bill number into its components.
    
    Args:
        bill_number: Full bill number (e.g., 'HR1234', 'S42', 'SJRES33')
        
    Returns:
        Tuple of (bill_type, bill_number)
    """
    # Use regex to separate letters from numbers
    match = re.match(r'^([a-zA-Z]+)(\d+)$', bill_number)
    if match:
        return match.group(1).lower(), match.group(2)
    
    # If regex fails, try character by character
    for i, c in enumerate(bill_number):
        if c.isdigit():
            return bill_number[:i].lower(), bill_number[i:]
    
    # Return the whole string as type if no numbers found
    return bill_number.lower(), ''

def get_bill_status_hierarchy() -> dict:
    """
    Get the hierarchical ordering of bill statuses.
    Higher values indicate further progress in the legislative process.
    
    Returns:
        Dictionary mapping status strings to numeric values
    """
    return {
        'Introduced': 10,
        'In Committee': 20,
        'Reported': 30,
        'Passed House': 40,
        'Passed Senate': 40,
        'Passed Both Chambers': 50,
        'Enacted': 60,
        'Became Law': 70
    }

def get_bill_url(congress: int, bill_type: str, bill_number: str) -> str:
    """
    Generate a URL for viewing a bill on Congress.gov.
    
    Args:
        congress: Congress number
        bill_type: Type of bill (e.g., 'hr', 's', 'hjres')
        bill_number: Bill number
        
    Returns:
        URL string
    """
    return f"https://www.congress.gov/bill/{congress}th-congress/{bill_type}/{bill_number}"