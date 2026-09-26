"""
import_config_settings.py: 
    Part of the example dicom2sphn package.
    It contains the functions for importing configuration settings.
"""
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from time import time

from pydicom.uid import UID
from pynetdicom import sop_class
from pynetdicom.service_class import StorageServiceClass

from .api_users import DicomwebAPIUser, OrthancRestAPIUser
from .context import Context
from .data_store import DataStore
from .sphn_concepts.sphn_code import CodingSystemList, SPHNCode
from .sphn_concepts.sphn_data_provider import SPHNDataProvider
from .sphn_concepts.sphn_data_release import SPHNDataRelease
from .sphn_concepts.sphn_department import SPHNDepartment
from .sphn_concepts.sphn_healthcare_primary_information_system import (
    SPHNHealthcarePrimaryInformationSystem,
)
from .sphn_concepts.sphn_source_system import SPHNSourceSystem
from .sphn_schema_graph import SPHNSchemaGraph
from .tools import is_clean_string, is_valid_string


#
# Edwin 2026-07-14
#
class ImportConfigSettingsError(Exception):
    """Custom exception for errors in the import_config_settings module."""


#
# Edwin 2026-07-15
#
def import_config_settings(config_file: Path, context: Context, indent: int=0) -> Context:
    """Import settings from a TOML configuration file and add them to the context."""

    # Checks
    assert isinstance(config_file,Path)
    assert isinstance(context,Context)
    assert isinstance(indent,int) and indent>=0

    # -----------------------------------------------------------------------------------------------------------------
    # Load settings from the configuration file
    # -----------------------------------------------------------------------------------------------------------------

    context.logger.info(" "*(indent+0) + "Trying to load settings from file.")

    settings = load_settings_from_configuration_file(config_file, context, indent=indent+2)

    context.logger.info(" "*(indent+0) + "Successfully loaded settings from file.")

    # -----------------------------------------------------------------------------------------------------------------
    # Process the SPHN settings
    # -----------------------------------------------------------------------------------------------------------------

    context.logger.info(" "*(indent+0) + "Trying to select the SPHN settings.")

    # SPHN Settings
    if "SPHN" not in settings:
        raise ImportConfigSettingsError("No 'SPHN' settings found.")

    sphn_settings = settings["SPHN"]

    if not isinstance(sphn_settings, dict):
        raise ImportConfigSettingsError("The 'SPHN' settings have the wrong format.")

    context.logger.info(" "*(indent+0) + "Successfully selected the SPHN settings.")

    # -----------------------------------------------------------------------------------------------------------------
    # Process the SPHN settings: RDF Schema
    # -----------------------------------------------------------------------------------------------------------------

    context.logger.info(" "*(indent+0) + "Trying to process the SPHN RDF schema file path settings.")

    sphn_rdf_schema_file_path = read_sphn_rdf_schema_file_path_settings(sphn_settings, context, indent=indent+2)

    context.logger.info(" "*(indent+0) + "Successfully processed the SPHN RDF schema file path settings.")

    context.logger.info(" "*(indent+0) + f"Trying to load SPHN RDF schema file '{sphn_rdf_schema_file_path}'.")

    if not sphn_rdf_schema_file_path.is_file():
        raise ImportConfigSettingsError(f"The 'sphn_rdf_schema_file_path' setting points to a non-existing file: '{sphn_rdf_schema_file_path}'.")

    sphn_schema = SPHNSchemaGraph(sphn_rdf_schema_file_path)

    sphn_schema_version = sphn_schema.get_version()

    context.sphn_schema = sphn_schema        

    context.logger.info(" "*(indent+0) + f"Successfully loaded the SPHN RDF schema file, version: '{sphn_schema_version!s}'.")

    # -----------------------------------------------------------------------------------------------------------------
    # Process the SPHN settings: SPHN DataProvider
    # -----------------------------------------------------------------------------------------------------------------

    context.logger.info(" "*(indent+0) + "Trying to process the SPHN DataProvider settings.")

    sphn_data_provider = read_sphn_data_provider_settings(sphn_settings, context, indent=indent+2)

    context.logger.info(" "*(indent+0) + "Successfully processed the SPHN DataProvider settings.")

    # -----------------------------------------------------------------------------------------------------------------
    # Process the SPHN settings: SPHN SourceSystem
    # -----------------------------------------------------------------------------------------------------------------

    context.logger.info(" "*(indent+0) + "Trying to process the SPHN SourceSystem settings.")

    sphn_source_system = read_sphn_source_system_settings(sphn_settings, context, indent=indent+2)

    context.logger.info(" "*(indent+0) + "Successfully processed the SPHN SourceSystem settings.")

    # -----------------------------------------------------------------------------------------------------------------
    # Process the SPHN settings: SPHN DataRelease
    # -----------------------------------------------------------------------------------------------------------------

    context.logger.info(" "*(indent+0) + "Trying to create the SPHN DataRelease concept.")

    # Timestamp: The time in seconds since the epoch. The epoch is: 1 January 1970 at 00:00:00 UTC.
    timestamp = time()
    # Convert to dateTime string
    extraction_date_time = datetime.fromtimestamp(timestamp, tz=UTC)
    # extraction_date_time_str = extraction_date_time.strftime("%Y-%m-%dT%H:%M:%S")
    # extraction_date_time_str = extraction_date_time.isoformat(timespec='milliseconds')

    context.logger.info(" "*(indent+2) + f"Using the extraction date/time: '{extraction_date_time.isoformat(timespec='milliseconds')}'.")

    # Get the SPHN Schema version, like: "https://biomedit.ch/rdf/sphn-schema/sphn/2026/1"
    sphn_schema_version = context.sphn_schema.get_version()

    sphn_data_release = SPHNDataRelease(
        has_data_provider=sphn_data_provider,
        conforms_to=sphn_schema_version,
        has_extraction_datetime=extraction_date_time,
        sphn_schema=context.sphn_schema)

    context.logger.info(" "*(indent+0) + "Successfully created the SPHN DataRelease concept.")

    # -----------------------------------------------------------------------------------------------------------------
    # Process the DICOM settings: Allowed SOP Classes
    # -----------------------------------------------------------------------------------------------------------------

    context.logger.info(" "*(indent+0) + "Trying to process the allowed SOP Classes settings.")

    sop_classes_specified = get_allowed_sop_classes_from_dicom_options_settings(settings, context, indent=indent+2)
    
    context.logger.info(" "*(indent+2) + f"Found {len(sop_classes_specified)} valid SOP class settings.")

    context.logger.info(" "*(indent+0) + "Successfully processed the allowed SOP Classes settings.")

    # -----------------------------------------------------------------------------------------------------------------
    # Process the DICOM settings: StudyDate and StudyTime for DICOM Studies without a date/time
    # -----------------------------------------------------------------------------------------------------------------

    context.logger.info(" "*(indent+0) + "Trying to process the StudyDate and StudyTime settings for DICOM Studies without a date/time.")

    fallback_study_date_time = get_fallback_study_date_time_from_dicom_options_settings(settings, context, indent=indent+2)

    context.logger.info(" "*(indent+2) + f"Using StudyDateTime: '{fallback_study_date_time}' for DICOM Studies without a date/time.")

    context.logger.info(" "*(indent+0) + "Successfully processed the StudyDate and StudyTime settings.")

    # -----------------------------------------------------------------------------------------------------------------
    # Create the DataStore
    # -----------------------------------------------------------------------------------------------------------------

    context.logger.info(" "*(indent+0) + "Trying to create the DataStore.")

    data_store = DataStore(
        sphn_data_release=sphn_data_release,
        sphn_data_provider=sphn_data_provider,
        sphn_source_system=sphn_source_system,
        sphn_schema=context.sphn_schema,
        valid_sop_classes=sop_classes_specified,
        fallback_study_date_time=fallback_study_date_time)
    
    context.data_store = data_store

    context.logger.info(" "*(indent+0) + "Successfully created the DataStore.")

    # -----------------------------------------------------------------------------------------------------------------
    # Process the Orthanc REST API user settins
    # -----------------------------------------------------------------------------------------------------------------

    # context.logger.info(" "*(indent+0) + "Trying to process the Orthanc REST API user settings.")

    # orthanc_rest_api_user = get_orthanc_rest_api_user_from_settings(settings, context, indent=indent+2)
    # context.logger.info(" "*(indent+2) + "Orthanc REST API user settings found.")
    # context.orthanc_rest_api_user = orthanc_rest_api_user

    # context.logger.info(" "*(indent+0) + "Successfully processed the Orthanc REST API user settings.")

    # -----------------------------------------------------------------------------------------------------------------
    # Process the DICOMweb API user settings
    # -----------------------------------------------------------------------------------------------------------------

    context.logger.info(" "*(indent+0) + "Trying to process the DICOMweb API user settings.")

    dicomweb_api_user = get_dicomweb_api_user_from_settings(settings, context, indent=indent+2)
    
    context.dicomweb_api_user = dicomweb_api_user

    context.logger.info(" "*(indent+0) + "Successfully processed the DICOMweb API user settings.")

    # -----------------------------------------------------------------------------------------------------------------

    # Return the updated context
    return context


