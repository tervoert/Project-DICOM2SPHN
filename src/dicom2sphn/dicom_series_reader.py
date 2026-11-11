"""
dicom_series_reader.py: 
    Part of the example dicom2sphn package.
    It contains functions for reading DICOM Series metadata for the SPHN ImagingSeries concept.
"""

from pydicom import Dataset

from .context import Context
from .sphn_concepts.sphn_imaging_series import SPHNImagingSeries
from .tools import combine_dicom_date_and_time, get_dicom_timezone, is_valid_string


#
# Edwin 2026-08-09
# 
def get_series_metadata_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> None:
    """
    Get the metadata related to SPHN ImagingSeries from the dataset
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Checks
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent>=0

    assert context.logger is not None
    assert context.data_store is not None

    logger = context.logger
    data_store = context.data_store

    # The SPHN ImagingSeries must be available in the data store
    assert isinstance(data_store.sphn_imaging_series, SPHNImagingSeries)            

    # -------------------------------------------------------------------------------------------------------------

    # 
    # SeriesDate and SeriesTime
    #

    if data_store.series_start_datetime is None:

        # Date
        series_date = get_series_date_from_dicom(dataset, context, indent=indent+2)

        if series_date is not None:
            assert isinstance(series_date, str)
            logger.debug(" "*(indent+0) + f"SeriesDate string from DICOM: '{series_date}'")
        else:
            logger.debug(" "*(indent+0) + "SeriesDate not found")

        # Time
        series_time = get_series_time_from_dicom(dataset, context, indent=indent+2)

        if series_time is not None:
            assert isinstance(series_time, str)
            logger.debug(" "*(indent+0) + f"SeriesTime string from DICOM: '{series_time}'")
        else:
            logger.debug(" "*(indent+0) + "SeriesTime not found")

        # DICOM dates and times are local times: get the timezone (TimezoneOffsetFromUTC or the configured local timezone)
        assert context.local_timezone is not None
        dicom_timezone = get_dicom_timezone(dataset, context.local_timezone, logger, indent=indent+2)

        # Combine SeriesDate and SeriesTime
        series_start_datetime_obj = None
        if series_date and series_time:

            # Combine the SeriesDate and SeriesTime strings into a single complete DICOM datetime (DT) object
            # - series datetime is completed by filling in missing components for Month, Day, Hour, Minute, Second
            series_start_datetime_obj = combine_dicom_date_and_time(series_date, series_time, dicom_timezone, logger, indent=indent+2)

        elif series_date and not series_time:

            # Combine the SeriesDate and SeriesTime strings into a single complete DICOM datetime (DT) object
            # - series datetime is completed by filling in missing components for Month, Day, Hour, Minute, Second
            series_start_datetime_obj = combine_dicom_date_and_time(series_date, "", dicom_timezone, logger, indent=indent+2)
        else:
            logger.debug(" "*(indent+0) + "Could not combine SeriesDate and SeriesTime: Series Date not defined")
        
        if series_start_datetime_obj is not None:
            # Set the series start datetime in the data store
            data_store.series_start_datetime = series_start_datetime_obj
            logger.debug(" "*(indent+0) + f"Combined Series Date and Time: '{series_start_datetime_obj!s}'")

            # Update the SPHN ImagingSeries start datetime
            assert isinstance(data_store.sphn_imaging_series, SPHNImagingSeries)            
            data_store.sphn_imaging_series.has_start_datetime = series_start_datetime_obj
            logger.debug(" "*(indent+0) + f"Updated SPHN ImagingSeries has_start_datetime: '{series_start_datetime_obj.isoformat(timespec='milliseconds')}'")
        else:
            logger.debug(" "*(indent+0) + "Could not combine SeriesDate and SeriesTime")

    # -------------------------------------------------------------------------------------------------------------

    # 
    # SeriesDescription
    #

    if data_store.sphn_imaging_series.has_description is None:

        series_description = get_series_description_from_dicom(dataset, context, indent=indent+2)

        if series_description is not None:

            assert is_valid_string(series_description)

            # Set the ImagingSeries property
            data_store.sphn_imaging_series.has_description = series_description
            logger.debug(" "*(indent+0) + f"Added SPHN ImagingSeries has_description: '{series_description}'")
        else:
            logger.debug(" "*(indent+0) + "SPHN ImagingSeries has_description not defined")

    # -------------------------------------------------------------------------------------------------------------

    # 
    # ProtocolName
    #

    if data_store.sphn_imaging_series.has_protocol_name is None:

        protocol_name = get_protocol_name_from_dicom(dataset, context, indent=indent+2)

        if protocol_name is not None:

            assert is_valid_string(protocol_name)

            # Set the ImagingSeries property
            data_store.sphn_imaging_series.has_protocol_name = protocol_name
            logger.debug(" "*(indent+0) + f"Added SPHN ImagingSeries has_protocol_name: '{protocol_name}'")
        else:
            logger.debug(" "*(indent+0) + "SPHN ImagingSeries has_protocol_name not defined")

    # -------------------------------------------------------------------------------------------------------------

    # 
    # Modality
    #

    assert data_store.sphn_imaging_series.has_imaging_modality_code is not None

    # -------------------------------------------------------------------------------------------------------------

    # 
    # NumberOfFrames
    #

    # assert data_store.sphn_imaging_series.has_number_of_frames is not None

    # -------------------------------------------------------------------------------------------------------------

    #
    # DataFile list
    #

    # ToDo by Edwin: 
    #  - Not implemented yet


# -----------------------------------------------------------------------------------------------------------------
# DICOM tag reading functions for SPHN ImagingProcedure metadata
# -----------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-11
#
def get_series_date_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM SeriesDate tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:	                (0008,0021)
    # Type:	                Optional (3)
    # Keyword:              SeriesDate
    # Value Multiplicity:   1
    # Value Representation: Date (DA)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM SeriesDate tag
    value = dataset.get("SeriesDate", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM SeriesDate tag was not found")  
        return None

    # Convert value to str and trim whitespace
    try:
        value_str = str(value).strip()
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM SeriesDate tag value could not be converted to str")
        return None

    if not value_str:
        logger.debug(" "*(indent+0) + "DICOM SeriesDate tag contains only whitespace")
        return None

    return value_str


#
# Edwin 2026-11-11
#
def get_series_time_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM SeriesTime tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:	                (0008,0031)
    # Type:	                Optional (3)
    # Keyword:              SeriesTime
    # Value Multiplicity:   1
    # Value Representation: Time (TM)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM SeriesTime tag
    value = dataset.get("SeriesTime", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM SeriesTime tag was not found")  
        return None

    # Convert value to str and trim whitespace
    try:
        value_str = str(value).strip()
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM SeriesTime tag value could not be converted to str")
        return None

    if not value_str:
        logger.debug(" "*(indent+0) + "DICOM SeriesTime tag contains only whitespace")
        return None

    return value_str


#
# Edwin 2026-11-11
#
def get_series_description_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM SeriesDescription tag
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:	                (0008,103E)
    # Type:	                Optional (3)
    # Keyword:              SeriesDescription
    # Value Multiplicity:   1
    # Value Representation: Long String (LO)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM SeriesDescription tag
    value = dataset.get("SeriesDescription", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM SeriesDescription tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    value_str = value.strip()

    if not value_str:
        logger.debug(" "*(indent+0) + "DICOM SeriesDescription tag contains only whitespace")
        return None

    return value_str


#
# Edwin 2026-11-11
#
def get_protocol_name_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM ProtocolName tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:	                (0018,1030)
    # Type:	                Optional (3)
    # Keyword:              ProtocolName
    # Value Multiplicity:   1
    # Value Representation: Long String (LO)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ProtocolName tag
    value = dataset.get("ProtocolName", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ProtocolName tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    value_str = value.strip()

    if not value_str:
        logger.debug(" "*(indent+0) + "DICOM ProtocolName tag contains only whitespace")
        return None

    return value_str

