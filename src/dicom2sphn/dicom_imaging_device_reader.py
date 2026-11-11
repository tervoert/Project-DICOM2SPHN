"""
dicom_imaging_device_reader.py: 
    Part of the example dicom2sphn package.
    It contains functions for reading DICOM Equipment metadata for the SPHn ImagingDevice entity.
"""
import pydicom
from pydicom import Dataset

from .context import Context
from .sphn_concepts.sphn_software import SPHNSoftware
from .tools import is_valid_string


#
# Edwin 2026-11-11
#
def get_imaging_device_metadata_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> None:
    """
    Get the metadata related to SPHN ImagingDevice from the dataset
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger
    data_store = context.data_store

    # 
    # Manufacturer
    #

    if data_store.manufacturer_name is None:

        manufacturer_name = get_manufacturer_from_dicom(dataset, context, indent=indent) 
        
        if manufacturer_name is not None:
            data_store.manufacturer_name = manufacturer_name
            logger.debug(" "*(indent+0) + f"Manufacturer name: '{manufacturer_name}'")
        else:
            logger.debug(" "*(indent+0) + "Manufacturer name not defined")

    # 
    # ManufacturerModelName
    #

    if data_store.manufacturer_model_name is None:

        manufacturer_model_name = get_manufacturer_model_name_from_dicom(dataset, context, indent=indent) 

        if manufacturer_model_name is not None:
            data_store.manufacturer_model_name = manufacturer_model_name
            logger.debug(" "*(indent+0) + f"ManufacturerModelName: '{manufacturer_model_name}'")
        else:
            logger.debug(" "*(indent+0) + "ManufacturerModelName not defined")

    # 
    # DeviceSerialNumber
    #

    if data_store.device_serial_number is None:

        device_serial_number = get_device_serial_number_from_dicom(dataset, context, indent=indent) 

        if device_serial_number is not None:
            data_store.device_serial_number = device_serial_number
            logger.debug(" "*(indent+0) + f"DeviceSerialNumber: '{device_serial_number}'")
        else:
            logger.debug(" "*(indent+0) + "DeviceSerialNumber not defined")

    # 
    # SoftwareVersions
    #

    if data_store.software_list is None:

        software_versions_list = get_software_versions_from_dicom(dataset, context, indent=indent) 

        if software_versions_list is not None:

            counter=0
            for software_version in software_versions_list:
                
                # ToDo: Edwin - 2026-07-24
                #   - Try to split name and version

                sphn_software = SPHNSoftware(
                    sphn_schema=data_store.sphn_schema,
                    has_name=software_version,
                    has_version=software_version
                )

                # Add the SPHN Software to the data_store if it is not already in the list
                if data_store.software_list is None:
                    data_store.software_list = [sphn_software]
                    counter += 1

                elif sphn_software not in data_store.software_list:
                    data_store.software_list.append(sphn_software)
                    counter += 1
                else:
                    logger.debug(" "*(indent+0) + "SoftwareVersion is already in the list")
                    continue

            logger.debug(" "*(indent+0) + f"Total new SoftwareVersions added: {counter}")

        else:
            logger.debug(" "*(indent+0) + "SoftwareVersions not defined")

# -----------------------------------------------------------------------------------------------------------------
# DICOM tag reading functions for SPHN ImagingFrame metadata
# -----------------------------------------------------------------------------------------------------------------

#
#  Edwin 2026-11-11
#
def get_manufacturer_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM Manufacturer tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:	                (0008,0070)
    # Type:	                Required, Empty if Unknown (2)
    # Keyword:              Manufacturer
    # Value Multiplicity:   1
    # Value Representation: Long String (LO)

    # Note:
    #   Available in CR, DX, CT, MR, PT, enhanced CT, enhanced MR, enhanced PT

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM Manufacturer tag
    value = dataset.get("Manufacturer", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM Manufacturer tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    value_str = value.strip()

    if not value_str:
        logger.debug(" "*(indent+0) + "DICOM Manufacturer tag contains only whitespace")
        return None

    assert is_valid_string(value_str)
    
    return value_str


#
# Edwin 2026-11-11
#
def get_manufacturer_model_name_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM ManufacturerModelName tag
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:	                (0008,1090)
    # Type:	                Optional (3)
    # Keyword:              ManufacturerModelName
    # Value Multiplicity:   1
    # Value Representation: Long String (LO)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ManufacturerModelName tag
    value = dataset.get("ManufacturerModelName", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ManufacturerModelName tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    value_str = value.strip()

    if not value_str:
        logger.debug(" "*(indent+0) + "DICOM ManufacturerModelName tag contains only whitespace")
        return None

    assert is_valid_string(value_str)

    return value_str


#
# Edwin 2026-11-11
#
# (Not used in the SPHN metadata due to privacy concerns)
#
def get_device_serial_number_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM DeviceSerialNumber tag
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:	                (0018,1000)
    # Type:	                Optional (3)
    # Keyword:              DeviceSerialNumber
    # Value Multiplicity:   1
    # Value Representation: Long String (LO)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM DeviceSerialNumber tag
    value = dataset.get("DeviceSerialNumber", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM DeviceSerialNumber tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    value_str = value.strip()

    if not value_str:
        logger.debug(" "*(indent+0) + "DICOM DeviceSerialNumber tag contains only whitespace")
        return None
    
    assert is_valid_string(value_str)

    return value_str


#
# Edwin 2026-11-11
#
def get_software_versions_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> list[str]|None:
    """
    Returns a list of values corresponding to the values of the DICOM SoftwareVersions tag
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:	                (0018,1020)
    # Type:	                Optional (3)
    # Keyword:              SoftwareVersions
    # Value Multiplicity:   1-n
    # Value Representation: Long String (LO)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Set initial value
    software_versions_list = []

    # Get the value of the DICOM SoftwareVersions tag
    value = dataset.get("SoftwareVersions", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM SoftwareVersions tag was not found")  
        return None

    # It could be a multi-valued tag
    if isinstance(value, pydicom.multival.MultiValue):

        # For each value in the multi-value list
        for value_item in value:

            if not isinstance(value_item, str):
                logger.warning(" "*(indent+0) + "DICOM SoftwareVersions tag value-item has an unknown format")
                continue
                
            # Remove whitespace
            value_item_str = value_item.strip()

            # Check if value is not empty
            if not value_item_str:
                logger.debug(" "*(indent+0) + "DICOM SoftwareVersions tag value-item contains only whitespace")
                continue

            assert is_valid_string(value_item_str)

            # Adding to the list
            software_versions_list.append(value_item_str)

    # It could be a single-valued tag, a string
    elif isinstance(value, str):

        # Remove whitespace
        value_str = value.strip()

        # Check if value is not empty
        if not value_str:
            logger.debug(" "*(indent+0) + "DICOM SoftwareVersions tag contains only whitespace")
            return None

        assert is_valid_string(value_str)

        # Convert to a list with a string
        software_versions_list = [value_str]

    else:
        logger.warning(" "*(indent+0) + "DICOM SoftwareVersions tag has an unknown format")
        return None

    return software_versions_list if len(software_versions_list)>0 else None