#
# Edwin 2026-07-13
#
def load_settings_from_configuration_file(config_file: Path, context: Context, indent: int=0) -> dict:
    """Load settings from a TOML configuration file and return them as a dictionary."""

    # Checks
    assert isinstance(config_file,Path)
    assert isinstance(context,Context)
    assert isinstance(indent,int) and indent>=0

    context.logger.info(" "*(indent+0) + f"Trying to load settings from configuration file '{config_file}'.")

    try:
        with open(config_file, "rb") as f:
            settings = tomllib.load(f)
            context.logger.info(" "*(indent+0) + f"Successfully loaded settings from configuration file '{config_file}'.")
    except (OSError, FileNotFoundError, ValueError) as e:
        raise ImportConfigSettingsError(f"Error reading configuration file '{config_file}': '{e}'")

    if not isinstance(settings, dict):
        raise ImportConfigSettingsError(f"The settings loaded from configuration file '{config_file}' have the wrong format.")

    return settings


#
# Edwin 2026-07-06
#
def read_sphn_rdf_schema_file_path_settings(sphn_settings: dict, context: Context, indent: int=0) -> Path:
    """
    Reads the SPHN RDF schema settings from the configuration settings and returns the path to the SPHN RDF schema file.
    Input: settings in dictionary format
    Output: Path object
    """

    # Checks
    assert isinstance(sphn_settings, dict)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    if "sphn_rdf_schema_file_path" not in sphn_settings:
        raise ImportConfigSettingsError("The 'SPHN' settings are missing the 'sphn_rdf_schema_file_path' field.")

    sphn_rdf_schema_file_path_str = sphn_settings["sphn_rdf_schema_file_path"]

    if not is_valid_string(sphn_rdf_schema_file_path_str):
        raise ImportConfigSettingsError("The 'sphn_rdf_schema_file_path' setting has an invalid string value.")

    assert isinstance(sphn_rdf_schema_file_path_str, str)

    sphn_rdf_schema_file_path = Path(sphn_rdf_schema_file_path_str)

    return sphn_rdf_schema_file_path


