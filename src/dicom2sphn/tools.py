"""
tools.py: 
    Part of the example dicom2sphn package.
    It contains utility functions for the application.
"""

import logging
import re
import uuid
from datetime import UTC, datetime
from typing import Any


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


def combine_dicom_date_and_time(dicom_date: str, dicom_time: str, logger: logging.Logger, indent: int = 0) -> datetime|None:
    """
    Returns the datetime given a date and a time string obtained from DICOM
        - dicom_date is the date string obtained from a DICOM SOP Instance,
        - dicom_time is the time string obtained from a DICOM SOP Instance.
    Note: DICOM DA date format: yyyymmdd, or old format: yyyy.mm.dd
          DICOM TM time format: HHMMSS.frac or in the old format: HH:MM:SS.frac
          - The string may be padded with trailing spaces. 
          - The frac may be up to 6 positions
          - One or more components MM, SS, or frac may be unspecified as long as every component to the right is also unspecified
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
    #result_date = datetime.strptime(dicom_date_modified,"%Y%m%d").date()
    result_date = datetime.strptime(dicom_date_modified,"%Y%m%d").replace(tzinfo=UTC).date()

    # DICOM TM time format: HHMMSS.frac or in the old format: HH:MM:SS.frac
    # The string may be padded with trailing spaces. 
    # The frac may be up to 6 positions
    # One or more components MM, SS, or frac may be unspecified as long as every component to the right is also unspecified
    
    # Remove whitespace
    dicom_time_modified = dicom_time.strip()
    # Remove the colons in the old format
    dicom_time_modified = dicom_time_modified.replace(':','')

    # Check if the length/format is as expected
    if len(dicom_time_modified) > 13:
        logger.warning(" "*(indent+0) + f"DICOM time string longer than expected (13 char) HHMMSS.frac format: '{dicom_time_modified}'.")
        return None
    
    if len(dicom_time_modified) > 7 and dicom_time_modified[6] == ".":
        # Try to parse the string using HHMMSS.f format
        result_time = datetime.strptime(dicom_time_modified, "%H%M%S.%f").replace(tzinfo=UTC).time()
    
    elif len(dicom_time_modified) == 7 and dicom_time_modified[6] == ".":
        # Try to parse the string using HHMMSS. format
        result_time = datetime.strptime(dicom_time_modified, "%H%M%S.").replace(tzinfo=UTC).time()
    
    elif len(dicom_time_modified) == 6:
        # Try to parse the string using HHMMSS format
        result_time = datetime.strptime(dicom_time_modified, "%H%M%S").replace(tzinfo=UTC).time()
    
    elif len(dicom_time_modified) == 4:
        # Try to parse the string using HHMM format
        result_time = datetime.strptime(dicom_time_modified, "%H%M").replace(tzinfo=UTC).time()
    
    elif len(dicom_time_modified) == 2:
        # Try to parse the string using HH format
        result_time = datetime.strptime(dicom_time_modified, "%H").replace(tzinfo=UTC).time()
    
    else:
        logger.warning(" "*(indent+0) + f"DICOM time string different than expected HHMMSS.frac or HHMMSS. or HHMMSS or HHMM or HH format: '{dicom_time_modified}'.")
        return None

    # Combine date and time
    result_datetime = datetime.combine(result_date, result_time, tzinfo=UTC)

    return result_datetime


def generate_id() -> str:
    """
    Generates a unique ID
    """
    # Generate a unique id using '.hex' to have only the 32 hex values (without the dashes inbetween)
    return uuid.uuid4().hex


def already_in_list(sphn_item: Any, sphn_item_list: list[Any]) -> bool:
    """
    Checks if the SPHN item is already in the SPHN item list
    Note: it requires the is_similar() method of the SPHN item to check for similarity
    """

    assert hasattr(sphn_item, "is_similar") and callable(sphn_item.is_similar), \
        "The sphn_item does not have an 'is_similar' method or it is not callable"
    
    # Check if list exists
    if sphn_item_list is None:
        return False
    
    for listed_item in sphn_item_list:
        if sphn_item.is_similar(listed_item):
            return True

    return False

def are_similar_lists(list1: list[Any], list2: list[Any]) -> bool:
    """
    Compares two lists for similarity regardless of item order. 
    Returns True if both lists contain similar items, False otherwise.
    """

    # Check if both lists are None
    if list1 is None and list2 is None:
        return True

    # Check if one of the lists is None
    if list1 is None or list2 is None:
        return False

    # Check if the lengths of the lists are different
    if len(list1) != len(list2):
        return False

    # Check each item in list1 against items in list2
    for item1 in list1:
        found_similar = False
        for item2 in list2:
            if hasattr(item1, "is_similar") and callable(item1.is_similar):
                if item1.is_similar(item2):
                    found_similar = True
                    break
            else:
                raise TypeError("The list item does not have an 'is_similar' method or it is not callable")
        
        if not found_similar:
            return False

    return True

# import collections

# l1 = [10, 20, 30, 40, 50]
# l2 = [20, 30, 50, 40, 70]
# l3 = [50, 20, 30, 40, 10]

# if collections.Counter(l1) == collections.Counter(l2):
#     print ("The lists l1 and l2 are the same")
# else:
#     print ("The lists l1 and l2 are not the same")

# if collections.Counter(l1) == collections.Counter(l3):
#     print ("The lists l1 and l3 are the same")
# else:
#     print ("The lists l1 and l3 are not the same")