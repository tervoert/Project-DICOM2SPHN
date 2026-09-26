"""
dicom_imaging_device_reader.py: 
    Part of the example dicom2sphn package.
    It contains functions for reading DICOM Equipment metadata for the SPHn ImagingDevice entity.
"""
import pydicom
from pydicom import Dataset

from .context import Context
from .sphn_concepts.sphn_software import SPHNSoftware
from .tools import already_in_list


#
# Edwin 2026-07-24
#
def get_imaging_device_metadata_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> None:
    """
    Get the metadata related to SPHN ImagingDevice from the dataset
        dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
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

    manufacturer_name = get_manufacturer_from_dicom(dataset, context, indent=indent) 
    
    if manufacturer_name is not None:
        data_store.manufacturer_name = manufacturer_name
        logger.debug(" "*(indent+0) + f"Manufacturer name: '{manufacturer_name}'")
    else:
        logger.debug(" "*(indent+0) + "Manufacturer name not defined")

    # 
    # ManufacturerModelName
    #

    manufacturer_model_name = get_manufacturer_model_name_from_dicom(dataset, context, indent=indent) 

    if manufacturer_model_name is not None:
        data_store.manufacturer_model_name = manufacturer_model_name
        logger.debug(" "*(indent+0) + f"ManufacturerModelName: '{manufacturer_model_name}'")
    else:
        logger.debug(" "*(indent+0) + "ManufacturerModelName not defined")

    # 
    # DeviceSerialNumber
    #

    device_serial_number = get_device_serial_number_from_dicom(dataset, context, indent=indent) 

    if device_serial_number is not None:
        data_store.device_serial_number = device_serial_number
        logger.debug(" "*(indent+0) + f"DeviceSerialNumber: '{device_serial_number}'")
    else:
        logger.debug(" "*(indent+0) + "DeviceSerialNumber not defined")

    # 
    # SoftwareVersions
    #

    software_versions_list = get_software_versions_from_dicom(dataset, context, indent=indent) 

    if software_versions_list is not None:

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

            elif not already_in_list(sphn_software, data_store.software_list):
                data_store.software_list.append(sphn_software)
                logger.debug(" "*(indent+0) + f"SoftwareVersions item: '{software_version}'")
            else:
                logger.debug(" "*(indent+0) + f"SoftwareVersions item: '{software_version}' already exists in the list, not adding it again")
                continue

    else:
        logger.debug(" "*(indent+0) + "SoftwareVersions not defined")

# -----------------------------------------------------------------------------------------------------------------
# DICOM tag reading functions for SPHN ImagingFrame metadata
# -----------------------------------------------------------------------------------------------------------------

#
#  Edwin 2026-07-24
#
def get_manufacturer_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM Manufacturer tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              Manufacturer
    # Value Representation: Long String (LO)
    # Type:	                Required, Empty if Unknown (2)
    # Value Multiplicity:   1

    # Note:
    #   Available in CR, DX, CT, MR, PT, enhanced CT, enhanced MR, enhanced PT

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "Manufacturer" not in dataset:
        logger.warning(" "*(indent+0) + "DICOM Manufacturer tag was not found")
        return None
    
    # Get the DataElement
    data_element = dataset["Manufacturer"]

    # Get the value
    value = data_element.value
        
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
        
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM Manufacturer tag value was not provided")
        return None
    
    # It should be a single-valued tag, a string
    if value_multiplicity != 1 or not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM Manufacturer tag has an unknown format")
        return None
    
    # Remove whitespace
    manufacturer_str = value.strip()

    # Check if value is not empty
    if len(manufacturer_str) == 0:
        logger.debug(" "*(indent+0) + "DICOM Manufacturer tag contains only whitespace")
        return None

    return manufacturer_str

#
# Edwin 2026-07-24
#
def get_manufacturer_model_name_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM ManufacturerModelName tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              ManufacturerModelName
    # Value Representation: Long String (LO)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "ManufacturerModelName" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM ManufacturerModelName tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["ManufacturerModelName"]

    # Get the value
    value = data_element.value
    
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
        
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM ManufacturerModelName tag value was not provided")
        return None
        
    # It should be a single-valued tag, a string
    if value_multiplicity != 1 or not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM ManufacturerModelName tag has an unknown format")
        return None

    # Remove whitespace
    manufacturer_model_name = value.strip()

    # Check if value is not empty
    if len(manufacturer_model_name) == 0:
        logger.debug(" "*(indent+0) + "DICOM ManufacturerModelName tag contains only whitespace")
        return None

    return manufacturer_model_name

#
# Edwin 2026-07-24
#
# (Not used in the metadata in this example due to privacy concerns)
#
def get_device_serial_number_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM DeviceSerialNumber tag
        dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              DeviceSerialNumber
    # Value Representation: Long String (LO)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "DeviceSerialNumber" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM DeviceSerialNumber tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["DeviceSerialNumber"]

    # Get the value
    value = data_element.value
    
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
        
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM DeviceSerialNumber tag value was not provided")
        return None

    # It should be a single-valued tag, a string
    if value_multiplicity != 1 or not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM DeviceSerialNumber tag has an unknown format")
        return None

    # Remove whitespace
    device_serial_number = value.strip()

    # Check if value is not empty
    if len(device_serial_number) == 0:
        logger.debug(" "*(indent+0) + "DICOM DeviceSerialNumber tag contains only whitespace")
        return None

    return device_serial_number

#
# Edwin 2026-07-24
#
def get_software_versions_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> list[str]|None:
    """
    Returns a list of values corresponding to the values of the DICOM SoftwareVersions tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              SoftwareVersions
    # Value Representation: Long String (LO)
    # Type:	                Optional (3)
    # Value Multiplicity:   1-n

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Set initial value
    software_versions_list = []

    if "SoftwareVersions" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM SoftwareVersions tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["SoftwareVersions"]

    # Get the value
    value = data_element.value
    
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
    
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM SoftwareVersions tag value was not provided")
        return None

    # It could be a multi-valued tag
    if value_multiplicity >= 1 and isinstance(value, pydicom.multival.MultiValue):

        # For each value in the multi-value list
        for value_item in value:

            if not isinstance(value_item, str):
                logger.warning(" "*(indent+0) + "DICOM SoftwareVersions tag value-item has an unknown format")
                continue
                
            # Remove whitespace
            software_version_str = value_item.strip()

            # Check if value is not empty
            if len(software_version_str) == 0:
                logger.debug(" "*(indent+0) + "DICOM SoftwareVersions tag value-item contains only whitespace")
                continue

            # Adding to the list
            software_versions_list.append(software_version_str)

    # It could be a single-valued tag, a string
    elif value_multiplicity == 1 and isinstance(value, str):

        # Remove whitespace
        software_version_str = value.strip()

        # Check if value is not empty
        if len(software_version_str) == 0:
            logger.debug(" "*(indent+0) + "DICOM SoftwareVersions tag contains only whitespace")
            return None
        
        # Convert to a list with a string
        software_versions_list = [software_version_str]

    else:
        logger.warning(" "*(indent+0) + "DICOM SoftwareVersions tag has an unknown format")
        return None

    return software_versions_list if len(software_versions_list)>0 else None