#
# Edwin 2026-07-06
#
def read_sphn_data_provider_settings(sphn_settings:dict, context: Context, indent: int=0) -> SPHNDataProvider:
    """
    Reads the SPHN DataProvider settings from the configuration settings
    Input: SPHN settings in dictionary format
    Output: SPHN DataProvider object
    """
    
    # Checks
    assert isinstance(sphn_settings,dict)
    assert isinstance(context,Context)
    assert isinstance(indent,int) and indent>=0
    assert context.sphn_schema is not None
    
    if "data_provider" not in sphn_settings:
        raise ImportConfigSettingsError("The 'SPHN' settings are missing the 'data_provider' field.")
    
    data_provider_settings = sphn_settings["data_provider"]

    if not isinstance(data_provider_settings, dict):
        raise ImportConfigSettingsError("The 'SPHN data_provider' settings have the wrong format.")

    ## Institution Code (SPHNCode) is mandatory for SPHN DataProvider

    if "institution_code" not in data_provider_settings:
        raise ImportConfigSettingsError("The 'SPHN data_provider' settings are missing the 'institution_code' settings.")

    institution_code_settings = data_provider_settings["institution_code"]

    if not isinstance(institution_code_settings, dict):
        raise ImportConfigSettingsError("The 'SPHN data_provider institution_code' settings have the wrong format.")

    sphn_code = read_sphn_code_settings(institution_code_settings, context, indent=indent+2)

    # SPHN DataProvider Category Value Set Member is optional for SPHN DataProvider

    data_provider_category = data_provider_settings.get("category", None)

    if data_provider_category is not None:
        if not is_clean_string(data_provider_category):
            raise ImportConfigSettingsError("The 'SPHN data_provider category' setting has an invalid string value.")
    
        assert isinstance(data_provider_category, str)

        if not context.sphn_schema.is_sphn_data_provider_category_value_set_member(data_provider_category):
            raise ImportConfigSettingsError("The 'SPHN data_provider category' setting is not a SPHN DataProvider category value set member.")

    assert data_provider_category is None or isinstance(data_provider_category, str)

    # Optional SPHN Department

    if "department" in data_provider_settings:

        sphn_department_settings = data_provider_settings["department"]

        if not isinstance(sphn_department_settings, dict):
            raise ImportConfigSettingsError("The 'SPHN data_provider department' settings have the wrong format.")
        
        sphn_department = read_sphn_data_provider_department_settings(sphn_department_settings, context, indent=indent+2)
    else:
        sphn_department = None

    # Create the SPHNDataProvider object
    sphn_data_provider = SPHNDataProvider(
        has_institution_code=sphn_code, 
        has_department=sphn_department,
        has_category=data_provider_category, 
        sphn_schema=context.sphn_schema)

    return sphn_data_provider


