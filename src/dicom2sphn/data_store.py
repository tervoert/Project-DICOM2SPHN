"""
data_store.py: 
    Part of the example dicom2sphn package.
    It contains the DataStore class, which handles data storage.
"""

import json
from datetime import datetime
from pathlib import Path

from pathvalidate import sanitize_filepath
from pydicom import Dataset

from .sphn_concepts.sphn_body_site import SPHNBodySite
from .sphn_concepts.sphn_contrast_agent_administration_event import (
    SPHNContrastAgentAdministrationEvent,
)
from .sphn_concepts.sphn_data_compression_algorithm import SPHNDataCompressionAlgorithm
from .sphn_concepts.sphn_data_provider import SPHNDataProvider
from .sphn_concepts.sphn_data_release import SPHNDataRelease
from .sphn_concepts.sphn_image_dimensions import SPHNImageDimensions
from .sphn_concepts.sphn_imaging_device import SPHNImagingDevice
from .sphn_concepts.sphn_imaging_frame import SPHNImagingFrame
from .sphn_concepts.sphn_imaging_procedure import SPHNImagingProcedure
from .sphn_concepts.sphn_imaging_series import SPHNImagingSeries
from .sphn_concepts.sphn_pixel_dimensions import SPHNPixelDimensions
from .sphn_concepts.sphn_software import SPHNSoftware
from .sphn_concepts.sphn_source_system import SPHNSourceSystem
from .sphn_concepts.sphn_subject_pseudo_identifier import SPHNSubjectPseudoIdentifier
from .sphn_schema_graph import SPHNSchemaGraph
from .tools import generate_id, is_valid_string


