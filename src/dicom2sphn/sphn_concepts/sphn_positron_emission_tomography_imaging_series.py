"""
sphn_positron_emission_tomography_imaging_series.py:
    Part of the example dicom2sphn package.
    It contains the SPHNPositronEmissionTomographyImagingSeries class, which represents the SPHN Positron Emission Tomography Imaging Series concept in the SPHN schema.
"""

from datetime import datetime

from pydantic import Field, ValidationInfo, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import already_in_list, are_similar_lists, generate_id, is_valid_string
from .sphn_administrative_case import SPHNAdministrativeCase
from .sphn_body_position import SPHNBodyPosition
from .sphn_code import SPHNCode
from .sphn_data_file import SPHNDataFile
from .sphn_imaging_device import SPHNImagingDevice
from .sphn_imaging_series import SPHNImagingSeries
from .sphn_positron_emission_tomography_imaging_frame import (
    SPHNPositronEmissionTomographyImagingFrame,
)
from .sphn_quantity import SPHNQuantity
from .sphn_source_system import SPHNSourceSystem
from .sphn_subject_pseudo_identifier import SPHNSubjectPseudoIdentifier


#
# The SPHNPositronEmissionTomographyImagingSeries class representing the SPHN Positron Emission Tomography Imaging Series concept in the SPHN schema.
#
class SPHNPositronEmissionTomographyImagingSeries(SPHNImagingSeries):

    has_start_datetime: datetime|None=None                                              # (0:1) xsd:dateTime
    has_end_datetime: datetime|None=None                                                # (0:1) xsd:dateTime                    # Not in DICOM
    has_description: str|None=None                                                      # (0:1) xsd:string
    has_protocol_name: str|None=None                                                    # (0:1) xsd:string
    has_imaging_modality_code: SPHNCode|None=None                                       # (0:1) SPHN Code or SPHN Terminology
    has_imaging_frame_list: list[SPHNPositronEmissionTomographyImagingFrame]|None=None  # (0:n) SPHN Positron Emission Tomography Imaging Frame (list)
    has_number_of_frames: SPHNQuantity|None=None                                        # (0:1) SPHN Quantity
    has_medical_device: SPHNImagingDevice|None=None                                     # (0:1) SPHN ImagingDevice
    has_data_file_list: list[SPHNDataFile]|None=None                                    # (0:n) SPHN DataFile (list)            # Not Implemented

    has_body_position_list: list[SPHNBodyPosition]|None=None                            # (0:n) SPHN BodyPosition (list)

    has_administrative_case: SPHNAdministrativeCase|None=None                           # (0:1) SPHN AdministrativeCase         # Not Implemented
    has_subject_pseudo_identifier: SPHNSubjectPseudoIdentifier                          # (1:1) SPHN Subject Pseudo Identifier
    has_source_system_list: list[SPHNSourceSystem]                                      # (1:n) SPHN SourceSystem (list)

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())


    @field_validator('has_description','has_protocol_name', mode='after')
    @classmethod
    def validate_string_or_none(cls, value: str|None, info: ValidationInfo) -> str|None:
        if value is not None and not is_valid_string(value):
            raise ValueError(f"SPHN '{info.field_name}' value is not a valid string")
        return value  

    @field_validator('has_imaging_frame_list', mode='after')
    @classmethod
    def validate_imaging_frame_list(cls, value: list[SPHNPositronEmissionTomographyImagingFrame]|None) -> list[SPHNPositronEmissionTomographyImagingFrame]|None:
        if value is not None:
            if not isinstance(value, list) or len(value) == 0:
                raise ValueError("SPHN 'has_imaging_frame' list must be a non-empty list or None")
            if not all(isinstance(item, SPHNPositronEmissionTomographyImagingFrame) for item in value):
                raise TypeError("One or more items in the SPHN 'has_imaging_frame' list are not SPHN PositronEmissionTomographyImagingFrame instances.")
        return value

    @field_validator('has_data_file_list', mode='after')
    @classmethod
    def validate_data_file_list(cls, value: list[SPHNDataFile]|None) -> list[SPHNDataFile]|None:
        if value is not None:
            if len(value) == 0:
                raise ValueError("SPHN 'has_data_file' list must be a non-empty list or None")
            if not all(isinstance(item, SPHNDataFile) for item in value):
                raise TypeError("One or more items in the SPHN 'has_data_file' list are not SPHN DataFile instances.")
        return value

    @field_validator('has_source_system_list', mode='after')  
    @classmethod
    def validate_source_system_list(cls, value: list[SPHNSourceSystem]) -> list[SPHNSourceSystem]:
        if len(value) == 0:
            raise ValueError("SPHN 'has_source_system' list must be a non-empty list.")
        if not all(isinstance(item, SPHNSourceSystem) for item in value):
            raise TypeError("One or more items in the SPHN 'has_source_system' list are not SPHN SourceSystem instances.")
        return value

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-13
    # (Not used)
    def add_sphn_imaging_frame(self, imaging_frame: SPHNPositronEmissionTomographyImagingFrame) -> None:
        """ 
        Adds the imaging_frame to the list
        """
        # Checks
        assert isinstance(imaging_frame, SPHNPositronEmissionTomographyImagingFrame)

        if self.has_imaging_frame_list is None:
            self.has_imaging_frame_list = [imaging_frame]
        else:
            if not already_in_list(imaging_frame, self.has_imaging_frame_list):
                self.has_imaging_frame_list.append(imaging_frame)


    #
    # Edwin 2026-08-05
    # (Not used)
    def add_sphn_data_file(self, data_file: SPHNDataFile) -> None:
        """ 
        Adds the data_file to the list
        """
        # Checks
        assert isinstance(data_file, SPHNDataFile)

        if self.has_data_file_list is None:
            self.has_data_file_list = [data_file]
        else:
            if not already_in_list(data_file, self.has_data_file_list):
                self.has_data_file_list.append(data_file)


    #
    # Edwin 2026-08-05
    # (Not used)
    def add_sphn_source_system(self, source_system: SPHNSourceSystem) -> None:
        """ 
        Adds the source_system to the list
        """
        # Checks
        assert isinstance(source_system, SPHNSourceSystem)

        if not already_in_list(source_system, self.has_source_system_list):
            self.has_source_system_list.append(source_system)


    #
    # Edwin 2026-08-13
    #
    # It is a Core Concept
    def get_json_dict(self, content: dict, source_concept_id: str|None=None) -> dict:
        """ 
        Gets the dict for json output
        """
        # Checks
        assert isinstance(content, dict)
        assert source_concept_id is None or is_valid_string(source_concept_id)        
        
        # Part 1: Create the JSON description of the reference to the instance
        
        json_dict_ref = {
            "id": f"{self.id}"
        }

        # Part 2: Create the JSON description of the instance for the 'content'

        json_dict_content = {
            "id": f"{self.id}"
        }

        if self.has_start_datetime is not None:
            json_dict_content[f"{SPHN.hasStartDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_start_datetime.isoformat(timespec='milliseconds')

        if self.has_end_datetime is not None:
            json_dict_content[f"{SPHN.hasEndDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_end_datetime.isoformat(timespec='milliseconds')

        if self.has_description is not None:
            json_dict_content[f"{SPHN.hasDescription.n3(self.sphn_schema.namespace_manager())}"] = self.has_description

        if self.has_protocol_name is not None:
            json_dict_content[f"{SPHN.hasProtocolName.n3(self.sphn_schema.namespace_manager())}"] = self.has_protocol_name

        if self.has_imaging_modality_code is not None:
            json_dict_content[f"{SPHN.hasImagingModalityCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_imaging_modality_code.get_json_dict(content, self.id)

        if self.has_imaging_frame_list is not None and len(self.has_imaging_frame_list)>0:
            json_dict_content[f"{SPHN.hasImagingFrame.n3(self.sphn_schema.namespace_manager())}"] = [imaging_frame.get_json_dict(content, self.id) for imaging_frame in self.has_imaging_frame_list]

        if self.has_number_of_frames is not None:
            json_dict_content[f"{SPHN.hasNumberOfFrames.n3(self.sphn_schema.namespace_manager())}"] = self.has_number_of_frames.get_json_dict(content, self.id)

        if self.has_medical_device is not None:
            json_dict_content[f"{SPHN.hasMedicalDevice.n3(self.sphn_schema.namespace_manager())}"] = self.has_medical_device.get_json_dict(content, self.id)

        if self.has_body_position_list is not None and len(self.has_body_position_list)>0:
            json_dict_content[f"{SPHN.hasBodyPosition.n3(self.sphn_schema.namespace_manager())}"] = [body_position.get_json_dict(content, self.id) for body_position in self.has_body_position_list]

        if self.has_data_file_list is not None and len(self.has_data_file_list)>0:
            json_dict_content[f"{SPHN.hasDataFile.n3(self.sphn_schema.namespace_manager())}"] = [data_file.get_json_dict(content, self.id) for data_file in self.has_data_file_list]

        if self.has_administrative_case is not None:
            json_dict_content[f"{SPHN.hasAdministrativeCase.n3(self.sphn_schema.namespace_manager())}"] = self.has_administrative_case.get_json_dict(content, self.id)

        if self.has_source_system_list is not None and len(self.has_source_system_list)>0:
            json_dict_content[f"{SPHN.hasSourceSystem.n3(self.sphn_schema.namespace_manager())}"] = [source_system.get_json_dict(content, self.id) for source_system in self.has_source_system_list]

        # subject = <prefix:classname>
        subject = f"{SPHN.PositronEmissionTomographyImagingSeries.n3(self.sphn_schema.namespace_manager())}"
        
        # Check if 'subject'-list already exists in the JSON 'content'
        if subject in content:
            # 'Subject'-list does exist in the JSON 'content'
            # Check if instance JSON description is already in the 'subject'-list in the JSON 'content'
            subject_list = content[subject]
            for item_dict in subject_list:
                if "id" in item_dict and item_dict["id"] == self.id:
                    # Already in the 'subject'-list in 'content', we don't add it
                    break
            else:
                # Not in the 'subject'-list in 'content', so we can add it
                content[subject].append(json_dict_content)

        else:
            # 'Subject'-list does not exist in the JSON 'content'
            content[subject] = [json_dict_content]

        # Return the JSON description of the reference to the instance
        return json_dict_ref


    #
    # Edwin 2026-08-13
    #
    def is_similar(self, other, rel_tol: float=1e-4, abs_tol: float=1e-9) -> bool:
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_start_datetime == other.has_start_datetime \
            and self.has_end_datetime == other.has_end_datetime \
            and self.has_description == other.has_description \
            and self.has_protocol_name == other.has_protocol_name \
            and self.has_subject_pseudo_identifier.is_similar(other.has_subject_pseudo_identifier) \
            and ((self.has_imaging_modality_code is None and other.has_imaging_modality_code is None) \
                 or (self.has_imaging_modality_code is not None and other.has_imaging_modality_code is not None \
                    and self.has_imaging_modality_code.is_similar(other.has_imaging_modality_code))) \
            and ((self.has_number_of_frames is None and other.has_number_of_frames is None) \
                 or (self.has_number_of_frames is not None and other.has_number_of_frames is not None \
                    and self.has_number_of_frames.is_similar(other.has_number_of_frames, rel_tol=rel_tol, abs_tol=abs_tol))) \
            and ((self.has_medical_device is None and other.has_medical_device is None) \
                 or (self.has_medical_device is not None and other.has_medical_device is not None \
                    and self.has_medical_device.is_similar(other.has_medical_device))) \
            and ((self.has_administrative_case is None and other.has_administrative_case is None) \
                 or (self.has_administrative_case is not None and other.has_administrative_case is not None \
                    and self.has_administrative_case.is_similar(other.has_administrative_case))) \
            and ((self.has_imaging_frame_list is None and other.has_imaging_frame_list is None) \
                 or (self.has_imaging_frame_list is not None and other.has_imaging_frame_list is not None \
                    and are_similar_lists(self.has_imaging_frame_list, other.has_imaging_frame_list))) \
            and ((self.has_body_position_list is None and other.has_body_position_list is None) \
                 or (self.has_body_position_list is not None and other.has_body_position_list is not None \
                    and are_similar_lists(self.has_body_position_list, other.has_body_position_list))) \
            and ((self.has_data_file_list is None and other.has_data_file_list is None) \
                 or (self.has_data_file_list is not None and other.has_data_file_list is not None \
                    and are_similar_lists(self.has_data_file_list, other.has_data_file_list))) \
            and are_similar_lists(self.has_source_system_list, other.has_source_system_list)

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------

