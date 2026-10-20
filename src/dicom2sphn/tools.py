"""
tools.py: 
    Part of the example dicom2sphn package.
    It contains utility functions for the application.
"""

import logging
import re
import uuid
from datetime import UTC

from pydicom.valuerep import DA, DT, TM


def is_valid_string(string: str) -> bool:
    """
    Checks if the string is a normal non-empty string without leading and trailing spaces
    """

    #return (isinstance(string,str) and len(string) > 0 and len(string) == len(string.strip()))
    #return isinstance(string,str) and re.match(r"^\S+(?: \S+)*$", string) is not None

    return (isinstance(string,str) and len(string) > 0 and len(string) == len(string.strip()))


def is_clean_string(string: str) -> bool:
    """
    Checks if the string is a normal non-empty string without leading and trailing spaces and without special characters
    """
    return isinstance(string,str) and re.match(r"^[A-Za-z0-9]+$", string) is not None


def make_clean(input: str) -> str:

    # Checks
    assert is_valid_string(input)

    # Remove all characters except A-Z, a-z, 0-9        
    output = re.sub(r"[^A-Za-z0-9]", "", input, flags=re.UNICODE)

    return output


def combine_dicom_date_and_time(dicom_date: str, dicom_time: str, logger: logging.Logger, indent: int = 0) -> DT|None:
    """
    Returns the DICOM datetime (DT) object given a date and a time string obtained from DICOM
        - dicom_date is the date string obtained from a DICOM SOP Instance,
        - dicom_time is the time string obtained from a DICOM SOP Instance.
    Note: DICOM date (DA) format or YYYY[MM[DD]], or old format: YYYY[.MM[.DD]]
          - The string may be padded with trailing spaces. 
          - One or more components MM or DD may be unspecified as long as every component to the right is also unspecified
          - Any timezone information in the DICOM date string will be ignored.
          DICOM time (TM) format or [HH[MM[SS[.frac]]]] or in the old format: [HH[:MM[:SS[.frac]]]]
          - The string may be padded with trailing spaces. 
          - The frac may be up to 6 positions (FFFFFF)
          - One or more components HH, MM, SS, or frac may be unspecified as long as every component to the right is also unspecified
          - Any timezone information in the DICOM time string will be ignored.
          The resulting datetime will be completed to a full DICOM DT datetime (DT) in UTC.
          - If any component of the date or time is missing, it will be assumed to be the earliest valid value (e.g., month=01, day=01, hour=00, minute=00, second=00).
    """

    assert isinstance(dicom_date, str)
    assert isinstance(dicom_time, str)

    if not dicom_date or not dicom_time:
        logger.debug(" "*(indent+0) + "DICOM date or time string is empty.")
        return None

    dicom_date_modified = complete_dicom_date(dicom_date, logger, indent=indent)
    if dicom_date_modified is None:
        return None

    dicom_time_modified = complete_dicom_time(dicom_time, logger, indent=indent)
    if dicom_time_modified is None:
        return None

    # At this point, both dicom_date_modified and dicom_time_modified are complete and valid.

    # Parse the DICOM date string YYYYMMDD into a datetime.date object.
    try:
        dicom_dt= DT.combine(dicom_date_modified, dicom_time_modified, tzinfo=UTC)
    except ValueError as e:
        logger.debug(" "*(indent+0) + f"Failed to combine DICOM date (DA) and DICOM time (TM) to a DICOM datetime (DT): {e}")
        return None

    return dicom_dt


