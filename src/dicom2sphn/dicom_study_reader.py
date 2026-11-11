"""
dicom_study_reader.py:
    Part of the example dicom2sphn package.
    It contains functions for reading DICOM Study metadata for the SPHN ImagingProcedure concept.
"""

from datetime import datetime

from pydicom import Dataset

from .context import Context
from .data_converter import DataConverter
from .sphn_concepts.sphn_administrative_sex import SPHNAdministrativeSex
from .sphn_concepts.sphn_age import SPHNAge
from .sphn_concepts.sphn_body_height import SPHNBodyHeight
from .sphn_concepts.sphn_body_mass_index import SPHNBodyMassIndex
from .sphn_concepts.sphn_body_weight import SPHNBodyWeight
from .sphn_concepts.sphn_code import SPHNCode
from .sphn_concepts.sphn_data_determination import SPHNDataDetermination
from .sphn_concepts.sphn_imaging_procedure import SPHNImagingProcedure
from .sphn_concepts.sphn_quantity import SPHNQuantity
from .sphn_concepts.sphn_source_system import SPHNSourceSystem
from .sphn_concepts.sphn_subject_pseudo_identifier import SPHNSubjectPseudoIdentifier
from .sphn_concepts.sphn_unit import SPHNUnit
from .tools import combine_dicom_date_and_time, get_dicom_timezone, is_valid_string

type Code = tuple[str, str, str]  # tuple[system, code, description] for UCUM unit code
type Age = tuple[int, Code]  # (value, ucum_unit_code)

