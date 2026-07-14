"""
main.py: 
    Part of the example dicom2sphn package.
    It contains the main application logic.
"""
import logging
import pydicom
from pydantic import BaseModel, Field, ValidationError, BeforeValidator, SecretStr, ConfigDict
from typing import Any, Protocol, runtime_checkable
from pathlib import Path
from pydicom import Dataset, dcmread, Sequence
from pydicom.uid import UID
from pydicom.misc import is_dicom
from pynetdicom import sop_class
from pynetdicom.service_class import StorageServiceClass

# Use DICOMweb Client to connect to the Orthanc DICOMweb API
from dicomweb_client.api import DICOMwebClient
from dicomweb_client.session_utils import create_session_from_user_pass

from .tools import is_valid_string
from .protocols import LoggerProtocol
from .context import Context
from .import_config_settings import import_config_settings, ImportConfigSettingsError
from .patient_processor import PatientProcessor

# For type hints, see: https://docs.python.org/3/library/typing.html
# https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html
# Python 3.9+ supports built-in generic types, so we can use list, dict, set, etc. instead of List, Dict, Set from the typing module.
# Python 3.10+ supports union types with the | operator, so we can use str | None instead of Optional[str], etc.

##### Note: Old functions for the main program

def is_valid_dicom_file(file_path: Path) -> bool:
    """Check if the file is a valid DICOM file."""
    return file_path.is_file() and is_dicom(file_path)

def has_valid_sop_class_uid(dataset: Dataset, valid_sop_classes: dict[str, str]) -> bool:
    """Check if the DICOM dataset has a valid SOP Class UID."""
    sop_class_uid = dataset.get("SOPClassUID", None)
    return sop_class_uid in valid_sop_classes

def read_dicom_header(file_path: Path, logger: LoggerProtocol, indent: int=0) -> Dataset|None:
    """Read the DICOM header and return the dataset."""
    try:
        dataset = dcmread(file_path, stop_before_pixels=True)
        return dataset
    except Exception as e:
        logger.error(" "*(indent+0) + f"Error reading DICOM file '{file_path}': '{e}'")
        return None

def process_dicom_tags(datasets: list[Dataset|None], output_file: Path, logger: LoggerProtocol, level: int = 0,  indent: int = 0) -> None:
    """Process the DICOM tags and print the results."""

    dicom_tags = sorted(set([tag for ds in datasets if ds is not None for tag in ds.keys() ]))

    logger.debug(" "*(indent+0) + f"Found '{len(dicom_tags)}' unique DICOM tag(s).")

    for tag in dicom_tags: 
        out_string = f"{tag}\t" + ">"*level + f"{pydicom.datadict.keyword_for_tag(tag)}"

        logger.debug(" "*(indent+1) + f"Current tag: '{tag}' - '{pydicom.datadict.keyword_for_tag(tag)}'")

        sequence_found = False
        for i, ds in enumerate(datasets):
            if ds is not None and tag in ds:
                data_element = ds[tag]
                if data_element.VR == "SQ":
                    sequence_found = True
                    logger.debug(" "*(indent+2) + f"Found the Sequence tag in Dataset: '{i}'.")                    
                    break
                else:
                    out_string += f"\t {ds[tag].value}"
                    logger.debug(" "*(indent+2) + f"Found the tag with value: '{ds[tag].value}' in Dataset: '{i}'.")
            else:
                out_string += "\t N/A"
                logger.debug(" "*(indent+2) + f"Did not find the tag in Dataset: '{i}'.")

        logger.debug(" "*(indent+2) + f"Added line to output file: '{out_string}'.")
        with open(output_file,"a", encoding="utf-8") as f:
            f.write(out_string + "\n")

        # Process the sequence tags separately
        if sequence_found is True:
            sequences = []
            for ds in datasets:
                if ds is not None and tag in ds:
                    data_element = ds[tag]
                    if data_element.VR == "SQ":
                        sequences.append(data_element)  # Add data_element of type sequence to the the list of sequences
                    else:
                        sequences.append(None)  # If the tag is not a sequence, append None
                else:
                    sequences.append(None)  # If the tag is not present, append None

            process_dicom_sequence_tags(sequences, output_file, logger, level=level, indent=indent+2)


def process_dicom_sequence_tags(sequences: list[Sequence|None], output_file: Path, logger: LoggerProtocol, level: int = 0, indent: int = 0) -> None:
    """Process the DICOM sequence tags and print the results."""

    # Get the max number of items across all sequences
    # max_number_of_items = max([len(element.value) if element.VR == "SQ" else 0 for element in sequences if element is not None])
    max_number_of_items = max([len(data_element.value) if data_element is not None and data_element.VR == "SQ" else 0 for data_element in sequences])

    logger.debug(" "*(indent+0) + f"Max number of items in Sequence: '{max_number_of_items}'.")

    # Get the max number of items in the sequence for the current tag across all datasets
    # max_number_of_items = max([len(element.value) if element.VR == "SQ" else 0 for ds in sequences if tag in ds for element in [ds[tag]]])

    for i in range(max_number_of_items):

        logger.debug(" "*(indent+1) + f"Processing item '{i+1}' in Sequence.")

        out_string = "\t" + ">"*level + f"[ITEM_{i+1}]"

        logger.debug(" "*(indent+1) + f"Adding line to output file: '{out_string}'.")

        with open(output_file,"a", encoding="utf-8") as f:
            f.write(out_string + "\n")

        datasets = [data_element.value[i] if data_element is not None and data_element.VR == "SQ" and len(data_element.value) > i else None for data_element in sequences]

        # Process the items in the sequence for the current tag across all datasets
        process_dicom_tags(datasets, output_file, logger, level=level+1, indent=indent+1)