def complete_dicom_date(dicom_date: str, logger: logging.Logger, indent: int=0) -> DA|None:
    """
    Completes a DICOM date string by filling in missing components with default values.
    The resulting DICOM DA object will have the format YYYYMMDD.
    Note:
    - If any component of the date is missing, it will be assumed to be the earliest valid value (e.g., month=01, day=01).
    - Any timezone information in the DICOM date string will be ignored.

    Args:
        dicom_date (str): The DICOM date string to complete: YYYY[MM[DD]], or old format: YYYY[.MM[.DD]]
        logger (logging.Logger): Logger for debug and warning messages.
        indent (int, optional): Indentation level for log messages. Defaults to 0.

    Returns:
        DA|None: The completed DICOM date object, or None if the input is invalid.
    """
    assert isinstance(dicom_date, str)

    # Remove whitespace
    d_str = dicom_date.strip()

    # Remove the dots in the old format
    d_str = d_str.replace('.','')

    # Dates should not have a timezone
    # Separate the timezone information if present (+HHMM or -HHMM)
    tz_match = re.search(r'([+-]\d{4})$', d_str)
    tz_suffix = tz_match.group(1) if tz_match else ""

    if tz_match:
        logger.debug(" "*(indent+0) + f"Removed timezone information in DICOM date string: '{tz_suffix}'.")

    # Get the pure date string without the timezone
    pure_d = d_str[:-5] if tz_match else d_str

    # Determine how many components we already have
    length = len(pure_d)

    # Complete the date string to YYYYMMDD format
    if length == 4:
        pure_d += "0101"  # YYYY -> YYYYMMDD
        logger.debug(" "*(indent+0) + "Completed DICOM date string from YYYY to YYYYMMDD by assuming month=01, day=01.")
    elif length == 6:
        pure_d += "01"  # YYYYMM -> YYYYMMDD
        logger.debug(" "*(indent+0) + "Completed DICOM date string from YYYYMM to YYYYMMDD by assuming day=01.")
    elif length == 8:
        pass  # Already YYYYMMDD
    else:
        logger.debug(" "*(indent+0) + f"DICOM date string has unexpected length YYYY[MM[DD]]: '{pure_d}'.")
        return None

    # Try to parse the complete date string
    try:
        dicom_d = DA(pure_d)
    except ValueError as e:
        logger.debug(" "*(indent+0) + f"Failed to parse DICOM date string: '{pure_d}'. Error: {e}")
        return None

    return dicom_d


def complete_dicom_time(dicom_time: str, logger: logging.Logger, indent: int=0) -> TM|None:
    """
    Completes a DICOM time string by filling in missing components with default values.
    The resulting TM object will have the format HHMMSS, optionally with milliseconds.
    Note:
    - If any component of the time is missing, it will be assumed to be the earliest valid value (e.g., hours=00, minutes=00, seconds=00).
    - Any timezone information in the DICOM time string will be ignored.

    Args:
        dicom_time (str): The DICOM time string to complete: [HH[MM[SS[.FFFFFF]]]], or old format: [HH[:MM[:SS[.FFFFFF]]]]
        logger (logging.Logger): Logger for debug and warning messages.
        indent (int, optional): Indentation level for log messages. Defaults to 0.

    Returns:
        TM|None: The completed DICOM time object, or None if the input is invalid.
    """
    assert isinstance(dicom_time, str)

    # Remove whitespace
    t_str = dicom_time.strip()

    # Remove the colons in the old format
    t_str = t_str.replace(':','')

    # It should not have a timezone according to the DICOM time (TM) format
    # Separate the timezone information if present (+HHMM or -HHMM)
    tz_match = re.search(r'([+-]\d{4})$', t_str)
    tz_suffix = tz_match.group(1) if tz_match else ""

    if tz_match:
        logger.debug(" "*(indent+0) + f"Removed timezone information in DICOM time string: '{tz_suffix}'.")

    # Get the pure time string without the timezone and without any milliseconds (.FFFFFF)
    pure_t = t_str[:-5] if tz_match else t_str
    if '.' in pure_t:
        pure_t, ms_part = pure_t.split('.', 1)
        ms_suffix = f".{ms_part}"
    else:
        ms_suffix = ""

    # Determine how many components we already have
    length = len(pure_t)

    # Complete the time string to HHMMSS format
    if length == 0:
        pure_t = "000000"  # 'empty' -> HHMMSS
        logger.debug(" "*(indent+0) + "Completed DICOM time string from empty to HHMMSS by assuming HH=00, MM=00, SS=00.")
    elif length == 2:
        pure_t += "0000"  # HH -> HHMMSS
        logger.debug(" "*(indent+0) + "Completed DICOM time string from HH to HHMMSS by assuming minutes=00, seconds=00.")
    elif length == 4:
        pure_t += "00"  # HHMM -> HHMMSS
        logger.debug(" "*(indent+0) + "Completed DICOM time string from HHMM to HHMMSS by assuming seconds=00.")
    elif length == 6:
        pass  # Already HHMMSS
    else:
        logger.debug(" "*(indent+0) + f"DICOM time string has unexpected length for HH[MM[SS]]]]] part: '{pure_t}'.")
        return None

    # Concatenate the pure time with any milliseconds back together. Without the timezone.
    total_t = f"{pure_t}{ms_suffix}"

    # Try to parse the complete time string
    try:
        dicom_t = TM(total_t)
    except ValueError as e:
        logger.debug(" "*(indent+0) + f"Failed to parse DICOM time string: '{total_t}'. Error: {e}")
        return None

    return dicom_t