#
# Edwin 2026-07-13
#
def read_sphn_code_settings(code_settings:dict, context: Context, indent: int=0) -> SPHNCode:
    """
    Reads the SPHN Code settings from the configuration settings
    Input: code_settings in dictionary format
    Output: SPHNCode object
    """

    # Checks
    assert isinstance(code_settings,dict)
    assert isinstance(context,Context)
    assert isinstance(indent,int) and indent>=0
    assert context.sphn_schema is not None

    if "coding_system_and_version" not in code_settings:
        raise ImportConfigSettingsError("The 'code' settings are missing the 'coding_system_and_version' field.")

    coding_system = code_settings["coding_system_and_version"]

    if not is_valid_string(coding_system):
        raise ImportConfigSettingsError("The 'coding_system_and_version' setting has an invalid string value.")

    assert isinstance(coding_system, str)

    if coding_system not in CodingSystemList:
        raise ImportConfigSettingsError(f"The 'coding_system_and_version' setting has an unsupported coding system: {coding_system}")

    if "identifier" not in code_settings:
        raise ImportConfigSettingsError("The 'code' settings are missing the 'identifier' field.")

    identifier = code_settings["identifier"]

    if not is_valid_string(identifier):
        raise ImportConfigSettingsError("The 'identifier' setting has an invalid string value.")
    
    assert isinstance(identifier, str)

    name = code_settings.get("name", None)

    if name is not None and not is_valid_string(name):
        raise ImportConfigSettingsError("The 'name' setting has an invalid string value.")

    assert name is None or isinstance(name, str)

    # Create the SPHNCode object for UID
    sphn_code = SPHNCode(
        has_coding_system_and_version = coding_system,
        has_identifier = identifier,
        has_name = name,
        sphn_schema = context.sphn_schema)
    
    return sphn_code