#
# Edwin 2026-08-09
# 
def get_study_metadata_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> None:
    """
    Get the metadata related to SPHN ImagingFrame from the dataset
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
    sphn_schema = data_store.sphn_schema

    # The SPHN Imaging Procedure, Subject Pseudo Identifier, and Source System must be available in the data store
    assert isinstance(data_store.sphn_imaging_procedure, SPHNImagingProcedure)            
    assert isinstance(data_store.sphn_subject_pseudo_identifier, SPHNSubjectPseudoIdentifier)
    assert isinstance(data_store.sphn_source_system, SPHNSourceSystem)

    # -------------------------------------------------------------------------------------------------------------

    # 
    # StudyDate and StudyTime
    #

    if data_store.study_start_datetime is None:

        # Date
        study_date = get_study_date_from_dicom(dataset, context, indent=indent+2)

        if study_date is not None:
            assert isinstance(study_date, str)
            logger.debug(" "*(indent+0) + f"StudyDate string from DICOM: '{study_date}'")
        else:
            logger.debug(" "*(indent+0) + "StudyDate not found")

        # Time
        study_time = get_study_time_from_dicom(dataset, context, indent=indent+2)

        if study_time is not None:
            assert isinstance(study_time, str)
            logger.debug(" "*(indent+0) + f"StudyTime string from DICOM: '{study_time}'")
        else:
            logger.debug(" "*(indent+0) + "StudyTime not found")

        # DICOM dates and times are local times: get the timezone (TimezoneOffsetFromUTC or the configured local timezone)
        assert context.local_timezone is not None
        dicom_timezone = get_dicom_timezone(dataset, context.local_timezone, logger, indent=indent+2)

        # Combine StudyDate and StudyTime
        study_start_datetime_obj = None
        if study_date and study_time:

            # Combine the StudyDate and StudyTime strings into a single complete DICOM datetime (DT) object
            # - study datetime is completed by filling in missing components for Month, Day, Hour, Minute, Second
            study_start_datetime_obj = combine_dicom_date_and_time(study_date, study_time, dicom_timezone, logger, indent=indent+2)

        elif study_date and not study_time:

            # Combine the StudyDate and a missing or empty StudyTime strings into a single complete DICOM datetime (DT) object
            # - study datetime is completed by filling in missing components for Month, Day, Hour, Minute, Second
            study_start_datetime_obj = combine_dicom_date_and_time(study_date, "", dicom_timezone, logger, indent=indent+2)
        else:
            logger.debug(" "*(indent+0) + "Could not combine StudyDate and StudyTime: Study Date not defined")
        
        if study_start_datetime_obj is not None:
            # Set the study start datetime in the data store
            data_store.study_start_datetime = study_start_datetime_obj
            logger.debug(" "*(indent+0) + f"Combined Study Date and Time: '{study_start_datetime_obj!s}'")

            # Update the SPHN ImagingProcedure start datetime
            data_store.sphn_imaging_procedure.has_start_datetime = study_start_datetime_obj
            logger.debug(" "*(indent+0) + f"Updated SPHN ImagingProcedure has_start_datetime: '{study_start_datetime_obj.isoformat(timespec='milliseconds')}'")
        else:
            logger.debug(" "*(indent+0) + "Could not combine StudyDate and StudyTime")

    # Set the start datetime for the SPHN ImagingProcedure if it has not been set already
    if data_store.sphn_imaging_procedure.has_start_datetime is None:
        # Use the fallback StudyDate and StudyTime for SPHN ImagingProcedure has_start_datetime as it is mandatory in SPHN
        study_start_datetime = data_store.fallback_study_datetime
        assert isinstance(study_start_datetime, datetime)
        logger.debug(" "*(indent+0) + f"Using 'fallback_study_datetime': '{study_start_datetime!s}'")
        # Set the ImagingProcedure property
        data_store.sphn_imaging_procedure.has_start_datetime =  study_start_datetime
        logger.debug(" "*(indent+0) + f"Added SPHN ImagingProcedure has_start_datetime: '{study_start_datetime.isoformat(timespec='milliseconds')}'")

    # -------------------------------------------------------------------------------------------------------------

    # 
    # StudyDescription
    #

    if data_store.sphn_imaging_procedure.has_description is None:
    
        study_description = get_study_description_from_dicom(dataset, context, indent=indent+2)

        if study_description is not None:

            assert is_valid_string(study_description)

            # Set the ImagingProcedure property
            data_store.sphn_imaging_procedure.has_description = study_description
            logger.debug(" "*(indent+0) + f"Added SPHN ImagingProcedure has_description: '{study_description}'")
        else:
            logger.debug(" "*(indent+0) + "SPHN ImagingProcedure has_description not defined")

    # -------------------------------------------------------------------------------------------------------------

    # 
    # Imaging Procedure Code list
    #

    # DICOM Procedure Code Sequence tag is not implemented yet

    # -------------------------------------------------------------------------------------------------------------

    # 
    # PatientAge
    #

    if data_store.sphn_imaging_procedure.has_subject_age is None:

        patient_age = get_patient_age_from_dicom(dataset, context, indent=indent+2)

        if patient_age is not None:
            # Set the ImagingProcedure property

            # Age: (value, (system, code, description))
            assert isinstance(patient_age, tuple) \
                and len(patient_age) == 2 \
                and isinstance(patient_age[0], (int, float)) \
                and isinstance(patient_age[1], tuple) \
                and len(patient_age[1]) == 3 \
                and all(is_valid_string(item) for item in patient_age[1])
            assert isinstance(data_store.sphn_imaging_procedure.has_start_datetime, datetime)

            sphn_code_age = SPHNCode( 
                sphn_schema = sphn_schema,
                has_coding_system_and_version = patient_age[1][0],
                has_identifier = patient_age[1][1],
                has_name = patient_age[1][2]
                )
            sphn_unit_age = SPHNUnit(
                sphn_schema = sphn_schema,
                has_code = sphn_code_age
                )
            sphn_quantity_age = SPHNQuantity(
                sphn_schema = sphn_schema,
                has_value = patient_age[0],
                has_unit = sphn_unit_age
                )
            sphn_age = SPHNAge(
                sphn_schema = sphn_schema,
                has_quantity = sphn_quantity_age,
                has_determination_datetime = data_store.sphn_imaging_procedure.has_start_datetime,
                has_subject_pseudo_identifier = data_store.sphn_subject_pseudo_identifier,
                has_source_system_list = [data_store.sphn_source_system]
                )

            data_store.sphn_imaging_procedure.has_subject_age = sphn_age

            logger.debug(" "*(indent+0) + f"Added SPHN ImagingProcedure has_subject_age value: '{patient_age[0]}', unit UCUM code:'{patient_age[1]}'")
        else:
            logger.debug(" "*(indent+0) + "SPHN ImagingProcedure has_subject_age not defined")

    # -------------------------------------------------------------------------------------------------------------

    # 
    # PatientSize
    #

    if data_store.sphn_imaging_procedure.has_subject_body_height is None:
    
        patient_size = get_patient_size_from_dicom(dataset, context, indent=indent+2)

        if patient_size is not None:
            # Set the ImagingProcedure property

            assert isinstance(patient_size, (int, float))
            assert isinstance(data_store.sphn_imaging_procedure.has_start_datetime, datetime)

            # The DICOM unit for Patient Size is always "meter"
            size_ucum_unit =  ("UCUM", "m", "meter")

            sphn_code_body_height = SPHNCode( 
                sphn_schema = sphn_schema,
                has_coding_system_and_version = size_ucum_unit[0],
                has_identifier = size_ucum_unit[1],
                has_name = size_ucum_unit[2]
                )
            sphn_unit_body_height = SPHNUnit(
                sphn_schema = sphn_schema,
                has_code = sphn_code_body_height
                )
            sphn_quantity_body_height = SPHNQuantity(
                sphn_schema = sphn_schema,
                has_value = patient_size,
                has_unit = sphn_unit_body_height
                )

            sphn_code_data_determination = SPHNCode( 
                sphn_schema = sphn_schema,
                has_identifier = "87982008", # SNOMED 87982008 | Manual (qualifier value) |
                has_coding_system_and_version = "SNOMED"
                )

            sphn_data_determination = SPHNDataDetermination(
                sphn_schema = sphn_schema,
                has_method_code = sphn_code_data_determination
                )

            sphn_body_height = SPHNBodyHeight(
                sphn_schema = sphn_schema,
                has_quantity = sphn_quantity_body_height,
                has_datetime = data_store.sphn_imaging_procedure.has_start_datetime,
                has_data_determination = sphn_data_determination
                )

            data_store.sphn_imaging_procedure.has_subject_body_height = sphn_body_height

            logger.debug(" "*(indent+0) + f"Added SPHN ImagingProcedure subject_body_height value: '{patient_size}', unit code:'{size_ucum_unit}'")
        else:
            logger.debug(" "*(indent+0) + "SPHN ImagingProcedure subject_body_height not defined")

    # -------------------------------------------------------------------------------------------------------------

    # 
    # PatientWeight
    #

    if data_store.sphn_imaging_procedure.has_subject_body_weight is None:

        patient_weight = get_patient_weight_from_dicom(dataset, context, indent=indent+2)

        if patient_weight is not None:
            # Set the ImagingProcedure property

            assert isinstance(patient_weight, (int, float))
            assert isinstance(data_store.sphn_imaging_procedure.has_start_datetime, datetime)

            # The DICOM unit for Patient weight is "kilogram"
            weight_ucum_unit = ("UCUM", "kg", "kilogram") 

            sphn_code_body_weight = SPHNCode( 
                sphn_schema = sphn_schema,
                has_coding_system_and_version = weight_ucum_unit[0],
                has_identifier = weight_ucum_unit[1],
                has_name = weight_ucum_unit[2]
                )
            sphn_unit_body_weight = SPHNUnit(
                sphn_schema = sphn_schema,
                has_code = sphn_code_body_weight
                )
            sphn_quantity_body_weight = SPHNQuantity(
                sphn_schema = sphn_schema,
                has_value = patient_weight,
                has_unit = sphn_unit_body_weight
                )

            sphn_code_data_determination = SPHNCode( 
                sphn_schema = sphn_schema,
                has_coding_system_and_version = "SNOMED",
                has_identifier = "87982008" # SNOMED 87982008 | Manual (qualifier value) |
                )

            sphn_data_determination = SPHNDataDetermination(
                sphn_schema = sphn_schema,
                has_method_code = sphn_code_data_determination
                )

            sphn_body_weight = SPHNBodyWeight(
                sphn_schema = sphn_schema,
                has_quantity = sphn_quantity_body_weight,
                has_datetime = data_store.sphn_imaging_procedure.has_start_datetime,
                has_data_determination = sphn_data_determination
                )

            data_store.sphn_imaging_procedure.has_subject_body_weight = sphn_body_weight

            logger.debug(" "*(indent+0) + f"Added SPHN ImagingProcedure subject_body_weight value: '{patient_weight}', unit code:'{weight_ucum_unit}'")
        else:
            logger.debug(" "*(indent+0) + "SPHN ImagingProcedure subject_body_weight not defined")

    # -------------------------------------------------------------------------------------------------------------

    # 
    # PatientBodyMassIndex
    #

    if data_store.sphn_imaging_procedure.has_subject_body_mass_index is None:

        bmi_value = get_patient_body_mass_index_from_dicom(dataset, context, indent=indent+2)

        if bmi_value is not None:
            # Set the ImagingProcedure property

            assert isinstance(bmi_value, (int, float))
            assert isinstance(data_store.sphn_imaging_procedure.has_start_datetime, datetime)

            # The DICOM unit for Patient Body Mass Index is "kg/m2"
            bmi_ucum_unit = ("UCUM", "kgperm2", "kilogram per square meter") 

            sphn_code_bmi = SPHNCode( 
                sphn_schema = sphn_schema,
                has_coding_system_and_version = bmi_ucum_unit[0],
                has_identifier = bmi_ucum_unit[1],
                has_name = bmi_ucum_unit[2]
                )
            sphn_unit_bmi = SPHNUnit(
                sphn_schema = sphn_schema,
                has_code = sphn_code_bmi
                )
            sphn_quantity_bmi = SPHNQuantity(
                sphn_schema = sphn_schema,
                has_value = bmi_value,
                has_unit = sphn_unit_bmi
                )
            
            sphn_body_mass_index = SPHNBodyMassIndex(
                sphn_schema = sphn_schema,
                has_quantity = sphn_quantity_bmi,
                has_subject_pseudo_identifier = data_store.sphn_subject_pseudo_identifier,
                has_source_system_list = [data_store.sphn_source_system],
                has_determination_datetime = data_store.sphn_imaging_procedure.has_start_datetime,
                has_administrative_case = None
                )

            data_store.sphn_imaging_procedure.has_subject_body_mass_index = sphn_body_mass_index

            logger.debug(" "*(indent+0) + f"Added SPHN ImagingProcedure has_subject_body_mass_index value: '{bmi_value}', unit code:'{bmi_ucum_unit}'")
        else:
            logger.debug(" "*(indent+0) + "SPHN ImagingProcedure has_subject_body_mass_index not defined")

    # -------------------------------------------------------------------------------------------------------------


    # 
    # PatientSex
    # 

    if data_store.sphn_imaging_procedure.has_subject_administrative_sex is None:
        
        result = get_patient_sex_from_dicom(dataset, context, indent=indent+2)

        if result is not None:
            # Set the ImagingProcedure property

            assert isinstance(data_store.sphn_imaging_procedure.has_start_datetime, datetime)

            sphn_code_sex = SPHNCode( 
                sphn_schema = sphn_schema,
                has_identifier = result[1],
                has_coding_system_and_version = result[0],
                has_name = result[2],
                )

            sphn_administrative_sex = SPHNAdministrativeSex(
                sphn_schema = sphn_schema,
                has_code = sphn_code_sex,
                has_subject_pseudo_identifier = data_store.sphn_subject_pseudo_identifier,
                has_source_system_list = [data_store.sphn_source_system],
                has_record_datetime = data_store.sphn_imaging_procedure.has_start_datetime
                )
            
            data_store.sphn_imaging_procedure.has_subject_administrative_sex = sphn_administrative_sex

            logger.debug(" "*(indent+0) + f"Added SPHN ImagingProcedure has_subject_administrative_sex value: '({result[0]},{result[1]},{result[2]})'")
        else:
            logger.debug(" "*(indent+0) + "SPHN ImagingProcedure has_subject_administrative_sex not defined")

    # -------------------------------------------------------------------------------------------------------------

    # 
    # PregnancyStatus
    # 

    if data_store.sphn_imaging_procedure.has_subject_pregnancy_status_code is None:

        result = get_pregnancy_status_from_dicom(dataset, context, indent=indent+2)

        if result is not None:
            # Set the ImagingProcedure property

            sphn_code_pregnancy_status = SPHNCode( 
                sphn_schema = sphn_schema,
                has_identifier = result[1],
                has_coding_system_and_version = result[0],
                has_name = result[2]
                )

            data_store.sphn_imaging_procedure.has_subject_pregnancy_status_code = sphn_code_pregnancy_status

            logger.debug(" "*(indent+0) + f"Added SPHN ImagingProcedure has_subject_pregnancy_status_code value: '({result[0]},{result[1]},{result[2]})'")
        else:
            logger.debug(" "*(indent+0) + "SPHN ImagingProcedure has_subject_pregnancy_status_code not defined")

# -----------------------------------------------------------------------------------------------------------------
# DICOM tag reading functions for SPHN ImagingProcedure metadata
# -----------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-11
#
def get_study_date_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM StudyDate tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:	                (0008,0020)
    # Type:	                Required, Empty if Unknown (2)
    # Keyword:              StudyDate
    # Value Multiplicity:   1
    # Value Representation: Date (DA)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM StudyDate tag
    value = dataset.get("StudyDate", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM StudyDate tag was not found")  
        return None

    # Convert value to str and trim whitespace
    try:
        value_str = str(value).strip()
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM StudyDate tag value could not be converted to str")
        return None

    if not value_str:
        logger.debug(" "*(indent+0) + "DICOM StudyDate tag contains only whitespace")
        return None

    assert is_valid_string(value_str)

    return value_str


#
# Edwin 2026-11-11
#
def get_study_time_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM StudyTime tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:	                (0008,0030)
    # Type:	                Required, Empty if Unknown (2)
    # Keyword:              StudyTime
    # Value Multiplicity:   1
    # Value Representation: Time (TM)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM StudyTime tag
    value = dataset.get("StudyTime", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM StudyTime tag was not found")  
        return None

    # Convert value to str and trim whitespace
    try:
        value_str = str(value).strip()
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM StudyTime tag value could not be converted to str")
        return None

    if not value_str:
        logger.debug(" "*(indent+0) + "DICOM StudyTime tag contains only whitespace")
        return None

    assert is_valid_string(value_str)

    return value_str


#
# Edwin 2026-11-11
#
def get_study_description_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM StudyDescription tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:	                (0008,1030)
    # Type:	                Optional (3)
    # Keyword:              StudyDescription
    # Value Multiplicity:   1
    # Value Representation: Long String (LO)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM StudyDescription tag
    value = dataset.get("StudyDescription", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM StudyDescription tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    value_str = value.strip()

    if not value_str:
        logger.debug(" "*(indent+0) + "DICOM StudyDescription tag contains only whitespace")
        return None

    assert is_valid_string(value_str)

    return value_str


#
# Edwin 2026-11-11
#
def get_patient_age_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Age|None:
    """
    Returns the value and UCUM coded unit corresponding to the value of the DICOM PatientAge tag
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0010,1010)
    # Type:	                Optional (3)
    # Keyword:              PatientAge
    # Value Multiplicity:   1
    # Value Representation: Age String (AS)

    # Info on AS: 
    #   https://dicom.nema.org/medical/dicom/current/output/chtml/part05/sect_6.2.html#table_6.2-1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM PatientAge tag
    value = dataset.get("PatientAge", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM PatientAge tag was not found")  
        return None

    # It should be a string
    assert isinstance(value, str)

    # Trim whitespace
    patient_age_str = value.strip()

    # Check if value is not empty
    if len(patient_age_str) == 0:
        logger.debug(" "*(indent+0) + "DICOM PatientAge tag contains only whitespace")
        return None

    # The Age String format is either: nnnD, nnnW, nnnM, or nnnY
    if len(patient_age_str) != 4:
        logger.warning(" "*(indent+0) + "DICOM PatientAge tag value has an unknown format")
        return None

    # Get the unit. The Age String format is either: nnnD, nnnW, nnnM, or nnnY
    if patient_age_str[3] == "Y":
        patient_age_ucum_coded_unit = ("UCUM", "a", "year")
    elif patient_age_str[3] == "M":
        patient_age_ucum_coded_unit = ("UCUM", "mo", "month")
    elif patient_age_str[3] == "W":
        patient_age_ucum_coded_unit = ("UCUM", "wk", "week")
    elif patient_age_str[3] == "D":
        patient_age_ucum_coded_unit = ("UCUM", "d", "day")
    else:
        logger.warning(" "*(indent+0) + f"DICOM PatientAge tag value: '{patient_age_str}', has an unknown unit format")
        return None

    # Try to get the integer value
    try:
        patient_age_value = int(patient_age_str[:-1])
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + f"DICOM PatientAge tag value: '{patient_age_str}', could not be converted to an integer value")
        return None

    if patient_age_value < 0:
        logger.warning(" "*(indent+0) + f"DICOM PatientAge tag value: '{patient_age_value}', is not a valid value")
        return None

    return patient_age_value, patient_age_ucum_coded_unit

