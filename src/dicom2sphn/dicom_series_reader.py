"""
dicom_series_reader.py: 
    Part of the example dicom2sphn package.
    It contains functions for reading DICOM Series metadata for the SPHN ImagingSeries concept.
"""

from datetime import datetime

from pydicom import Dataset

from .context import Context
from .sphn_concepts.sphn_imaging_series import SPHNImagingSeries
from .tools import combine_dicom_date_and_time, is_valid_string


#
# Edwin 2026-08-09
# 
def get_series_metadata_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> None:
    """
    Get the metadata related to SPHN ImagingSeries from the dataset
        - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Checks
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent>=0

    assert context.logger is not None
    assert context.data_store is not None

    logger = context.logger
    data_store = context.data_store
    sphn_schema = data_store.sphn_schema

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

        # Combine StudyDate and StudyTime
        series_start_datetime_obj = None
        if series_date and series_time:

            # Combine the SeriesDate and SeriesTime strings into a single complete DICOM datetime (DT) object
            # - series datetime is completed by filling in missing components for Month, Day, Hour, Minute, Second
            series_start_datetime_obj = combine_dicom_date_and_time(series_date, series_time, logger, indent=indent+2)
        
        elif series_date and not series_time:

            # Combine the SeriesDate and SeriesTime strings into a single complete DICOM datetime (DT) object
            # - series datetime is completed by filling in missing components for Month, Day, Hour, Minute, Second
            series_start_datetime_obj = combine_dicom_date_and_time(series_date, "", logger, indent=indent+2)
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
# Edwin 2026-08-09
#
def get_series_date_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM SeriesDate tag
        dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              SeriesDate
    # Value Representation: Date (DA)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "SeriesDate" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM SeriesDate tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["SeriesDate"]

    # Get the value
    value = data_element.value
    
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
    
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM SeriesDate tag value was not provided")
        return None
    
    # It should be a single-valued tag, a string
    if value_multiplicity != 1 or not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM SeriesDate tag has an unknown format")
        return None
    
    # Remove whitespace
    series_date_str = value.strip()

    # Check if value is not empty
    if len(series_date_str) == 0:
        logger.debug(" "*(indent+0) + "DICOM SeriesDate tag contains only whitespace")
        return None

    return series_date_str

#
# Edwin 2026-08-09
#
def get_series_time_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM SeriesTime tag
        dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              SeriesTime
    # Value Representation: Time (TM)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "SeriesTime" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM SeriesTime tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["SeriesTime"]

    # Get the value
    value = data_element.value
    
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
    
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM SeriesTime tag value was not provided")
        return None
            
    # It should be a single-valued tag, a string
    if value_multiplicity != 1 or not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM SeriesTime tag has an unknown format")
        return None
    
    # Remove whitespace
    series_time_str = value.strip()

    # Check if value is not empty
    if len(series_time_str) == 0:
        logger.debug(" "*(indent+0) + "DICOM SeriesTime tag contains only whitespace")
        return None

    return series_time_str

#
# Edwin 2025-05-28
#
def get_series_description_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM SeriesDescription tag
        dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              SeriesDescription
    # Value Representation: Long String (LO)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "SeriesDescription" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM SeriesDescription tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["SeriesDescription"]

    # Get the value
    value = data_element.value
    
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
    
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM SeriesDescription tag value was not provided")
        return None
    
    # It should be a single-valued tag, a string
    if value_multiplicity != 1 or not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM SeriesDescription tag has an unknown format")
        return None

    # Remove whitespace
    series_description_str = value.strip()

    # Check if value is not empty
    if len(series_description_str) == 0:
        logger.debug(" "*(indent+0) + "DICOM SeriesDescription tag contains only whitespace")
        return None
    
    return series_description_str

#
# Edwin 2026-08-09
#
def get_protocol_name_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM ProtocolName tag
        dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              ProtocolName
    # Value Representation: Long String (LO)
    # Type:	                Optional (3)
    # Value Multiplicity:   1
    # Check

    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "ProtocolName" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM ProtocolName tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["ProtocolName"]

    # Get the value
    value = data_element.value
    
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
    
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM ProtocolName tag value was not provided")
        return None
    
    # It should be a single-valued tag, a string
    if value_multiplicity != 1 or not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM ProtocolName tag has an unknown format")
        return None
    
    # Remove whitespace
    protocol_name = value.strip()

    # Check if value is not empty
    if len(protocol_name) == 0:
        logger.debug(" "*(indent+0) + "DICOM ProtocolName tag contains only whitespace")
        return None
    
    return protocol_name