#
# Edwin 2026-07-13
#
def read_sphn_data_provider_department_settings(department_settings:dict, context: Context, indent: int=0) -> SPHNDepartment:
    """
    Reads the SPHN DataProvider Department settings from the configuration settings
    Input: department_settings in dictionary format
    Output: SPHNDepartment object
    """

    # Checks
    assert isinstance(department_settings,dict)
    assert isinstance(context,Context)
    assert isinstance(indent,int) and indent>=0
    assert context.sphn_schema is not None

    # SPHN DataProvider Department Name is mandatory

    if "name" not in department_settings:
        raise ImportConfigSettingsError("The 'SPHN data_provider department' settings are missing the 'name' field.")

    name = department_settings["name"]

    if not is_valid_string(name):
        raise ImportConfigSettingsError("The 'SPHN data_provider department name' setting has an invalid string value.")

    assert isinstance(name, str)

    # Create the SPHNDepartment object
    sphn_department = SPHNDepartment(
        has_name = name, 
        sphn_schema = context.sphn_schema)

    return sphn_department

#
# Edwin 2026-07-14
#
def read_sphn_source_system_settings(sphn_settings:dict, context: Context, indent: int=0) -> SPHNSourceSystem:
    """
    Reads the SPHN SourceSystem settings from the configuration settings
    Input: SPHN settings in dictionary format
    Output: SPHNSourceSystem object
    """

    # Checks
    assert isinstance(sphn_settings,dict)
    assert isinstance(context,Context)
    assert isinstance(indent,int) and indent>=0
    assert context.sphn_schema is not None

    if "source_system" not in sphn_settings:
        raise ImportConfigSettingsError("The 'SPHN' settings are missing the 'source_system' field.")
    
    source_system_settings = sphn_settings["source_system"]

    if not isinstance(source_system_settings, dict):
        raise ImportConfigSettingsError("The 'SPHN source_system' settings have the wrong format.")

    # SPHM Source System Name is optional
    
    name = source_system_settings.get("name", None)

    if name is not None and not is_valid_string(name):
        raise ImportConfigSettingsError("The 'SPHN source_system name' setting has an invalid string value.")
    
    assert name is None or isinstance(name, str)

    # SPHN Source System Purpose Value Set Member is optional for SPHN SourceSystem

    source_system_purpose = source_system_settings.get("purpose", None)

    if source_system_purpose is not None:
        if not is_clean_string(source_system_purpose):
            raise ImportConfigSettingsError("The 'SPHN source_system purpose' setting has an invalid string value.")
    
        assert isinstance(source_system_purpose, str)

        if not context.sphn_schema.is_sphn_source_system_purpose_value_set_member(source_system_purpose):
            raise ImportConfigSettingsError("The 'SPHN source_system purpose' setting is not a SPHN SourceSystem purpose value set member.")

    assert source_system_purpose is None or isinstance(source_system_purpose, str)

    # SPHN Source System Category Value Set Member is optional for SPHN SourceSystem

    source_system_category = source_system_settings.get("category", None)

    if source_system_category is not None:
        if not is_clean_string(source_system_category):
            raise ImportConfigSettingsError("The 'SPHN source_system category' setting has an invalid string value.")
    
        assert isinstance(source_system_category, str)

        if not context.sphn_schema.is_sphn_source_system_category_value_set_member(source_system_category):
            raise ImportConfigSettingsError("The 'SPHN source_system category' setting is not a SPHN SourceSystem category value set member.")
        
    assert source_system_category is None or isinstance(source_system_category, str)

    # SPHN Source System Primary System is optional for SPHN SourceSystem

    source_system_primary_system = read_sphn_source_system_primary_system_settings(source_system_settings, context, indent=indent+2)

    # Create the SPHNSourceSystem object
    sphn_source_system = SPHNSourceSystem(
        has_name = name,
        has_purpose = source_system_purpose,
        has_category = source_system_category,
        has_primary_system = source_system_primary_system,
        sphn_schema = context.sphn_schema)

    return sphn_source_system


