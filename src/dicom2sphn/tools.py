"""
tools.py: 
    Part of the example dicom2sphn package.
    It contains utility functions for the application.
"""

import logging
import re
import uuid
from datetime import datetime, time, timedelta, timezone, tzinfo

from pydicom import Dataset
from pydicom.valuerep import DA, DT, TM

from .data_converter import DataConverter


def is_valid_string(string: str) -> bool:
    """
    Checks if the string is a normal non-empty string without leading and trailing spaces
    """

    #return (isinstance(string,str) and len(string) > 0 and len(string) == len(string.strip()))
    #return isinstance(string,str) and re.match(r"^\S+(?: \S+)*$", string) is not None

    return (isinstance(string,str) and len(string) > 0 and len(string) == len(string.strip()))


def get_lookup_coding_scheme_designator(coding_scheme_designator: str) -> str:
    """
    Returns the coding scheme designator to use for looking up a DICOM code in the DataConverter mapping dictionaries.
    The retired designator "SNM3" is replaced by "SRT", as both are used in older DICOM data for the same SNOMED-RT codes.
    Other designators are returned unchanged (the case is kept, as some mapping keys use mixed case, e.g.: "NCIt").
    Parameters:
        - coding_scheme_designator: The coding scheme designator as found in DICOM (e.g.: "SCT", "SRT", "SNM3")
    Returns:
        - The coding scheme designator to use as the first item of the lookup key (e.g.: "SCT", "SRT")
    """

    assert is_valid_string(coding_scheme_designator)

    return "SRT" if coding_scheme_designator.upper() == "SNM3" else coding_scheme_designator


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


def get_dicom_timezone(dataset: Dataset, local_timezone: tzinfo, logger: logging.Logger, indent: int = 0) -> tzinfo:
    """
    Returns the timezone to use for the (local) DICOM dates and times in the dataset:
        - the fixed offset from the DICOM TimezoneOffsetFromUTC (0008,0201) tag, if present and valid,
        - otherwise the configured local timezone (e.g. ZoneInfo("Europe/Zurich")), which also handles daylight saving time.
    """
    assert isinstance(dataset, Dataset)
    assert isinstance(local_timezone, tzinfo)

    value = dataset.get("TimezoneOffsetFromUTC", None)
    if value is None or str(value).strip() == "":
        return local_timezone

    offset_str = str(value).strip()

    # Format: &ZZXX, with & = '+' or '-', ZZ = hours and XX = minutes
    match = re.fullmatch(r"([+-])(\d{2})(\d{2})", offset_str)
    if match is None or int(match.group(2)) > 14 or int(match.group(3)) > 59:
        logger.warning(" "*(indent+0) + f"DICOM TimezoneOffsetFromUTC tag value '{offset_str}' is invalid, using the configured local timezone '{local_timezone}' instead.")
        return local_timezone

    sign = -1 if match.group(1) == "-" else 1
    offset = timedelta(hours=int(match.group(2)), minutes=int(match.group(3)))

    logger.debug(" "*(indent+0) + f"Using DICOM TimezoneOffsetFromUTC tag value '{offset_str}' as timezone.")

    return timezone(sign * offset)