#
# Edwin 2026-07-16
#
class DataStore:
    """
    A class to handle data storage.
    """
    # -----------------------------------------------------------------------------------------------------------------------------
    # Class variables set during init, obtained from the settings in the configuration file
    # -----------------------------------------------------------------------------------------------------------------------------
    sphn_data_release: SPHNDataRelease
    sphn_data_provider: SPHNDataProvider
    sphn_source_system: SPHNSourceSystem
    sphn_schema: SPHNSchemaGraph
    valid_sop_classes: dict[str, str]
    fallback_study_date_time: datetime

    # -----------------------------------------------------------------------------------------------------------------------------
    # Class variables set during the processing of the DICOM Patient - Study - Series - Instance hierarchical tree
    # -----------------------------------------------------------------------------------------------------------------------------

    # 
    # Statistics
    #
    total_number_of_dicom_studies_processed: int=0
    total_number_of_dicom_studies_skipped: int=0
    total_number_of_dicom_series_processed: int=0
    total_number_of_dicom_series_skipped: int=0
    total_number_of_dicom_instances_processed: int=0
    total_number_of_dicom_instances_skipped: int=0
    total_number_of_dicom_frames_processed: int=0

    number_of_dicom_studies_processed: int=0
    number_of_dicom_studies_skipped: int=0
    number_of_dicom_series_processed: int=0
    number_of_dicom_series_skipped: int=0
    number_of_dicom_instances_processed: int=0
    number_of_dicom_instances_skipped: int=0
    number_of_dicom_frames_processed: int=0

    number_of_sphn_imaging_frames_stored: int=0

    total_number_of_sphn_imaging_procedures_stored: int=0
    total_number_of_sphn_imaging_series_stored: int=0
    total_number_of_sphn_imaging_frames_stored: int=0

    number_of_sphn_imaging_frames_added_to_sphn_imaging_series: int=0
    number_of_sphn_imaging_series_added_to_sphn_imaging_procedure: int=0


    # Dictionary to keep track of skipped SOPClassUIDs and their names
    skipped_sop_class_uid_dict: dict[str, tuple[int, str]]  # Key: SOPClassUID, Value: (Count, SOPClassUIDName)
    skipped_frame_type_dict: dict[str, int] # Key: FrameType, Value: Count


    # Dictionary to keep track of DICOM contrast bolus agent
    contrast_bolus_agent_dict: dict[str, int] # Key: ContrastBolusAgent, Value: Count

    # Dictionary to keep track of DICOM contrast bolus ingredients
    contrast_bolus_ingredient_dict: dict[str, int] # Key: ContrastBolusIngredient, Value: Count

    # Dictionary to keep track of DICOM contrast bolus agent sequence codes
    contrast_bolus_agent_sequence_codes_dict: dict[tuple[str, str, str], int]  # Key: (coding_scheme_designator, code_value, code_descr), Value: Count

    # Dictionary to keep track of unknown DICOM contrast bolus agent sequence codes
    unknown_contrast_bolus_agent_sequence_codes_dict: dict[tuple[str, str, str], int]  # Key: (coding_scheme_designator, code_value, code_descr), Value: Count

    # Dictionary to keep track of DICOM contrast bolus administration route sequence codes
    contrast_bolus_administration_route_sequence_codes_dict: dict[tuple[str, str, str], int]  # Key: (coding_scheme_designator, code_value, code_descr), Value: Count

    # Dictionary to keep track of unknown DICOM contrast bolus administration route sequence codes
    unknown_contrast_bolus_administration_route_sequence_codes_dict: dict[tuple[str, str, str], int]  # Key: (coding_scheme_designator, code_value, code_descr), Value: Count

    # 
    # Patient level
    #
    patient_id: str|None=None
    file_id: str|None=None

    sphn_imaging_procedure_list: list[SPHNImagingProcedure]
    
    # 
    # Study level
    #
    current_study_number: int|None=None
    study_instance_uid: str|None=None
    number_of_study_related_series: int|None=None
    number_of_study_related_instances: int|None=None
    modalities_in_study_code_list: list[tuple[str, str, str]]|None=None                  # ToDo: Edwin: Not Used Yet
    modality_based_imaging_procedure_code_list: list[tuple[str, str, str]]|None=None

    sphn_imaging_series_list: list[SPHNImagingSeries]


    # 
    # Series level
    #
    current_series_number: int|None=None
    series_instance_uid: str|None=None
    number_of_series_related_instances: int|None=None

    modality_coding_scheme_designator: str|None=None
    modality_dcm_code: str|None=None
    modality_dcm_description: str|None=None

    number_of_frames_in_series: int=0

    # 
    # Imaging Device related
    #
    manufacturer_name: str|None=None
    manufacturer_model_name: str|None=None
    device_serial_number: str|None=None
    software_list: list[SPHNSoftware]|None=None

    sphn_imaging_device: SPHNImagingDevice|None=None

    # 
    # Instance level
    #
    current_instance_number: int|None=None
    sop_instance_uid: str|None=None
    sop_class_uid: str|None=None
    sop_class_uid_name: str|None=None
    number_of_frames_in_instance: int=0

    instance_ds: Dataset|None=None

    sphn_subject_pseudo_identifier: SPHNSubjectPseudoIdentifier|None=None
    sphn_imaging_procedure: SPHNImagingProcedure|None=None
    sphn_imaging_series: SPHNImagingSeries|None=None

    # 
    # Frame level - Values are set by the dw_frame_processor.py module
    #
    current_frame_number: int|None=None
    sphn_imaging_frame: SPHNImagingFrame|None=None
    sphn_pixel_dimensions: SPHNPixelDimensions|None=None
    sphn_image_dimensions: SPHNImageDimensions|None=None
    sphn_imagingframe_content_qualification_valueset_member: str|None=None
    sphn_body_site_list: SPHNBodySite|None=None
    sphn_data_compression_algorithm_list: list[SPHNDataCompressionAlgorithm]|None=None
    sphn_imagingframe_type_valueset_member_list: list[str]|None=None

    sphn_contrast_agent_administration_event_list: list[SPHNContrastAgentAdministrationEvent]|None=None
    
    #
    # Edwin 2026-07-16
    #
    def __init__(self, 
                 sphn_data_release: SPHNDataRelease, 
                 sphn_data_provider: SPHNDataProvider, 
                 sphn_source_system: SPHNSourceSystem, 
                 sphn_schema: SPHNSchemaGraph, 
                 valid_sop_classes: dict[str, str],
                 fallback_study_date_time: datetime):
        """
        Initializes the DataStore instance.
        """

        # Checks
        assert isinstance(sphn_data_release, SPHNDataRelease)
        assert isinstance(sphn_data_provider, SPHNDataProvider)
        assert isinstance(sphn_source_system, SPHNSourceSystem)
        assert isinstance(sphn_schema, SPHNSchemaGraph)
        assert isinstance(valid_sop_classes, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in valid_sop_classes.items())
        assert isinstance(fallback_study_date_time, datetime)

        self.sphn_data_release = sphn_data_release
        self.sphn_data_provider = sphn_data_provider
        self.sphn_source_system = sphn_source_system
        self.sphn_schema = sphn_schema
        self.valid_sop_classes = valid_sop_classes
        self.fallback_study_date_time = fallback_study_date_time

        self.sphn_imaging_procedure_list = []
        self.sphn_imaging_series_list = []

        self.skipped_sop_class_uid_dict = {}
        self.skipped_frame_type_dict = {}

        self.contrast_bolus_agent_dict = {}
        self.contrast_bolus_ingredient_dict = {}

        self.contrast_bolus_agent_sequence_codes_dict = {}
        self.unknown_contrast_bolus_agent_sequence_codes_dict = {}

        self.contrast_bolus_administration_route_sequence_codes_dict = {}
        self.unknown_contrast_bolus_administration_route_sequence_codes_dict = {}

        self.file_id = generate_id()

    # -----------------------------------------------------------------------------------------------------------------
    # JSON Generation for SPHN Connector
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-07-16 
    #
    def generate_json_string_for_sphn_connector(self, indent: int=0) -> str:
        """
        Generates a JSON string intended for the SPHN Connector.
        """

        # Checks
        assert isinstance(indent, int) and indent>=0
        assert self.sphn_data_release is not None and isinstance(self.sphn_data_release, SPHNDataRelease)
        assert self.sphn_data_provider is not None and isinstance(self.sphn_data_provider, SPHNDataProvider)
        assert self.sphn_subject_pseudo_identifier is not None and isinstance(self.sphn_subject_pseudo_identifier, SPHNSubjectPseudoIdentifier)
        assert self.file_id is not None and is_valid_string(self.file_id)

        


        # Get the sphn:DataRelease output (for the special concepts)
        data_release_dict = self.sphn_data_release.get_json_dict()
        assert data_release_dict is not None and isinstance(data_release_dict, dict)

        # Get the sphn:DataProvider output (for the special concepts)
        data_provider_dict = self.sphn_data_provider.get_json_dict()
        assert data_provider_dict is not None and isinstance(data_provider_dict, dict)

        # Get the sphn:SubjectPseudoIdentifier output (for the special concepts)
        subject_pseudo_identifier_dict = self.sphn_subject_pseudo_identifier.get_json_dict()
        assert subject_pseudo_identifier_dict is not None and isinstance(subject_pseudo_identifier_dict, dict)

        # Get "content" by calling get_json_dict for each SPHNImagingProcedure in the list
        content = {}
        for imaging_procedure in self.sphn_imaging_procedure_list:
            
            #assert isinstance(imaging_procedure, SPHNImagingProcedure)
            
            # Get the JSON dict for the imaging procedure and add it to the content
            # The returned Reference ID is ignored
            # The source_concept_id is set to 'fake_id' because it is not used in the content
            imaging_procedure.get_json_dict(content,'fake_id')

        # Create the final output dictionary
        output_dict = {
            "id": self.file_id,
            "schema": self.sphn_schema.get_version(),
            "title": "PatientRecord",
            "targetType": "RDF",
            "license": "",
            "sphn:DataRelease": data_release_dict,
            "sphn:DataProvider": data_provider_dict,
            "sphn:SubjectPseudoIdentifier": subject_pseudo_identifier_dict,
            "content": content,
        }

        json_output_string = json.dumps(output_dict, indent=4)
        return json_output_string
    

    #
    # Edwin 2026-07-16
    #
    def write_json_string_to_file(self, json_string: str, output_file_path_specification: str="output_patient_{patient_id}-file_{file_id}.json", indent: int=0) -> None:
        """
        Writes the JSON string to file
        input: json_string: str - The JSON string to write to file
               file_path_with_patient_id_indicator: str - The file path with the '{patient_id}' indicator to be replaced with the actual patient_id
        """

        # Checks
        assert isinstance(json_string, str)
        assert isinstance(output_file_path_specification, str)
        assert isinstance(indent, int) and indent>=0

        assert self.patient_id is not None and is_valid_string(self.patient_id)
        assert self.file_id is not None and is_valid_string(self.file_id)
        assert "{patient_id}" in Path(output_file_path_specification).name
        assert "{file_id}" in Path(output_file_path_specification).name

        file_path_replaced = output_file_path_specification.replace("{patient_id}", f"{self.patient_id}").replace("{file_id}", f"{self.file_id}")

        file_path_sanitized = sanitize_filepath(file_path=file_path_replaced, replacement_text="_")

        file_path = Path(file_path_sanitized)
        
        if file_path.is_file():
            raise FileExistsError(f"Output file path:'{file_path}' already exists.")

        # Writing
        with open(file_path, "w", encoding="utf-8") as outfile:
            outfile.write(json_string)


    # -----------------------------------------------------------------------------------------------------------------
    # Imaging Patient levelSPHN SubjectPseudoIdentifier
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-04
    # not used
    def reset_patient_level(self) -> None:
        """
        Resets the patient level data
        """
        self.sphn_subject_pseudo_identifier = None
        self.patient_id = None
        self.file_id = None
        self.sphn_imaging_procedure_list = []

    # -----------------------------------------------------------------------------------------------------------------
    # Imaging Study level - SPHN ImagingProcedure
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-04
    #
    def reset_imaging_study_level(self) -> None:
        """
        Resets the imaging study level data
        """
        self.sphn_imaging_procedure = None
        self.current_study_number = None
        self.study_instance_uid = None
        self.number_of_study_related_series = None
        self.number_of_study_related_instances = None
        self.modalities_in_study_code_list = None
        self.modality_based_imaging_procedure_code_list = None
        self.sphn_imaging_series_list = []

        self.number_of_dicom_series_processed = 0
        self.number_of_dicom_series_skipped = 0

        self.number_of_sphn_imaging_series_added_to_sphn_imaging_procedure = 0

    # -----------------------------------------------------------------------------------------------------------------
    # Imaging Series level - SPHNImagingSeries
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-04
    #
    def reset_imaging_series_level(self) -> None:
        """
        Resets the imaging series level data
        """
        self.sphn_imaging_series = None
        self.current_series_number = None
        self.series_instance_uid = None
        self.number_of_series_related_instances = None
        self.modality_coding_scheme_designator = None
        self.modality_dcm_code = None
        self.modality_dcm_description = None

        self.manufacturer_name = None
        self.manufacturer_model_name = None
        self.device_serial_number = None
        self.software_list = None
        self.sphn_imaging_device = None

        self.number_of_frames_in_series = 0

        self.number_of_dicom_instances_processed = 0
        self.number_of_dicom_instances_skipped = 0
        self.number_of_sphn_imaging_frames_stored = 0

        self.sphn_contrast_agent_administration_event_list = None

    # -----------------------------------------------------------------------------------------------------------------
    # Imaging Instance level
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-04
    #
    def reset_imaging_instance_level(self) -> None:
        """
        Resets the imaging instance level data
        """
        self.sphn_imaging_instance = None
        self.current_instance_number = None
        self.sop_instance_uid = None
        self.sop_class_uid = None
        self.sop_class_uid_name =None
        self.number_of_frames_in_instance = 0
        self.instance_ds = None

        self.number_of_dicom_frames_processed = 0
        self.number_of_sphn_imaging_frames_added_to_sphn_imaging_series = 0


    # -----------------------------------------------------------------------------------------------------------------
    # Imaging Frame level - SPHNImagingFrame
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-04
    #
    def reset_imaging_frame_level(self) -> None:
        """
        Resets the imaging frame level data
        """
        self.sphn_imaging_frame = None
        self.current_frame_number = None
        self.sphn_pixel_dimensions = None
        self.sphn_image_dimensions = None
        self.sphn_imagingframe_content_qualification_valueset_member = None
        self.sphn_body_site_list = None
        self.sphn_imagingframe_type_valueset_member_list = None
        self.sphn_data_compression_algorithm_list = None

    # -----------------------------------------------------------------------------------------------------------------
    # Statistics
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-07-30
    #
    def add_skipped_frame_type_to_dict(self, frame_type: str) -> None:
        """
        Adds a skipped frame (or image) type to the dictionary for statistics.
        """
        
        # Checks
        assert is_valid_string(frame_type)
        assert self.skipped_frame_type_dict is not None and isinstance(self.skipped_frame_type_dict, dict)

        if frame_type not in self.skipped_frame_type_dict:
            self.skipped_frame_type_dict[frame_type] = 1
        else:
            self.skipped_frame_type_dict[frame_type] += 1


    #
    # Edwin 2026-07-24
    #
    def add_skipped_sop_class_uid_to_dict(self, sop_class_uid: str, sop_class_uid_name: str) -> None:
        """
        Adds a skipped SOPClassUID and its name to the dictionary for statistics.
        """
        
        # Checks
        assert is_valid_string(sop_class_uid)
        assert is_valid_string(sop_class_uid_name)
        assert self.skipped_sop_class_uid_dict is not None and isinstance(self.skipped_sop_class_uid_dict, dict)

        if sop_class_uid not in self.skipped_sop_class_uid_dict:
            self.skipped_sop_class_uid_dict[sop_class_uid] = (1, sop_class_uid_name)
        else:
            self.skipped_sop_class_uid_dict[sop_class_uid] = (self.skipped_sop_class_uid_dict[sop_class_uid][0] + 1, sop_class_uid_name)


    #
    # Edwin 2026-08-24
    #
    def add_contrast_bolus_agent_to_dict(self, contrast_bolus_agent: str) -> None:
        """
        Adds a contrast bolus agent to the dictionary for statistics.
        """
        
        # Checks
        assert is_valid_string(contrast_bolus_agent)
        assert self.contrast_bolus_agent_dict is not None and isinstance(self.contrast_bolus_agent_dict, dict)

        if contrast_bolus_agent in self.contrast_bolus_agent_dict:
            self.contrast_bolus_agent_dict[contrast_bolus_agent] += 1
        else:
            self.contrast_bolus_agent_dict[contrast_bolus_agent] = 1

    #
    # Edwin 2026-09-24
    #
    def add_contrast_bolus_ingredient_to_dict(self, contrast_bolus_ingredient_term: str) -> None:
        """
        Adds a contrast bolus ingredient term to the dictionary for statistics.
        """
        
        # Checks
        assert is_valid_string(contrast_bolus_ingredient_term)
        assert self.contrast_bolus_ingredient_dict is not None and isinstance(self.contrast_bolus_ingredient_dict, dict)

        if contrast_bolus_ingredient_term in self.contrast_bolus_ingredient_dict:
            self.contrast_bolus_ingredient_dict[contrast_bolus_ingredient_term] += 1
        else:
            self.contrast_bolus_ingredient_dict[contrast_bolus_ingredient_term] = 1


    #
    # Edwin 2026-09-24
    #
    def add_contrast_bolus_agent_sequence_code_to_dict(self, coding_scheme_designator: str|None, code_value: str|None, code_meaning: str|None = None) -> None:

        # Checks
        assert coding_scheme_designator is None or is_valid_string(coding_scheme_designator)
        assert code_value is None or is_valid_string(code_value)
        assert code_meaning is None or is_valid_string(code_meaning)
        assert self.contrast_bolus_agent_sequence_codes_dict is not None and isinstance(self.contrast_bolus_agent_sequence_codes_dict, dict)

        key = (coding_scheme_designator, code_value, code_meaning)
        if key in self.contrast_bolus_agent_sequence_codes_dict:
            self.contrast_bolus_agent_sequence_codes_dict[key] += 1
        else:
            self.contrast_bolus_agent_sequence_codes_dict[key] = 1

    #
    # Edwin 2026-09-24
    #
    def add_unknown_contrast_bolus_agent_sequence_code_to_dict(self, coding_scheme_designator: str|None, code_value: str|None, code_meaning: str | None = None) -> None:
        """
        Adds an unknown contrast bolus agent sequence code to the dictionary for statistics.
        """
        
        # Checks
        assert coding_scheme_designator is None or is_valid_string(coding_scheme_designator)
        assert code_value is None or is_valid_string(code_value)
        assert code_meaning is None or is_valid_string(code_meaning)
        assert self.unknown_contrast_bolus_agent_sequence_codes_dict is not None and isinstance(self.unknown_contrast_bolus_agent_sequence_codes_dict, dict)

        key = (coding_scheme_designator, code_value, code_meaning)
        if key in self.unknown_contrast_bolus_agent_sequence_codes_dict:
            self.unknown_contrast_bolus_agent_sequence_codes_dict[key] += 1
        else:
            self.unknown_contrast_bolus_agent_sequence_codes_dict[key] = 1


    #
    # Edwin 2026-09-29
    #
    def add_contrast_bolus_administration_route_sequence_code_to_dict(self, coding_scheme_designator: str|None, code_value: str|None, code_meaning: str|None = None) -> None:

        # Checks
        assert coding_scheme_designator is None or is_valid_string(coding_scheme_designator)
        assert code_value is None or is_valid_string(code_value)
        assert code_meaning is None or is_valid_string(code_meaning)
        assert self.contrast_bolus_administration_route_sequence_codes_dict is not None and isinstance(self.contrast_bolus_administration_route_sequence_codes_dict, dict)

        key = (coding_scheme_designator, code_value, code_meaning)
        if key in self.contrast_bolus_administration_route_sequence_codes_dict:
            self.contrast_bolus_administration_route_sequence_codes_dict[key] += 1
        else:
            self.contrast_bolus_administration_route_sequence_codes_dict[key] = 1

    #
    # Edwin 2026-09-29
    #
    def add_unknown_contrast_bolus_administration_route_sequence_code_to_dict(self, coding_scheme_designator: str|None, code_value: str|None, code_meaning: str|None = None) -> None:

        # Checks
        assert coding_scheme_designator is None or is_valid_string(coding_scheme_designator)
        assert code_value is None or is_valid_string(code_value)
        assert code_meaning is None or is_valid_string(code_meaning)
        assert self.unknown_contrast_bolus_administration_route_sequence_codes_dict is not None and isinstance(self.unknown_contrast_bolus_administration_route_sequence_codes_dict, dict)

        key = (coding_scheme_designator, code_value, code_meaning)
        if key in self.unknown_contrast_bolus_administration_route_sequence_codes_dict:
            self.unknown_contrast_bolus_administration_route_sequence_codes_dict[key] += 1
        else:
            self.unknown_contrast_bolus_administration_route_sequence_codes_dict[key] = 1


    #
    # Edwin 2026-07-20
    #
    def increment_dicom_studies_processed_counter(self, value: int=1) -> None:
        """
        Increments the studies processed counter
        For statistics only
        """

        # Checks
        assert isinstance(value, int) and value>0

        # Increment number
        self.number_of_dicom_studies_processed += value
        self.total_number_of_dicom_studies_processed += value

    #
    # Edwin 2026-07-20
    #
    def increment_dicom_studies_skipped_counter(self, value: int=1) -> None:
        """
        Increments the studies skipped counter
        For statistics only
        """

        # Checks
        assert isinstance(value, int) and value>0

        # Increment number
        self.number_of_dicom_studies_skipped += value
        self.total_number_of_dicom_studies_skipped += value

    #
    # Edwin 2026-07-20
    #
    def increment_dicom_series_processed_counter(self, value: int=1) -> None:
        """
        Increments the series processed counter
        For statistics only
        """

        # Checks
        assert isinstance(value, int) and value>0

        # Increment number
        self.number_of_dicom_series_processed += value
        self.total_number_of_dicom_series_processed += value

    #
    # Edwin 2026-07-20
    #
    def increment_dicom_series_skipped_counter(self, value: int=1) -> None:
        """
        Increments the series skipped counter
        For statistics only
        """

        # Checks
        assert isinstance(value, int) and value>0

        # Increment number
        self.number_of_dicom_series_skipped += value
        self.total_number_of_dicom_series_skipped += value

    #
    # Edwin 2026-07-20
    #
    def increment_dicom_instances_processed_counter(self, value: int=1) -> None:
        """
        Increments the instances processed counter
        For statistics only
        """

        # Checks
        assert isinstance(value, int) and value>0

        # Increment number
        self.number_of_dicom_instances_processed += value
        self.total_number_of_dicom_instances_processed += value


    #
    # Edwin 2026-07-20
    #
    def increment_dicom_instances_skipped_counter(self, value: int=1) -> None:
        """
        Increments the instances skipped counter
        For statistics only
        """

        # Checks
        assert isinstance(value, int) and value>0

        # Increment number
        self.number_of_dicom_instances_skipped += value
        self.total_number_of_dicom_instances_skipped += value

    #
    # Edwin 2026-07-20
    #
    def increment_dicom_frames_processed_counter(self, value: int=1) -> None:
        """
        Increments the frames processed counter
        For statistics only
        """

        # Checks
        assert isinstance(value, int) and value>0

        # Increment number
        self.number_of_dicom_frames_processed += value
        self.total_number_of_dicom_frames_processed += value

    #
    # Edwin 2026-07-20
    # Not used
    def increment_sphn_imaging_frames_added_counter(self, value: int=1) -> None:
        """
        Increments the SPHN ImagingFrames added counter
        For statistics only
        """

        # Checks
        assert isinstance(value, int) and value>0

        # Increment number
        self.number_of_sphn_imaging_frames_stored += value
        self.total_number_of_sphn_imaging_frames_stored += value

    #
    # Edwin 2026-08-14
    #
    def increment_sphn_imaging_frames_added_to_sphn_imaging_series_counter(self, value: int=1) -> None:
        """
        Increments the SPHN ImagingFrames added to SPHN ImagingSeries counter
        For statistics only
        """

        # Checks
        assert isinstance(value, int) and value>0

        # Increment number
        self.number_of_sphn_imaging_frames_added_to_sphn_imaging_series += value

    #
    # Edwin 2026-08-15
    #
    def increment_sphn_imaging_series_added_to_sphn_imaging_procedure_counter(self, value: int=1) -> None:
        """
        Increments the SPHN ImagingSeries added to SPHN ImagingProcedure counter
        For statistics only
        """

        # Checks
        assert isinstance(value, int) and value>0

        # Increment number
        self.number_of_sphn_imaging_series_added_to_sphn_imaging_procedure += value


    #
    # Edwin 2026-08-04
    #
    def get_number_of_sphn_procedures_series_frames_stored(self) -> tuple[int,int,int]:
        """
        Returns the number of SPHN ImagingProcedures, ImagingSeries, and ImagingFrames stored.
        For statistics only
        """

        assert self.sphn_imaging_procedure_list is not None and isinstance(self.sphn_imaging_procedure_list, list)

        #n_procedures = len(self.sphn_imaging_procedure_list) 
        #n_series = sum(len(proc.has_imaging_series_list) if proc.has_imaging_series_list is not None else 0 for proc in self.sphn_imaging_procedure_list)
        #n_frames = sum(len(series.has_imaging_frame_list) if series.has_imaging_frame_list is not None else 0 for proc in self.sphn_imaging_procedure_list for series in proc.has_imaging_series_list if proc.has_imaging_series_list is not None)
        #return n_procedures, n_series, n_frames
    
        n_procedures = len(self.sphn_imaging_procedure_list)
        n_series = 0
        n_frames = 0
        for proc in self.sphn_imaging_procedure_list:
            if proc.has_imaging_series_list is not None:
                n_series += len(proc.has_imaging_series_list)
                for series in proc.has_imaging_series_list:
                    if series.has_imaging_frame_list is not None:
                        n_frames += len(series.has_imaging_frame_list)

        return n_procedures, n_series, n_frames