#
# Edwin 2026-07-14
#
def read_sphn_source_system_primary_system_settings(source_system_settings:dict, context: Context, indent: int=0) -> SPHNHealthcarePrimaryInformationSystem:
    """
    Reads the SPHN SourceSystem Primary System settings from the configuration settings
    Input: source_system_settings in dictionary format
    Output: SPHNHealthcarePrimaryInformationSystem object
    """

    # Checks
    assert isinstance(source_system_settings,dict)
    assert isinstance(context,Context)
    assert isinstance(indent,int) and indent>=0
    assert context.sphn_schema is not None

    if "healthcare_primary_information_system" not in source_system_settings:
        raise ImportConfigSettingsError("The 'SPHN source_system' settings are missing the 'healthcare_primary_information_system' field.")
    
    primary_system_settings = source_system_settings["healthcare_primary_information_system"]

    if not isinstance(primary_system_settings, dict):
        raise ImportConfigSettingsError("The 'SPHN source_system healthcare_primary_information_system' settings have the wrong format.")

    # SPHN Healthcare Primary Information System Name is optional
    
    name = primary_system_settings.get("name", None)

    if name is not None and not is_valid_string(name):
        raise ImportConfigSettingsError("The 'SPHN source_system healthcare_primary_information_system name' setting has an invalid string value.")
    
    assert name is None or isinstance(name, str)

    # SPHN Healthcare Primary Information System Code (SPHNCode) is optional for SPHN Healthcare Primary Information System

    code_settings = primary_system_settings.get("code", None)

    if code_settings is not None:
        if not isinstance(code_settings, dict):
            raise ImportConfigSettingsError("The 'SPHN source_system healthcare_primary_information_system code' settings have the wrong format.")

        sphn_code = read_sphn_code_settings(code_settings, context, indent=indent+2)
    else:
        sphn_code = None

    # Create the SPHNHealthcarePrimaryInformationSystem object
    sphn_primary_system = SPHNHealthcarePrimaryInformationSystem(
        has_name = name,
        has_code = sphn_code,
        sphn_schema = context.sphn_schema)

    return sphn_primary_system


#
# Edwin 2026-07-06
#
def get_orthanc_rest_api_user_from_settings(settings:dict, context: Context, indent: int=0) -> OrthancRestAPIUser:
    """Get the Orthanc REST API user settings from the configuration settings and return them as an OrthancRestAPIUser object."""

    # Checks
    assert isinstance(settings,dict)
    assert isinstance(context,Context)
    assert isinstance(indent,int) and indent>=0

    if "orthanc_rest_api_user" not in settings:
        raise ImportConfigSettingsError("No 'orthanc_rest_api_user' settings found.")

    orthanc_rest_api_user_settings = settings["orthanc_rest_api_user"]
    
    if not isinstance(orthanc_rest_api_user_settings, dict):
        raise ImportConfigSettingsError("The 'orthanc_rest_api_user' settings have the wrong format.")
    
    if "username" not in orthanc_rest_api_user_settings:
        raise ImportConfigSettingsError("Orthanc REST API user settings is missing the 'username' field.")
    
    if not is_valid_string(orthanc_rest_api_user_settings["username"]):
        raise ImportConfigSettingsError("Orthanc REST API user settings has an invalid 'username' string value.")

    if "password" not in orthanc_rest_api_user_settings:
        raise ImportConfigSettingsError("Orthanc REST API user settings is missing the 'password' field.")
    
    if not is_valid_string(orthanc_rest_api_user_settings["password"]):
        raise ImportConfigSettingsError("Orthanc REST API user settings has an invalid 'password' string value.")

    if "base_url" not in orthanc_rest_api_user_settings:
        raise ImportConfigSettingsError("Orthanc REST API user settings is missing the 'base_url' field.")

    if not is_valid_string(orthanc_rest_api_user_settings["base_url"]):
        raise ImportConfigSettingsError("Orthanc REST API user settings has an invalid 'base_url' string value.")

    orthanc_rest_api_user = OrthancRestAPIUser(
        base_url=orthanc_rest_api_user_settings["base_url"], 
        username=orthanc_rest_api_user_settings["username"], 
        password=orthanc_rest_api_user_settings["password"])
    
    return orthanc_rest_api_user