def combine_dicom_date_and_time(dicom_date: str, dicom_time: str, tz: tzinfo, logger: logging.Logger, indent: int = 0) -> DT|None:
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
          The resulting datetime will be completed to a full DICOM DT datetime (DT) in the timezone tz
          (see get_dicom_timezone(), as DICOM dates and times are local times).
          - If any component of the date or time is missing, it will be assumed to be the earliest valid value (e.g., month=01, day=01, hour=00, minute=00, second=00).
    """

    assert isinstance(dicom_date, str)
    assert isinstance(dicom_time, str)
    assert isinstance(tz, tzinfo)

    if not dicom_date:
        logger.debug(" "*(indent+0) + "DICOM date string is empty.")
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
        dicom_dt= DT.combine(dicom_date_modified, dicom_time_modified, tzinfo=tz)
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


def complete_dicom_datetime(dicom_datetime: str, tz: tzinfo, logger: logging.Logger, indent: int=0) -> DT|None:
    """
    Completes a DICOM datetime string by filling in missing components with default values.
    The resulting DT object will have the format YYYYMMDDHHMMSS, optionally with milliseconds and timezone.
    Note:
    - If any component of the datetime is missing, it will be assumed to be the earliest valid value (e.g., month=01, day=01, hours=00, minutes=00, seconds=00).
    - Any timezone information in the DICOM datetime string will be preserved.
    - Without timezone information in the DICOM datetime string, the timezone tz is used (see get_dicom_timezone()).
    Args:
        dicom_datetime (str): The DICOM datetime string to complete.
        tz (tzinfo): The timezone to use if the DICOM datetime string has no timezone (see get_dicom_timezone()).
        logger (logging.Logger): Logger for debug and warning messages.
        indent (int, optional): Indentation level for log messages. Defaults to 0.

    Returns:
        DT|None: The completed DICOM datetime object, or None if the input is invalid.
    """
    assert isinstance(dicom_datetime, str)
    assert isinstance(tz, tzinfo)

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

    # DICOM datetimes without a timezone suffix are local times
    if dicom_dt.tzinfo is None:
        dicom_dt = DT.combine(dicom_dt.date(), dicom_dt.time(), tzinfo=tz)

    return dicom_dt


#
# Edwin 2026-10-16 (moved from dicom_contrast_bolus_module_reader.get_contrast_bolus_datetime on 2026-11-13)
#
def combine_dicom_time_with_reference_datetime(
        dicom_time: time,
        acquisition_datetime: datetime|None,
        series_datetime: datetime|None,
        study_datetime: datetime|None,
        logger: logging.Logger,
        indent: int=0
    ) -> datetime|None:
    """
    Returns the estimated datetime of a DICOM time only value (e.g. a contrast/bolus or radiopharmaceutical start time),
    by combining it with the date of a reference datetime, adjusted for potential midnight boundary crossings.
    Parameters:
        dicom_time (datetime.time): The DICOM time, e.g. of the contrast/bolus or radiopharmaceutical injection.
        acquisition_datetime (datetime|None): The datetime of the acquisition.
        series_datetime (datetime|None): The datetime of the series.
        study_datetime (datetime|None): The datetime of the study.
        logger (logging.Logger): Logger for debug and warning messages.
        indent (int): The indentation level for logging.

    Returns:
        datetime|None: The estimated datetime, adjusted for potential midnight boundary crossings. Returns None if insufficient information is provided.

    Note: At least one of acquisition_datetime, series_datetime, or study_datetime must be provided.
    The time is a local time in the same timezone as the reference (acquisition, series, or study) datetime.
    """
    assert isinstance(dicom_time, time)
    assert acquisition_datetime is None or isinstance(acquisition_datetime, datetime)
    assert series_datetime is None or isinstance(series_datetime, datetime)
    assert study_datetime is None or isinstance(study_datetime, datetime)
    assert isinstance(indent, int) and indent >= 0

    # 1. Validate input parameters and ensure at least one datetime is provided
    if acquisition_datetime is None and series_datetime is None and study_datetime is None:
        logger.warning(" "*(indent+0) + "At least one of acquisition_datetime, series_datetime, or study_datetime must be provided.")
        return None

    # 2. Select the reference datetime: the acquisition, series, or study datetime
    reference_datetime = acquisition_datetime if acquisition_datetime else series_datetime if series_datetime else study_datetime

    # 3. Use whole seconds only, to ensure a uniform comparison
    reference_dt = reference_datetime.replace(microsecond=0)
    time_dt = datetime.combine(reference_dt.date(), dicom_time.replace(microsecond=0, tzinfo=None), tzinfo=reference_datetime.tzinfo)

    # 4. Handle Both Midnight Scenarios (Forward and Reverse Crossings)
    time_difference = time_dt - reference_dt.replace(tzinfo=reference_datetime.tzinfo)

    # Scenario A: The time looks like it is 23+ hours AFTER the reference
    # (Real world: Time right BEFORE midnight, the reference (e.g. scan) right AFTER midnight)
    if time_difference.total_seconds() > 82800:
        time_dt = time_dt - timedelta(days=1)

    # Scenario B: The time looks like it is 23+ hours BEFORE the reference
    # (Real world: The reference (e.g. scan) right BEFORE midnight, the time right AFTER midnight)
    elif time_difference.total_seconds() < -82800:
        time_dt = time_dt + timedelta(days=1)

    # Scenario C: Normal daytime workflow or same-day post-midnight operations
    # No adjustments needed, the calendar date matches perfectly.

    logger.debug(" "*(indent+0) + f"Combined the DICOM time '{dicom_time!s}' with the reference datetime '{reference_datetime!s}': '{time_dt!s}'")

    return time_dt


#
# Edwin 2026-10-28 (moved from dicom_contrast_bolus_module_reader.extract_administration_routes on 2026-11-13)
#
def extract_administration_routes_from_text(route_string: str, logger: logging.Logger, indent: int=0) -> list[dict]:
    """
    Extracts administration route codes from a (free text) route string, e.g. of the DICOM Contrast/Bolus Route or Radiopharmaceutical Route tag.
    The routes are matched with DataConverter.route_patterns and coded with DataConverter.sphn_route_codes.
    Parameters:
        - route_string: The (free text) administration route string.
        - logger: Logger for debug and warning messages.
        - indent: The indentation level for logging (default is 0)
    Returns:
        - A list of dictionaries containing the matched administration routes ("Route") and their corresponding Codes ("Code").
    """

    assert is_valid_string(route_string)
    assert isinstance(indent, int)

    # Ensure that every route pattern has a corresponding code in the DataConverter class
    assert hasattr(DataConverter, "route_patterns") \
        and hasattr(DataConverter, "sphn_route_codes") \
        and isinstance(DataConverter.route_patterns, dict) \
        and isinstance(DataConverter.sphn_route_codes, dict) \
        and all(isinstance(route_name, str) and isinstance(pattern, str) for route_name, pattern in DataConverter.route_patterns.items()) \
        and all(isinstance(route_name, str) and isinstance(snomed_code, tuple) for route_name, snomed_code in DataConverter.sphn_route_codes.items()) \
        and all(len(snomed_code) == 3 for snomed_code in DataConverter.sphn_route_codes.values()) \
        and all(route_name in DataConverter.sphn_route_codes for route_name in DataConverter.route_patterns)

    matches_found = []
    # Check each route pattern (case-insensitive) against the route string
    for route_name, pattern in DataConverter.route_patterns.items():
        if re.search(pattern, route_string, re.IGNORECASE):

            # Retrieve the corresponding Code for the matched route name
            code = DataConverter.sphn_route_codes.get(route_name, None)

            # Append the matched route and its Code to the list of matches found
            matches_found.append({
                "Route": route_name,
                "Code": code
            })
            logger.debug(" "*(indent+0) + f"Matched route: '{route_name}' and mapped it to SPHN route code: '{code}'")

    return matches_found


def generate_id() -> str:
    """
    Generates a unique ID
    """
    # Generate a unique id using '.hex' to have only the 32 hex values (without the dashes inbetween)
    return uuid.uuid4().hex