#
# Edwin 2026-11-11
#
def get_patient_size_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the value corresponding to the value of the DICOM PatientSize tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """
    # Tag:                  (0010,1020)
    # Type:	                Optional (3)
    # Keyword:              PatientSize
    # Value Multiplicity:   1
    # Value Representation: Decimal String (DS)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM PatientSize tag
    value = dataset.get("PatientSize", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM PatientSize tag was not found")  
        return None

    # Convert value to float
    try:
        value_float = float(value)
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM PatientSize tag value could not be converted to float")
        return None

    if value_float < 0.00:
        logger.warning(" "*(indent+0) + f"DICOM PatientSize tag value: '{value_float}' is not a valid value")
        return None

    if value_float > 3.00:
        logger.warning(" "*(indent+0) + f"DICOM PatientSize tag value: '{value_float}' is likely not a valid value")
                    
    return value_float

#
# Edwin 2026-11-11
#
def get_patient_weight_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the value corresponding to the value of the DICOM PatientWeight tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:	                (0010,1030)
    # Type:	                Optional (3)
    # Keyword:              PatientWeight
    # Value Multiplicity:   1
    # Value Representation: Decimal String (DS)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM PatientWeight tag
    value = dataset.get("PatientWeight", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM PatientWeight tag was not found")  
        return None

    # Convert value to float
    try:
        value_float = float(value)
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM PatientWeight tag value could not be converted to float")
        return None

    if value_float < 0.00:
        logger.warning(" "*(indent+0) + f"DICOM PatientWeight tag value: '{value_float}' is not a valid value")
        return None

    if value_float > 800.00:
        logger.debug(" "*(indent+0) + f"DICOM PatientWeight tag value: '{value_float}' is likely not a valid value")
    
    return value_float

#
# Edwin 2026-11-11
#
def get_patient_body_mass_index_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the value corresponding to the value of the DICOM PatientBodyMassIndex tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag: 	                (0010,1022)
    # Type:	                Optional (3)
    # Keyword:              PatientBodyMassIndex
    # Value Multiplicity:   1
    # Value Representation: Decimal String (DS)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM PatientBodyMassIndex tag
    value = dataset.get("PatientBodyMassIndex", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM PatientBodyMassIndex tag was not found")  
        return None

    # Convert value to float
    try:
        value_float = float(value)
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM PatientBodyMassIndex tag value could not be converted to float")
        return None

    if value_float < 0.00:
        logger.warning(" "*(indent+0) + f"DICOM PatientBodyMassIndex tag value: '{value_float}' is not a valid value")
        return None
            
    if value_float > 300.00:
        logger.debug(" "*(indent+0) + f"DICOM PatientBodyMassIndex tag value: '{value_float}' is likely not a valid value")

    return value_float


#
# Edwin 2026-11-11
#
def get_patient_sex_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Code|None:
    """
    Returns the SNOMED-CT code corresponding to the value of the DICOM PatientSex tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:	                (0010,0040)
    # Type:	                Required, Empty if Unknown (2)
    # Keyword:              PatientSex
    # Value Multiplicity:   1
    # Value Representation: Code String (CS)

    # Note:
    #   Available in CR, DX, CT, MR, PT, enhanced CT, enhanced MR, enhanced PT

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM PatientSex tag
    value = dataset.get("PatientSex", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM PatientSex tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    value_str = value.strip()

    if not value_str:
        logger.debug(" "*(indent+0) + "DICOM PatientSex tag contains only whitespace")
        return None
    
    # Convert to SNOMED CT code (using upper case key)
    result = DataConverter.dicom_patient_sex_code_dict.get(value_str.upper(), None)

    if result is None:
        logger.debug(" "*(indent+0) + f"DICOM PatientSex tag value: '{value_str}' could not be converted to a corresponding SNOMED-CT code.")
        return None

    # Check
    assert isinstance(result, tuple) \
        and len(result) == 3 \
        and all(is_valid_string(item) for item in result)

    return result


#
# Edwin 2026-11-11
#
def get_pregnancy_status_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Code|None:
    """
    Returns the SNOMED-CT code corresponding to the value of the DICOM PregnancyStatus tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:	                (0010,21C0)
    # Type:	                Optional (3)
    # Keyword:              PregnancyStatus
    # Value Multiplicity:   1
    # Value Representation: Unsigned Short (US)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM PregnancyStatus tag
    value = dataset.get("PregnancyStatus", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM PregnancyStatus tag was not found")  
        return None

    # Convert value to int
    try:
        value_int = int(value)
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM PregnancyStatus tag value could not be converted to int")
        return None

    # Convert to SNOMED CT code
    result = DataConverter.dicom_pregnancy_status_code_dict.get(value_int, None)

    if result is None:
        logger.debug(" "*(indent+0) + f"DICOM PregnancyStatus tag value: '{value_int}' could not be converted to a corresponding SNOMED-CT code.")
        return None

    # Check
    assert isinstance(result, tuple) \
        and len(result) == 3 \
        and all(is_valid_string(item) for item in result)

    return result