#
# Edwin 2026-07-14
#
def get_dicomweb_api_user_from_settings(settings:dict, context: Context, indent: int=0) -> DicomwebAPIUser:
    """Get the DICOMweb API user settings from the configuration settings and return them as an DicomwebAPIUser object."""
    
    # Checks
    assert isinstance(settings,dict)
    assert isinstance(context,Context)
    assert isinstance(indent,int) and indent>=0

    if "dicomweb_api_user" not in settings:
        raise ImportConfigSettingsError("No 'dicomweb_api_user' settings found.")

    dicomweb_api_user_settings = settings["dicomweb_api_user"]
    
    if not isinstance(dicomweb_api_user_settings, dict):
        raise ImportConfigSettingsError("The 'dicomweb_api_user' settings have the wrong format.")
    
    if "username" not in dicomweb_api_user_settings:
        raise ImportConfigSettingsError("DICOMweb API user settings is missing the 'username' field.")
    
    if not is_valid_string(dicomweb_api_user_settings["username"]):
        raise ImportConfigSettingsError("DICOMweb API user settings has an invalid 'username' string value.")

    if "password" not in dicomweb_api_user_settings:
        raise ImportConfigSettingsError("DICOMweb API user settings is missing the 'password' field.")
    
    if not is_valid_string(dicomweb_api_user_settings["password"]):
        raise ImportConfigSettingsError("DICOMweb API user settings has an invalid 'password' string value.")

    if "base_url" not in dicomweb_api_user_settings:
        raise ImportConfigSettingsError("DICOMweb API user settings is missing the 'base_url' field.")

    if not is_valid_string(dicomweb_api_user_settings["base_url"]):
        raise ImportConfigSettingsError("DICOMweb API user settings has an invalid 'base_url' string value.")

    if "timeout_seconds" not in dicomweb_api_user_settings:
        raise ImportConfigSettingsError("DICOMweb API user settings is missing the 'timeout_seconds' field.")

    if not isinstance(dicomweb_api_user_settings["timeout_seconds"], (int, float)) or dicomweb_api_user_settings["timeout_seconds"] < 20:
        raise ImportConfigSettingsError("DICOMweb API user settings has an invalid 'timeout_seconds' value. It must be a number greater than or equal to 20.")

    try:
        timeout_seconds = float(dicomweb_api_user_settings["timeout_seconds"])
    except ValueError:
        raise ImportConfigSettingsError("DICOMweb API user settings has an invalid 'timeout_seconds' value. It must be a number greater than or equal to 20.")

    dicomweb_api_user = DicomwebAPIUser(
        base_url=dicomweb_api_user_settings["base_url"], 
        username=dicomweb_api_user_settings["username"], 
        password=dicomweb_api_user_settings["password"],
        timeout_seconds=timeout_seconds)

    return dicomweb_api_user