##### Note: New functions for the main program

#
# Edwin 2026-07-14
#
def create_logger() -> LoggerProtocol:
    """Create a logger for the application."""
    logger = logging.getLogger("QueryDICOMwebServer")
    logger.setLevel(logging.DEBUG)  # Set the logging level to DEBUG to capture all log messages
    #logger.setLevel(logging.INFO) # Set the logging level to INFO only

    # Create console handler and set level to DEBUG
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    #ch.setLevel(logging.INFO)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(ch)

    return logger

#
# Edwin 2026-07-14
#
def main(output_file: Path, config_file: Path, patient_id: str) -> None:
    """Run the main program."""

    # ##################################################################################
    # Initializing 
    # ##################################################################################

    # Create a logger for the application
    logger = create_logger()
    indent = 0

    # Create a context for the application and add the logger to it
    context = Context(
        logger=logger
        )

    context.logger.info(" "*(indent+0) + "Start checking input parameters, reading configuration, and importing environment variables...")

    # Check if patient ID is a valid string
    if not is_valid_string(patient_id):
        context.logger.error(" "*(indent+1) + f"Patient ID '{patient_id}' is not a valid string.")
        return  

    # Check if the output file already exists
    if output_file.is_file():
        context.logger.error(" "*(indent+1) + f"Output file '{output_file}' already exists.")
        return        

    # Check if the configuration file exists
    if not config_file.is_file():
        context.logger.error(" "*(indent+1) + f"Configuration file '{config_file}' does not exist or is not a file.")
        return

    # 
    # Import settings from the configuration file
    #
    try:
        context = import_config_settings(config_file, context, indent=indent+1)
    except ImportConfigSettingsError as e:
        context.logger.error(" "*(indent+1) + f"Error importing configuration settings: '{e}'.")
        return

    # Check if a DICOMweb API user is defined
    if context.dicomweb_api_user is None:
        context.logger.error(" "*(indent+1) + "No DICOMweb API user settings found.")
        return

    # Create the DICOMweb API client
    try:
        context.logger.info(" "*(indent+1) + "Trying to create the DICOMweb API client.")

        # Connect to DICOMweb server with authentication:

        # Create a session using a username and password
        session = create_session_from_user_pass(
            username=context.dicomweb_api_user.username,
            password=context.dicomweb_api_user.password.get_secret_value()
        )

        # Create the DICOMweb client
        dw_client = DICOMwebClient(
            url=context.dicomweb_api_user.base_url,
            session=session
        )
        
        # Adding DICOMweb client to the context
        context.dw_client = dw_client

        context.logger.info(" "*(indent+1) + "Succesfully created the DICOMweb API client.")

    except Exception as e:
        context.logger.error(" "*(indent+1) + f"Could not create the DICOMweb API client: '{e}'.")
        return

    # ##################################################################################
    # Start processing patient data from DICOMweb
    # ##################################################################################

    context.logger.info(" "*(indent+1) + "Starting to process patient data from DICOMweb.")
    
    patient_processor = PatientProcessor(context, patient_id)
    patient_processor.process()
    patient_processor.save_to_json_file()

    context.logger.info(" "*(indent+1) + "Successfully processed patient data from DICOMweb.")

    return



"""     # Import settings from environment variables (if they exist) and overwrite settings from the configuration file
    # Export VALID_SOP_CLASS_UIDs as environment variable in the format: "VALID_SOP_CLASS_UIDs=uid1,uid2,uid3"
    valid_sop_class_uids_env = os.getenv('VALID_SOP_CLASS_UIDs')

    if valid_sop_class_uids_env is not None:
        VALID_SOP_CLASS_UIDs = [uid.strip() for uid in valid_sop_class_uids_env.split(',')] # Split the environment variable string by comma and strip whitespace from each UID
        print("Info: Using the 'VALID_SOP_CLASS_UIDs' environment variable.")
        logger.info(" "*(indent+1) + "Using the 'VALID_SOP_CLASS_UIDs' environment variable.")

    # Check if the VALID_SOP_CLASS_UIDs are valid UIDs and correspond to Storage Service Class UIDs
    if not all([sop_class.uid_to_service_class(uid) == StorageServiceClass for uid in VALID_SOP_CLASS_UIDs]):
        logger.error(" "*(indent+1) + "One or more of the specified VALID_SOP_CLASS_UIDs are not valid Storage Service Class UIDs.")
        return 

    logger.info(" "*(indent+0) + "Done checking input parameters, reading configuration, and importing environment variables...")
    logger.info(" "*(indent+0) + "Start processing DICOM file(s)...")

    dicom_files = [f for f in input_folder.iterdir() if is_valid_dicom_file(f)]
    dicom_headers = [ds for ds in (read_dicom_header(f) for f in dicom_files) if ds is not None and has_valid_sop_class_uid(ds)]
    num_of_dicom_files = len(dicom_headers)

    logger.info(" "*(indent+1) + f"Found '{len(dicom_files)}' valid DICOM file(s) of which '{num_of_dicom_files}' have valid DICOM SOP Class UID.")

    logger.info(" "*(indent+1) + f"Writing header to output file '{output_file}'...")
    
    first_line = f"DICOM, Dataset folder: {input_folder}" + "\t" + "".join([f"\tFilename:{Path(dataset.filename).name}" for dataset in dicom_headers]) + "\n"    
    second_line = "Attribute Tag\tAttribute Name" + "\tAttribute Value"*num_of_dicom_files + "\n"
    with open(output_file,"w", encoding="utf-8") as f:
        f.write(first_line)
        f.write(second_line)

    process_dicom_tags(dicom_headers, output_file, level=0, indent=indent+1)

    logger.info(" "*(indent+0) + "Done processing DICOM file(s)...")
 """