"""
dicom_study_reader.py:
    Part of the example dicom2sphn package.
    It contains functions for reading DICOM Study metadata for the SPHN ImagingProcedure concept.
"""

from datetime import datetime

import pydicom
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
from .tools import combine_dicom_date_and_time, is_valid_string

type UnitUCUMCode = str  # UCUM unit code as a string
type SnomedCTCode = str  # SNOMED-CT code as a string
type BMIValue = tuple[float, UnitUCUMCode]  # (value, unit_ucum_code)
type HeightValue = tuple[float, UnitUCUMCode]  # (value, unit_ucum_code)
type WeightValue = tuple[float, UnitUCUMCode]  # (value, unit_ucum_code)
type AgeValue = tuple[int, UnitUCUMCode]  # (value, unit_ucum_code)

#
# Edwin 2026-08-09
# 
def get_study_metadata_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> None:
    """
    Get the metadata related to SPHN ImagingFrame from the dataset
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
    # StudyDate
    #

    study_date_str = get_study_date_from_dicom(dataset, context, indent=indent+2)

    if study_date_str is not None:
        logger.debug(" "*(indent+0) + f"StudyDate: '{study_date_str}'")
    else:
        logger.debug(" "*(indent+0) + "No DICOM StudyDate found")

    # 
    # StudyTime
    #

    study_time_str = get_study_time_from_dicom(dataset, context, indent=indent+2)

    if study_time_str is not None:
        logger.debug(" "*(indent+0) + f"StudyTime: '{study_time_str}'")
    else:
        logger.debug(" "*(indent+0) + "No DICOM StudyTime found")

    # 
    # Combine StudyDate and StudyTime
    #

    study_start_datetime = None
    if study_date_str is not None and study_time_str is not None:
        # Combine date and time
        study_start_datetime = combine_dicom_date_and_time(study_date_str, study_time_str, logger=logger, indent=indent+2)

    if study_start_datetime is None:
        # Use the fallback StudyDate and StudyTime for SPHN ImagingProcedure has_start_datetime as it is mandatory in SPHN
        logger.debug(" "*(indent+0) + f"Using 'fallback_study_date_time': '{data_store.fallback_study_date_time.isoformat(timespec='milliseconds')}'")
        study_start_datetime = data_store.fallback_study_date_time

    assert isinstance(study_start_datetime, datetime)
    assert isinstance(data_store.sphn_imaging_procedure, SPHNImagingProcedure)

    # Set the ImagingProcedure property
    data_store.sphn_imaging_procedure.has_start_datetime =  study_start_datetime
    logger.debug(" "*(indent+0) + f"Added SPHN ImagingProcedure has_start_datetime: '{study_start_datetime.isoformat(timespec='milliseconds')}'")
    
    # -------------------------------------------------------------------------------------------------------------

    # 
    # StudyDescription
    #

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

    # Checks
    assert isinstance(data_store.sphn_subject_pseudo_identifier, SPHNSubjectPseudoIdentifier)
    assert isinstance(data_store.sphn_source_system, SPHNSourceSystem)
    assert isinstance(data_store.sphn_imaging_procedure.has_start_datetime, datetime)

    patient_age = get_patient_age_from_dicom(dataset, context, indent=indent+2)

    if patient_age is not None:
        # Set the ImagingProcedure property

        sphn_code_age = SPHNCode( 
            sphn_schema = sphn_schema,
            has_identifier = patient_age[1],
            has_coding_system_and_version = "UCUM"
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
            has_determination_date_time = data_store.sphn_imaging_procedure.has_start_datetime,
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

    # Checks
    assert isinstance(data_store.sphn_imaging_procedure.has_start_datetime, datetime)

    patient_size = get_patient_size_from_dicom(dataset, context, indent=indent+2)

    if patient_size is not None:
        # Set the ImagingProcedure property

        sphn_code_body_height = SPHNCode( 
            sphn_schema = sphn_schema,
            has_identifier = patient_size[1],
            has_coding_system_and_version = "UCUM"
            )
        sphn_unit_body_height = SPHNUnit(
            sphn_schema = sphn_schema,
            has_code = sphn_code_body_height
            )
        sphn_quantity_body_height = SPHNQuantity(
            sphn_schema = sphn_schema,
            has_value = patient_size[0],
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
            has_date_time = data_store.sphn_imaging_procedure.has_start_datetime,
            has_data_determination = sphn_data_determination
            )

        data_store.sphn_imaging_procedure.has_subject_body_height = sphn_body_height

        logger.debug(" "*(indent+0) + f"Added SPHN ImagingProcedure subject_body_height value: '{patient_size[0]}', unit UCUM code:'{patient_size[1]}'")
    else:
        logger.debug(" "*(indent+0) + "SPHN ImagingProcedure subject_body_height not defined")

    # -------------------------------------------------------------------------------------------------------------

    # 
    # PatientWeight
    #

    # Checks
    assert isinstance(data_store.sphn_imaging_procedure.has_start_datetime, datetime)

    patient_weight = get_patient_weight_from_dicom(dataset, context, indent=indent+2)

    if patient_weight is not None:
        # Set the ImagingProcedure property

        sphn_code_body_weight = SPHNCode( 
            sphn_schema = sphn_schema,
            has_identifier = patient_weight[1],
            has_coding_system_and_version = "UCUM"
            )
        sphn_unit_body_weight = SPHNUnit(
            sphn_schema = sphn_schema,
            has_code = sphn_code_body_weight
            )
        sphn_quantity_body_weight = SPHNQuantity(
            sphn_schema = sphn_schema,
            has_value = patient_weight[0],
            has_unit = sphn_unit_body_weight
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

        sphn_body_weight = SPHNBodyWeight(
            sphn_schema = sphn_schema,
            has_quantity = sphn_quantity_body_weight,
            has_date_time = data_store.sphn_imaging_procedure.has_start_datetime,
            has_data_determination = sphn_data_determination
            )

        data_store.sphn_imaging_procedure.has_subject_body_weight = sphn_body_weight

        logger.debug(" "*(indent+0) + f"Added SPHN ImagingProcedure subject_body_weight value: '{patient_weight[0]}', unit UCUM code:'{patient_weight[1]}'")
    else:
        logger.debug(" "*(indent+0) + "SPHN ImagingProcedure subject_body_weight not defined")

    # -------------------------------------------------------------------------------------------------------------

    # 
    # PatientBodyMassIndex
    #

    # Checks
    assert isinstance(data_store.sphn_subject_pseudo_identifier, SPHNSubjectPseudoIdentifier)
    assert isinstance(data_store.sphn_source_system, SPHNSourceSystem)
    assert isinstance(data_store.sphn_imaging_procedure.has_start_datetime, datetime)

    patient_bmi = get_patient_body_mass_index_from_dicom(dataset, context, indent=indent+2)

    if patient_bmi is not None:
        # Set the ImagingProcedure property

        sphn_code_bmi = SPHNCode( 
            sphn_schema = sphn_schema,
            has_identifier = patient_bmi[1],
            has_coding_system_and_version = "UCUM"
            )
        sphn_unit_bmi = SPHNUnit(
            sphn_schema = sphn_schema,
            has_code = sphn_code_bmi
            )
        sphn_quantity_bmi = SPHNQuantity(
            sphn_schema = sphn_schema,
            has_value = patient_bmi[0],
            has_unit = sphn_unit_bmi
            )
        
        sphn_body_mass_index = SPHNBodyMassIndex(
            sphn_schema = sphn_schema,
            has_quantity = sphn_quantity_bmi,
            has_subject_pseudo_identifier = data_store.sphn_subject_pseudo_identifier,
            has_source_system_list = [data_store.sphn_source_system],
            has_determination_date_time = data_store.sphn_imaging_procedure.has_start_datetime,
            has_administrative_case = None
            )

        data_store.sphn_imaging_procedure.has_subject_body_mass_index = sphn_body_mass_index

        logger.debug(" "*(indent+0) + f"Added SPHN ImagingProcedure has_subject_body_mass_index value: '{patient_bmi[0]}', unit UCUM code:'{patient_bmi[1]}'")
    else:
        logger.debug(" "*(indent+0) + "SPHN ImagingProcedure has_subject_body_mass_index not defined")

    # -------------------------------------------------------------------------------------------------------------


    # 
    # PatientSex
    # 

    # Checks
    assert isinstance(data_store.sphn_subject_pseudo_identifier, SPHNSubjectPseudoIdentifier)
    assert isinstance(data_store.sphn_source_system, SPHNSourceSystem)
    assert isinstance(data_store.sphn_imaging_procedure.has_start_datetime, datetime)

    result = get_patient_sex_from_dicom(dataset, context, indent=indent+2)

    if result is not None:
        # Set the ImagingProcedure property

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
            has_record_date_time = data_store.sphn_imaging_procedure.has_start_datetime
            )
        
        data_store.sphn_imaging_procedure.has_subject_administrative_sex = sphn_administrative_sex

        logger.debug(" "*(indent+0) + f"Added SPHN ImagingProcedure has_subject_administrative_sex value: '({result[0]},{result[1]},{result[2]})'")
    else:
        logger.debug(" "*(indent+0) + "SPHN ImagingProcedure has_subject_administrative_sex not defined")

    # -------------------------------------------------------------------------------------------------------------

    # 
    # PregnancyStatus
    # 

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
# Edwin 2026-08-08
#
def get_study_date_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str | None:
    """
    Returns the value corresponding to the value of the DICOM StudyDate tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              StudyDate
    # Value Representation: Date (DA)
    # Type:	                Required, Empty if Unknown (2)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "StudyDate" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM StudyDate tag was not found")
        return None

    # Get the DataElement
    data_element = dataset["StudyDate"]

    # Get the value
    value = data_element.value
        
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
        
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM StudyDate tag value was not provided")
        return None

    # It should be a single-valued tag, a string            
    if value_multiplicity != 1 or not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM StudyDate tag has an unknown format")
        return None
        
    # Remove whitespace
    study_date_str = value.strip()

    # Check if value is not empty
    if len(study_date_str) == 0:
        logger.warning(" "*(indent+0) + "DICOM StudyDate tag contains only whitespace")
        return None

    return study_date_str

