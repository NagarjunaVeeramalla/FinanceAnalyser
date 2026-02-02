import re
from datetime import datetime
import pandas as pd

def parse_date(date_str):
    """
    Parses a date string into a standard YYYY-MM-DD format.
    Handles multiple formats:
    - DD/MM/YYYY
    - DD-MM-YYYY
    - DD-MMM-YYYY
    - YYYY-MM-DD
    """
    if not isinstance(date_str, str):
        return None

    date_str = date_str.strip()
    
    # List of formats to try
    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d-%b-%Y",
        "%d %b %Y",
        "%d %b %y",
        "%Y-%m-%d",
        "%d.%m.%Y"
    ]

    parsed_date = None
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            parsed_date = dt
            break
        except ValueError:
            continue
    
    # Try pandas parser as a fallback for complex cases
    if not parsed_date:
        try:
            dt = pd.to_datetime(date_str, dayfirst=True)
            parsed_date = dt
        except Exception:
            pass

    if parsed_date:
        # Validate Year (sanity check: 2000 to current_year + 1)
        # This prevents random numbers like "1736" or "400708" being interpreted as dates
        if 2000 <= parsed_date.year <= 2030:
            return parsed_date.strftime("%Y-%m-%d")

    return None