def complete_dicom_datetime(dicom_datetime: str, logger: logging.Logger, indent: int=0) -> DT|None:
    """
    Completes a DICOM datetime string by filling in missing components with default values.
    The resulting DT object will have the format YYYYMMDDHHMMSS, optionally with milliseconds and timezone.
    Note:
    - If any component of the datetime is missing, it will be assumed to be the earliest valid value (e.g., month=01, day=01, hours=00, minutes=00, seconds=00).
    - Any timezone information in the DICOM datetime string will be preserved.
    Args:
        dicom_datetime (str): The DICOM datetime string to complete.
        logger (logging.Logger): Logger for debug and warning messages.
        indent (int, optional): Indentation level for log messages. Defaults to 0.

    Returns:
        DT|None: The completed DICOM datetime object, or None if the input is invalid.
    """
    assert isinstance(dicom_datetime, str)

    # Remove whitespace
    dt_str = dicom_datetime.strip()
    
    # YYYYMMDDHHMMSS.FFFFFF&ZZXX => pure datetime: YYYYMMDDHHMMSS, milliseconds: .FFFFFF, timezone: &ZZXX, &=-/+

    # Separate the timezone information if present (+HHMM or -HHMM)
    tz_match = re.search(r'([+-]\d{4})$', dt_str)
    tz_suffix = tz_match.group(1) if tz_match else ""
    
    # Get the pure datetime string without the timezone and without any milliseconds (.FFFFFF)
    pure_dt = dt_str[:-5] if tz_match else dt_str
    if '.' in pure_dt:
        pure_dt, ms_part = pure_dt.split('.', 1)
        ms_suffix = f".{ms_part}"
    else:
        ms_suffix = ""

    # The standards per position (total length must be 14 characters for YYYYMMDDHHMMSS)
    # Position 4-5: month ('01'), Position 6-7: day ('01'), the rest is hours/minutes/seconds ('00')
    
    # Determine how many components we already have
    length = len(pure_dt)

    # Complete the date time string to YYYYMMDDHHMMSS format
    if length == 4:    # YYYY -> YYYYMMDDHHMMSS
        pure_dt += "0101000000"
        logger.debug(" "*(indent+0) + "DICOM datetime string has only a YYYY component, filling with default MMDDHHMMSS=0101000000.")
    elif length == 6:  # YYYYMM -> YYYYMMDDHHMMSS
        pure_dt += "01000000"
        logger.debug(" "*(indent+0) + "DICOM datetime string has only a YYYYMM component, filling with default DDHHMMSS=01000000.")
    elif length == 8:  # YYYYMMDD -> YYYYMMDDHHMMSS
        pure_dt += "000000"
        logger.debug(" "*(indent+0) + "DICOM datetime string has only a YYYYMMDD component, filling with default HHMMSS=000000.")
    elif length == 10: # YYYYMMDDHH -> YYYYMMDDHHMMSS
        pure_dt += "0000"
        logger.debug(" "*(indent+0) + "DICOM datetime string has only a YYYYMMDDHH component, filling with default MMSS=0000.")
    elif length == 12: # YYYYMMDDHHMM -> YYYYMMDDHHMMSS
        pure_dt += "00"
        logger.debug(" "*(indent+0) + "DICOM datetime string has only a YYYYMMDDHHMM component, filling with default SS=00.")
    elif length == 14: # YYYYMMDDHHMMSS
        pass  # Already complete
    else:
        logger.debug(" "*(indent+0) + f"DICOM datetime string has unexpected length for YYYY[MM[DD[HH[MM[SS]]]]] part: '{pure_dt}'.")
        return None
        
    # Concatenate the pure datetime, any milliseconds, and the timezone back together
    total_dt = f"{pure_dt}{ms_suffix}{tz_suffix}" 

    # Try to parse the complete datetime string
    try:
        dicom_dt = DT(total_dt)
    except ValueError as e:
        logger.debug(" "*(indent+0) + f"Failed to parse DICOM datetime string: '{total_dt}'. Error: {e}")
        return None
    
    return dicom_dt


def generate_id() -> str:
    """
    Generates a unique ID
    """
    # Generate a unique id using '.hex' to have only the 32 hex values (without the dashes inbetween)
    return uuid.uuid4().hex