#
# Edwin 2026-08-08
#
def get_study_time_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str | None:
    """
    Returns the value corresponding to the value of the DICOM StudyTime tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              StudyTime
    # Value Representation: Time (TM)
    # Type:	                Required, Empty if Unknown (2)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "StudyTime" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM StudyTime tag was not found")
        return None

    # Get the DataElement
    data_element = dataset["StudyTime"]

    # Get the value
    value = data_element.value
        
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
        
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM StudyTime tag value was not provided")
        return None
                
    # It should be a single-valued tag, a string
    if value_multiplicity != 1 or not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM StudyTime tag has an unknown format")
        return None

    # Remove whitespace
    study_time_str = value.strip()

    # Check if value is not empty
    if len(study_time_str) == 0:
        logger.debug(" "*(indent+0) + "DICOM StudyTime tag contains only whitespace")
        return None

    return study_time_str

#
# Edwin 2026-08-08
#
def get_study_description_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str | None:
    """
    Returns the value corresponding to the value of the DICOM StudyDescription tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              StudyDescription
    # Value Representation: Long String (LO)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "StudyDescription" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM StudyDescription tag was not found")            
        return None

    # Get the DataElement
    data_element = dataset["StudyDescription"]

    # Get the value
    value = data_element.value
        
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
        
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM StudyDescription tag value was not provided")
        return None
    
    # It should be a single-valued tag, a string
    if value_multiplicity != 1 or not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM StudyDescription tag has an unknown format")
        return None

    # Should already be string, Remove Whitespace
    study_description_str = value.strip()

    # Check if value is not empty
    if len(study_description_str) == 0:
        logger.debug(" "*(indent+0) + "DICOM StudyDescription tag contains only whitespace")
        return None
    
    return study_description_str