#
# Edwin 2026-07-06
#
def get_allowed_sop_classes_from_dicom_options_settings(settings:dict, context: Context, indent: int=0) -> dict[UID,str]:
    """Get the allowed SOP Classes that are specified in the 'dicom options' in the configuration settings and return them as a dictionary."""

    # Checks
    assert isinstance(settings,dict)
    assert isinstance(context,Context)
    assert isinstance(indent,int) and indent>=0

    if "dicom_options" not in settings:
        raise ImportConfigSettingsError("No 'dicom_options' settings found in the configuration settings.")
    
    dicom_options_settings = settings["dicom_options"]

    if not isinstance(dicom_options_settings, dict):
        raise ImportConfigSettingsError("The 'dicom_options' settings have the wrong format.")
    
    if "allowed_sop_classes" not in dicom_options_settings:
        raise ImportConfigSettingsError("No 'allowed_sop_classes' found in the 'dicom_options' settings.")
    
    if not isinstance(dicom_options_settings["allowed_sop_classes"], list):
        raise ImportConfigSettingsError("The 'allowed_sop_classes' settings have the wrong format. Expected a list of dictionaries with 'UID' and 'Meaning' fields.")
    
    # Start with an empty dictionary to store the allowed SOP Classes
    allowed_sop_classes = {}
    
    for i, allowed_sop_class in enumerate(dicom_options_settings["allowed_sop_classes"]):
        
        if not isinstance(allowed_sop_class, dict):
            raise ImportConfigSettingsError(f"One of the SOP classes (index {i}) in 'allowed_sop_classes' has the wrong format. Expected a dictionary with 'UID' and 'Meaning' fields.")
        
        if "UID" not in allowed_sop_class or "Meaning" not in allowed_sop_class:
            raise ImportConfigSettingsError(f"One of the SOP classes (index {i}) in 'allowed_sop_classes' is missing the 'UID' or 'Meaning' field.")

        if not is_valid_string(allowed_sop_class["UID"]) or not is_valid_string(allowed_sop_class["Meaning"]):
            raise ImportConfigSettingsError(f"One of the SOP classes (index {i}) in 'allowed_sop_classes' has an invalid 'UID' or 'Meaning' string value.")

        uid = UID(allowed_sop_class["UID"])
        
        if not uid.is_valid:
            raise ImportConfigSettingsError(f"One of the SOP classes (index {i}) has an invalid SOP Class UID: '{allowed_sop_class['UID']}'.")
        
        # Check if the UID is a valid UID and corresponds to a Storage Service Class
        if sop_class.uid_to_service_class(uid) != StorageServiceClass:
            raise ImportConfigSettingsError(f"One of the SOP classes (index {i}) has a valid UID format: '{allowed_sop_class['UID']}', but it is not a Storage Service Class UID.")

        allowed_sop_classes[uid] = allowed_sop_class["Meaning"]

    if len(allowed_sop_classes) == 0:
        raise ImportConfigSettingsError("No SOP classes found in the 'allowed_sop_classes' settings.")

    return allowed_sop_classes


#
# Edwin 2026-08-07
#
def get_fallback_study_date_time_from_dicom_options_settings(settings:dict, context: Context, indent: int=0) -> datetime:
    """
    Get the Fallback StudyDate and StudyTime from the 'dicom_options' 
    in the configuration settings and return them as a combined datetime.
    """

    # Checks
    assert isinstance(settings,dict)
    assert isinstance(context,Context)
    assert isinstance(indent,int) and indent>=0

    if "dicom_options" not in settings:
        raise ImportConfigSettingsError("No 'dicom_options' settings found in the configuration settings.")
    
    dicom_options_settings = settings["dicom_options"]

    if not isinstance(dicom_options_settings, dict):
        raise ImportConfigSettingsError("The 'dicom_options' settings have the wrong format.")

    if "fallback_study_date" not in dicom_options_settings:
        raise ImportConfigSettingsError("No 'fallback_study_date' found in the 'dicom_options' settings.")

    if "fallback_study_time" not in dicom_options_settings:
        raise ImportConfigSettingsError("No 'fallback_study_time' found in the 'dicom_options' settings.")

    fallback_study_date = dicom_options_settings["fallback_study_date"]
    fallback_study_time = dicom_options_settings["fallback_study_time"]

    # Validate the date and time formats
    try:
        result_date = datetime.strptime(fallback_study_date,"%Y-%m-%d").replace(tzinfo=UTC).date()
    except ValueError as e:
        raise ImportConfigSettingsError(f"Failed to parse 'fallback_study_date' in the 'dicom_options' settings (expected format: 'YYYY-MM-DD'): {e}")
    
    try:
        result_time = datetime.strptime(fallback_study_time,"%H:%M:%S").replace(tzinfo=UTC).time()
    except ValueError as e:
        raise ImportConfigSettingsError(f"Failed to parse 'fallback_study_time' in the 'dicom_options' settings (expected format: 'HH:MM:SS'): {e}")

    # Combine date and time
    result_datetime = datetime.combine(result_date, result_time, tzinfo=UTC)

    return result_datetime
