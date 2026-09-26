"""
main.py: 
    Part of the example dicom2sphn package.
    It contains the main application logic.
"""
import logging
from datetime import timedelta
from pathlib import Path
from time import time

import pydicom
from dicomweb_client.api import DICOMwebClient
from dicomweb_client.session_utils import create_session_from_user_pass
from pydicom import Dataset, Sequence, dcmread
from pydicom.misc import is_dicom

from .context import Context
from .dw_patient_processor import DWPatientProcessor
from .import_config_settings import ImportConfigSettingsError, import_config_settings
from .protocols import LoggerProtocol
from .tools import is_valid_string

# For type hints, see: https://docs.python.org/3/library/typing.html
# https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html
# Python 3.9+ supports built-in generic types, so we can use list, dict, set, etc. instead of List, Dict, Set from the typing module.
# Python 3.10+ supports union types with the | operator, so we can use str | None instead of Optional[str], etc.

#
# Edwin 2026-07-14
#
def main(patient_id: str, output_file_path_specification: str, config_file: str) -> None:
    """Run the main program."""

    # -----------------------------------------------------------------------------------------------------------------
    # Initializing 
    # -----------------------------------------------------------------------------------------------------------------

    start_time_t1 = time()

    # Create a logger for the application
    logger = create_logger()
    indent = 0

    # Create a context for the application and add the logger to it
    context = Context(
        logger=logger
        )

    logger.info(" "*(indent+0) + "Starting...")

    logger.info(" "*(indent+2) + "Checking input parameters.")

    # Check if patient ID is a valid string
    if not is_valid_string(patient_id):
        logger.error(" "*(indent+4) + f"Patient ID '{patient_id}' is not a valid string.")
        return  

    # Check if "{patient_id}" is in the output_file_path_specification
    if "{patient_id}" not in Path(output_file_path_specification).name:
        logger.error(" "*(indent+4) +"The JSON output filename must contain the '{patient_id}' indicator for the DICOM Patient ID.")
        return

    # Check if "{file_id}" is in the output_file_path_specification
    if "{file_id}" not in Path(output_file_path_specification).name:
        logger.error(" "*(indent+4) +"The JSON output filename must contain the '{file_id}' indicator for the file ID.")
        return

    # Check if the configuration file exists
    config_file_path = Path(config_file)
    if not config_file_path.is_file():
        logger.error(" "*(indent+4) + f"Configuration file '{config_file_path}' does not exist or is not a file.")
        return

    # -----------------------------------------------------------------------------------------------------------------
    # Import settings from the configuration file
    # -----------------------------------------------------------------------------------------------------------------

    # Importing configuration settings from the configuration file
    # Using the imported SPHN configuration settings to create the SPHNDataRelease, SPHNDataProvider and SPHNSourceSystem concepts
    # Using the imported DICOM configuration settings to create the allowed SOP Class UIDs dictionary
    # Creating a DataStore with the SPHN concepts and the allowed SOP Class UIDs dictionary and add it to the context
    # Using the imported DICOMweb API user settings to create a DICOMwebClient and add it to the context
    
    logger.info(" "*(indent+2) + "Importing configuration settings.")

    try:
        context = import_config_settings(config_file_path, context, indent=indent+4)
        data_store = context.data_store
    except ImportConfigSettingsError as e:
        logger.error(" "*(indent+4) + f"Error importing configuration settings: '{e}'.")
        return

    # Check if a DICOMweb API user is defined
    if context.dicomweb_api_user is None:
        logger.error(" "*(indent+4) + "No DICOMweb API user settings found.")
        return

    # -----------------------------------------------------------------------------------------------------------------
    # Create the DICOMweb API client
    # -----------------------------------------------------------------------------------------------------------------

    logger.info(" "*(indent+2) + "Trying to create the DICOMweb API client.")

    # Connect to DICOMweb server with authentication:
    # Create a session using a username and password
    session = create_session_from_user_pass(
        username=context.dicomweb_api_user.username,
        password=context.dicomweb_api_user.password.get_secret_value()
    )

    # Create the DICOMweb client
    dw_client = DICOMwebClient(
        url=context.dicomweb_api_user.base_url,
        session=session,
        timeout=context.dicomweb_api_user.timeout_seconds
    )
    context.dw_client = dw_client
    
    logger.info(" "*(indent+2) + "Succesfully created the DICOMweb API client.")

    # -----------------------------------------------------------------------------------------------------------------
    # Start processing patient data from DICOMweb
    # -----------------------------------------------------------------------------------------------------------------

    logger.info(" "*(indent+2) + "Starting to process patient data from DICOMweb.")
    start_time_t2 = time()
    dw_patient_processor = DWPatientProcessor()
    dw_patient_processor.process(patient_id, context,indent=indent+4)
    stop_time_t2 = time()
    logger.info(" "*(indent+2) + f"Successfully processed patient data from DICOMweb in '{stop_time_t2 - start_time_t2:.2f}' seconds (" + str(timedelta(seconds=(stop_time_t2 - start_time_t2))) + ").") 
    logger.info("")

    # Generate and write JSON only if there is a subject pseudo identifier and at least one imaging procedure
    if data_store.sphn_subject_pseudo_identifier is not None and len(data_store.sphn_imaging_procedure_list) > 0:

        logger.info(" "*(indent+2) + "Starting to generate JSON.")
        start_time_t2 = time()
        json_string = data_store.generate_json_string_for_sphn_connector(indent=indent+4)
        stop_time_t2 = time()
        logger.info(" "*(indent+2) + f"Successfully generated JSON in '{stop_time_t2 - start_time_t2:.2f}' seconds (" + str(timedelta(seconds=(stop_time_t2 - start_time_t2))) + ").")
        logger.info("")

        logger.info(" "*(indent+2) + "Starting to write JSON to file.")
        start_time_t2 = time()
        data_store.write_json_string_to_file(json_string, output_file_path_specification, indent=indent+4)
        stop_time_t2 = time()
        logger.info(" "*(indent+2) + f"Successfully wrote JSON to file in '{stop_time_t2 - start_time_t2:.2f}' seconds (" + str(timedelta(seconds=(stop_time_t2 - start_time_t2))) + ").")
        logger.info("")

    else:
        logger.info(" "*(indent+2) + "Skipping JSON generation and writing because there is no subject pseudo identifier and/or no imaging procedures.")
        logger.info("")

    logger.info(" "*(indent+2) + f"Number of DICOM Studies processed:       '{data_store.total_number_of_dicom_studies_processed}'")
    logger.info(" "*(indent+2) + f"Number of DICOM Series processed:        '{data_store.total_number_of_dicom_series_processed}'")
    logger.info(" "*(indent+2) + f"Number of DICOM Instances processed:     '{data_store.total_number_of_dicom_instances_processed}'")
    logger.info(" "*(indent+2) + f"Number of DICOM Frames processed:        '{data_store.total_number_of_dicom_frames_processed}'")
    logger.info("")
    logger.info(" "*(indent+2) + f"Number of DICOM Studies skipped:         '{data_store.total_number_of_dicom_studies_skipped}'")
    logger.info(" "*(indent+2) + f"Number of DICOM Series skipped:          '{data_store.total_number_of_dicom_series_skipped}'")
    logger.info(" "*(indent+2) + f"Number of DICOM Instances skipped:       '{data_store.total_number_of_dicom_instances_skipped}'")
    logger.info("")

    n_procedures, n_series, n_frames = data_store.get_number_of_sphn_procedures_series_frames_stored()
    logger.info(" "*(indent+2) + f"Number of SPHN ImagingProcedures stored: '{n_procedures}'")
    logger.info(" "*(indent+2) + f"Number of SPHN ImagingSeries stored:     '{n_series}'")
    logger.info(" "*(indent+2) + f"Number of SPHN ImagingFrames stored:     '{n_frames}'")
    logger.info("")

    if len(data_store.skipped_sop_class_uid_dict) > 0:
        for item,(count,name) in data_store.skipped_sop_class_uid_dict.items():
            logger.info(" "*(indent+2) + f"Skipped SOP Class UID: '{item}' with name: '{name}' and count: '{count}'.")
        logger.info("")

    if len(data_store.skipped_frame_type_dict) > 0:
        for item,count in data_store.skipped_frame_type_dict.items():
            logger.info(" "*(indent+2) + f"Skipped Frame Type term: '{item}' with count: '{count}'.")
        logger.info("")

    if len(data_store.contrast_bolus_agent_dict) > 0:
        for item,count in data_store.contrast_bolus_agent_dict.items():
            logger.info(" "*(indent+2) + f"Contrast Bolus Agent text: '{item}' with count: '{count}'.")
        logger.info("")

    if len(data_store.contrast_bolus_ingredient_dict) > 0:
        for item,count in data_store.contrast_bolus_ingredient_dict.items():
            logger.info(" "*(indent+2) + f"Contrast Bolus Ingredient term: '{item}' with count: '{count}'.")
        logger.info("")

    if len(data_store.unknown_contrast_bolus_agent_sequence_codes_dict) > 0:
        for (coding_scheme_designator, code_value, code_meaning), count in data_store.unknown_contrast_bolus_agent_sequence_codes_dict.items():
            logger.info(" "*(indent+2) + f"Unknown Contrast Bolus Agent Sequence code: coding scheme designator: '{coding_scheme_designator}', code value: '{code_value}', code meaning: '{code_meaning}' with count: '{count}'.")
        logger.info("")

    if len(data_store.contrast_bolus_agent_sequence_codes_dict) > 0:
        for (coding_scheme_designator, code_value, code_meaning), count in data_store.contrast_bolus_agent_sequence_codes_dict.items():
            logger.info(" "*(indent+2) + f"Contrast Bolus Agent Sequence code: coding scheme designator: '{coding_scheme_designator}', code value: '{code_value}', code meaning: '{code_meaning}' with count: '{count}'.")
        logger.info("")

    stop_time_t1 = time()
    logger.info(" "*(indent+2) + f"Total processing time:'{stop_time_t1 - start_time_t1:.2f}' seconds (" + str(timedelta(seconds=(stop_time_t1 - start_time_t1))) + ").")

    logger.info(" "*(indent+0) + "Done...")

    return

#
# Edwin 2026-07-14
#
def create_logger() -> LoggerProtocol:
    """Create a logger for the application."""
    logger = logging.getLogger("DICOM2SPHN")
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
    except (OSError, ValueError) as e:
        logger.error(" "*(indent+0) + f"Error reading DICOM file '{file_path}': '{e}'")
        return None

def process_dicom_tags(datasets: list[Dataset|None], output_file: Path, logger: LoggerProtocol, level: int = 0,  indent: int = 0) -> None:
    """Process the DICOM tags and print the results."""

    dicom_tags = sorted({tag for ds in datasets if ds is not None for tag in ds})

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