#
# Edwin 2026-08-08
#
def get_patient_age_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> AgeValue | None:
    """
    Returns the value and UCUM unit corresponding to the value of the DICOM PatientAge tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              PatientAge
    # Value Representation: Age String (AS)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Info on AS: 
    #   https://dicom.nema.org/medical/dicom/current/output/chtml/part05/sect_6.2.html#table_6.2-1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "PatientAge" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM PatientAge tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["PatientAge"]

    # Get the value
    value = data_element.value
        
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
        
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM PatientAge tag value was not provided")
        return None
    
    # It should be a single-valued tag, a string
    if value_multiplicity != 1 or not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM PatientAge tag has an unknown format")
        return None

    # Should already be str, remove whitespace
    patient_age_str = value.strip()

    # Check if value is not empty
    if len(patient_age_str) == 0:
        logger.debug(" "*(indent+0) + "DICOM PatientAge tag contains only whitespace")
        return None
    
    if len(patient_age_str) != 4:
        logger.warning(" "*(indent+0) + "DICOM PatientAge tag value has an unknown format")
        return None

    # Get the unit. The Age String format is either: nnnD, nnnW, nnnM, or nnnY
    if patient_age_str[3] == "Y":
        patient_age_ucum_unit = "a"
    elif patient_age_str[3] == "M":
        patient_age_ucum_unit = "mo"
    elif patient_age_str[3] == "D":
        patient_age_ucum_unit = "d"
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

    return patient_age_value, patient_age_ucum_unit

#
# Edwin 2026-08-09
#
def get_patient_size_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> HeightValue | None:
    """
    Returns the value and UCUM unit corresponding to the value of the DICOM PatientSize tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              PatientSize
    # Value Representation: Decimal String (DS)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Set initial value
    patient_size_ucum_unit =  "m" # The DICOM unit for Patient Size is always "meter"

    if "PatientSize" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM PatientSize tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["PatientSize"]

    # Get the value
    value = data_element.value
        
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
        
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM PatientSize tag value was not provided")
        return None
        
    # It should be a single-valued tag, a DSfloat
    if value_multiplicity != 1 or not isinstance(value, pydicom.valuerep.DSfloat):
        logger.warning(" "*(indent+0) + "DICOM PatientSize tag has an unknown format")
        return None
    
    # Try to convert DSfloat to float
    try:
        patient_size_value = float(value)
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM PatientSize tag value could not be converted to a float value")
        return None
    
    if patient_size_value < 0.00:
        logger.warning(" "*(indent+0) + f"DICOM PatientSize tag value: '{patient_size_value}' is not a valid value")
        return None

    if patient_size_value > 3.00:
        logger.warning(" "*(indent+0) + f"DICOM PatientSize tag value: '{patient_size_value}' is likely not a valid value")
                    
    return patient_size_value, patient_size_ucum_unit

