"""
tools.py: 
    Part of the example dicom2sphn package.
    It contains utility functions for the application.
"""
import re
import logging
import uuid
from datetime import datetime

 
def is_valid_string(string: str) -> bool:
    """
    Checks if the string is a normal non-empty string without leading and trailing spaces
    """

    # old: return (isinstance(string,str) and len(string) > 0 and len(string) == len(string.strip()))

    return isinstance(string,str) and re.match(r"^\S+(?: \S+)*$", string) is not None

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


def convert_and_merge_date_time(dicom_date: str, dicom_time: str, logger: logging.Logger, indent: int = 0) -> datetime|None:
    """
    Returns the datetime given a date and a time string obtained from DICOM
        dicom_date is the date string obtained from a DICOM SOP Instance,
        dicom_time is the time string obtained from a DICOM SOP Instance.
    """

    assert isinstance(dicom_date, str)
    assert isinstance(dicom_time, str)

    # DICOM DA date format: yyyymmdd, or in the old format: yyyy.mm.dd
    # Remove whitespace
    dicom_date_modified = dicom_date.strip()
    # Remove the dots in the old format
    dicom_date_modified = dicom_date_modified.replace('.','')
    
    # Check if the length/format is as expected
    if len(dicom_date_modified) < 8:
        logger.warning(" "*(indent+0) + f"DICOM date string shorter than expected (8 char) YYYYmmdd format: '{dicom_date_modified}'.")
        return None
    
    if len(dicom_date_modified) > 8:
        logger.warning(" "*(indent+0) + f"DICOM date string longer than expected (8 char) YYYYmmdd format: '{dicom_date_modified}'.")
        return None

    # Try to parse the string using YYYYmmdd format
    result_date = datetime.strptime(dicom_date_modified,"%Y%m%d").date()

    # DICOM TM time format: HHMMSS.frac or in the old format: HH:MM:SS.frac
    # The string may be padded with trailing spaces. 
    # The frac may be up to 6 positions
    # One or more components MM, SS, or frac may be unspecified as long as every component to the right is also unspecified
    
    # Remove whitespace
    dicom_time_modiefied = dicom_time.strip()
    # Remove the colons in the old format
    dicom_time_modiefied = dicom_time_modiefied.replace(':','')

    # Check if the length/format is as expected
    if len(dicom_time_modiefied) > 13:
        logger.warning(" "*(indent+0) + f"DICOM time string longer than expected (13 char) HHMMSS.frac format: '{dicom_time_modiefied}'.")
        return None
    
    if len(dicom_time_modiefied) > 7 and dicom_time_modiefied[6] == ".":
        # Try to parse the string using HHMMSS.f format
        result_time = datetime.strptime(dicom_time_modiefied, "%H%M%S.%f").time()
    
    elif len(dicom_time_modiefied) == 7 and dicom_time_modiefied[6] == ".":
        # Try to parse the string using HHMMSS. format
        result_time = datetime.strptime(dicom_time_modiefied, "%H%M%S.").time()
    
    elif len(dicom_time_modiefied) == 6:
        # Try to parse the string using HHMMSS format
        result_time = datetime.strptime(dicom_time_modiefied, "%H%M%S").time()
    
    elif len(dicom_time_modiefied) == 4:
        # Try to parse the string using HHMM format
        result_time = datetime.strptime(dicom_time_modiefied, "%H%M").time()
    
    elif len(dicom_time_modiefied) == 2:
        # Try to parse the string using HH format
        result_time = datetime.strptime(dicom_time_modiefied, "%H").time()
    
    else:
        logger.warning(" "*(indent+0) + f"DICOM time string different than expected HHMMSS.frac or HHMMSS. or HHMMSS or HHMM or HH format: '{dicom_time_modiefied}'.")
        return None

    # Merge date and time
    result_datetime = datetime.combine(result_date, result_time)

    return result_datetime


def generate_id() -> str:
    """
    Generates a unique ID
    """
    # Generate a unique id using '.hex' to have only the 32 hex values (without the dashes inbetween)
    return uuid.uuid4().hex