#
# Edwin 2026-08-09
#
def get_patient_weight_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> WeightValue | None:
    """
    Returns the value and UCUM unit corresponding to the value of the DICOM PatientWeight tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              PatientWeight
    # Value Representation: Decimal String (DS)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Set initial value
    patient_weight_ucum_unit = "kg" # The DICOM unit for Patient weight is always "kilogram"

    if "PatientWeight" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM PatientWeight tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["PatientWeight"]

    # Get the value
    value = data_element.value
        
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
        
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM PatientWeight tag value was not provided")
        return None
    
    # It should be a single-valued tag, a DSfloat
    if value_multiplicity != 1 or not isinstance(value, pydicom.valuerep.DSfloat):
        logger.warning(" "*(indent+0) + "DICOM PatientWeight tag has an unknown format")
        return None
    
    # Try to convert DSfloat to float
    try:
        patient_weight_value = float(value)
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM PatientWeight tag value could not be converted to a float value")
        return None
    
    if patient_weight_value < 0.00:
        logger.warning(" "*(indent+0) + f"DICOM PatientWeight tag value: '{patient_weight_value}' is not a valid value")
        return None

    if patient_weight_value > 800.00:
        logger.warning(" "*(indent+0) + f"DICOM PatientWeight tag value: '{patient_weight_value}' is likely not a valid value")
    
    return patient_weight_value, patient_weight_ucum_unit

#
# Edwin 2026-08-09
#
def get_patient_body_mass_index_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> BMIValue | None:
    """
    Returns the value and UCUM unit corresponding to the value of the DICOM PatientBodyMassIndex tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              PatientBodyMassIndex
    # Value Representation: Decimal String (DS)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Set initial value
    patient_bmi_ucum_unit = "kgperm2" # The DICOM unit for Patient Body Mass Index is always "kg/m2"

    if "PatientBodyMassIndex" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM PatientBodyMassIndex tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["PatientBodyMassIndex"]

    # Get the value
    value = data_element.value
        
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
        
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM PatientBodyMassIndex tag value was not provided")
        return None
    
    # It should be a single-valued tag, a DSfloat
    if value_multiplicity != 1 or not isinstance(value, pydicom.valuerep.DSfloat):
        logger.warning(" "*(indent+0) + "DICOM PatientBodyMassIndex tag has unknown format")    
        return None
    
    # Try to convert DSfloat to float
    try:
        patient_bmi_value = float(value)
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM PatientBodyMassIndex tag value could not be converted to a float value")
        return None

    if patient_bmi_value < 0.00:
        logger.warning(" "*(indent+0) + f"DICOM PatientBodyMassIndex tag value: '{patient_bmi_value}' is not a valid value")
        return None
            
    if patient_bmi_value > 300.00:
        logger.warning(" "*(indent+0) + f"DICOM PatientBodyMassIndex tag value: '{patient_bmi_value}' is likely not a valid value")

    return patient_bmi_value, patient_bmi_ucum_unit

#
# Edwin 2026-08-09
#
def get_patient_sex_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> tuple[str,str,str] | None:
    """
    Returns the SNOMED-CT code corresponding to the value of the DICOM PatientSex tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              PatientSex
    # Value Representation: Code String (CS)
    # Type:	                Required, Empty if Unknown (2)
    # Value Multiplicity:   1

    # Note:
    #   Available in CR, DX, CT, MR, PT, enhanced CT, enhanced MR, enhanced PT

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "PatientSex" not in dataset:
        logger.warning(" "*(indent+0) + "DICOM PatientSex tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["PatientSex"]

    # Get the value
    value = data_element.value
        
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
        
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM PatientSex tag value was not provided")
        return None
    
    # It should be a single-valued tag, a string
    if value_multiplicity != 1 or not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM PatientSex tag has an unknown format")    
        return None

    # Remove whitespace
    patient_sex_str = value.strip()

    # Check if value is not empty
    if len(patient_sex_str) == 0:
        logger.debug(" "*(indent+0) + "DICOM PatientSex tag contains only whitespace")
        return None

    # Convert to SNOMED CT code (using upper case key)
    result = DataConverter.dicom_patient_sex_code_dict.get(patient_sex_str.upper(), None)

    assert result is None or (isinstance(result, tuple) and len(result) == 3)

    if result is None:
        logger.debug(" "*(indent+0) + f"DICOM PatientSex tag value: '{patient_sex_str}' could not be converted to a corresponding SNOMED-CT code.")
        return None

    return result

#
# Edwin 2026-08-09
#
def get_pregnancy_status_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> tuple[str,str,str] | None:
    """
    Returns the SNOMED-CT code corresponding to the value of the DICOM PregnancyStatus tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Keyword:              PregnancyStatus
    # Value Representation: Unsigned Short (US)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "PregnancyStatus" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM PregnancyStatus tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["PregnancyStatus"]

    # Get the value
    value = data_element.value
        
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
        
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM PregnancyStatus tag value was not provided")
        return None
        
    # It should be a single-valued tag, an integer
    if value_multiplicity != 1 or not isinstance(value, int):
        logger.warning(" "*(indent+0) + "DICOM PregnancyStatus tag has an unknown format")
        return None

    # Convert to SNOMED CT code
    result = DataConverter.dicom_pregnancy_status_code_dict.get(value, None)

    # Check conversion is ok
    assert result is None or (isinstance(result, tuple) and len(result) == 3)

    if result is None:
        logger.debug(" "*(indent+0) + f"DICOM PregnancyStatus tag value: '{value}' could not be converted to a corresponding SNOMED-CT code.")
        return None

    return result
