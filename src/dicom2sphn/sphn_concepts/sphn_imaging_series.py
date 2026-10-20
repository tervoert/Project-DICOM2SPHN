"""
sphn_imaging_series.py: 
    Part of the example dicom2sphn package.
    It contains the SPHNImagingSeries class, which represents the SPHN ImagingSeries concept in the SPHN schema.
"""

from datetime import datetime

from pydantic import Field, ValidationInfo, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_administrative_case import SPHNAdministrativeCase
from .sphn_code import SPHNCode
from .sphn_concept import SPHNConcept
from .sphn_data_file import SPHNDataFile
from .sphn_imaging_device import SPHNImagingDevice
from .sphn_imaging_frame import SPHNImagingFrame
from .sphn_quantity import SPHNQuantity
from .sphn_source_system import SPHNSourceSystem
from .sphn_subject_pseudo_identifier import SPHNSubjectPseudoIdentifier


#
#
# The SPHN ImagingSeries class representing the SPHN ImagingSeries concept in the SPHN schema.
#
class SPHNImagingSeries(SPHNConcept):

    has_start_datetime: datetime|None=None                                  # (0:1) xsd:dateTime
    has_end_datetime: datetime|None=None                                    # (0:1) xsd:dateTime                    # Not in DICOM
    has_description: str|None=None                                          # (0:1) xsd:string
    has_protocol_name: str|None=None                                        # (0:1) xsd:string
    has_imaging_modality_code: SPHNCode|None=None                           # (0:1) SPHN Code or SPHN Terminology
    has_imaging_frame_list: list[SPHNImagingFrame]|None=None                # (0:n) SPHN ImagingFrame (list)
    has_number_of_frames: SPHNQuantity|None=None                            # (0:1) SPHN Quantity
    has_medical_device: SPHNImagingDevice|None=None                         # (0:1) SPHN ImagingDevice
    has_data_file_list: list[SPHNDataFile]|None=None                        # (0:n) SPHN DataFile (list)            # Not Implemented

    has_administrative_case: SPHNAdministrativeCase|None=None               # (0:1) SPHN AdministrativeCase         # Not Implemented
    has_subject_pseudo_identifier: SPHNSubjectPseudoIdentifier              # (1:1) SPHN Subject Pseudo Identifier
    has_source_system_list: list[SPHNSourceSystem]                          # (1:n) SPHN SourceSystem (list)

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())


    @field_validator('has_description','has_protocol_name', mode='after')
    @classmethod
    def validate_string_or_none(cls, value: str|None, info: ValidationInfo) -> str|None:
        if value is not None and not is_valid_string(value):
            raise ValueError(f"SPHN {info.field_name} value is not a valid string")
        return value  

    @field_validator('has_imaging_frame_list', mode='after')
    @classmethod
    def validate_imaging_frame_list(cls, value: list[SPHNImagingFrame]|None) -> list[SPHNImagingFrame]|None:
        if value is not None:
            if not isinstance(value, list) or len(value) == 0:
                raise ValueError("SPHN 'has_imaging_frame' list must be a non-empty list or None")
            if not all(isinstance(item, SPHNImagingFrame) for item in value):
                raise TypeError("One or more items in the SPHN 'has_imaging_frame' list are not SPHN ImagingFrame instances.")
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
    # Edwin 2026-08-05
    # (Not used)
    def add_sphn_imaging_frame(self, imaging_frame: SPHNImagingFrame) -> None:
        """ 
        Adds the imaging_frame to the list
        """
        # Checks
        assert isinstance(imaging_frame, SPHNImagingFrame)

        if self.has_imaging_frame_list is None:
            self.has_imaging_frame_list = [imaging_frame]
        else:
            if imaging_frame not in self.has_imaging_frame_list:
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
            if data_file not in self.has_data_file_list:
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

        if source_system not in self.has_source_system_list:
            self.has_source_system_list.append(source_system)


    #
    # Edwin 2026-08-05
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

        if self.has_data_file_list is not None and len(self.has_data_file_list)>0:
            json_dict_content[f"{SPHN.hasDataFile.n3(self.sphn_schema.namespace_manager())}"] = [data_file.get_json_dict(content, self.id) for data_file in self.has_data_file_list]

        if self.has_administrative_case is not None:
            json_dict_content[f"{SPHN.hasAdministrativeCase.n3(self.sphn_schema.namespace_manager())}"] = self.has_administrative_case.get_json_dict(content, self.id)

        if self.has_source_system_list is not None and len(self.has_source_system_list)>0:
            json_dict_content[f"{SPHN.hasSourceSystem.n3(self.sphn_schema.namespace_manager())}"] = [source_system.get_json_dict(content, self.id) for source_system in self.has_source_system_list]

        # subject = <prefix:classname>
        subject = f"{SPHN.ImagingSeries.n3(self.sphn_schema.namespace_manager())}"
        
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
    # Edwin 2026-10-19
    #
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
                    self.has_start_datetime, 
                    self.has_end_datetime, 
                    self.has_description,
                    self.has_protocol_name,
                    self.has_subject_pseudo_identifier,
                    self.has_imaging_modality_code,
                    self.has_number_of_frames,
                    self.has_medical_device,
                    self.has_administrative_case,
                    sorted(self.has_imaging_frame_list) if self.has_imaging_frame_list is not None else None,
                    sorted(self.has_data_file_list) if self.has_data_file_list is not None else None,
                    sorted(self.has_source_system_list) if self.has_source_system_list is not None else None
                ) == (
                    other.has_start_datetime, 
                    other.has_end_datetime,
                    other.has_description,
                    other.has_protocol_name,
                    other.has_subject_pseudo_identifier,
                    other.has_imaging_modality_code,
                    other.has_number_of_frames,
                    other.has_medical_device,
                    other.has_administrative_case,
                    sorted(other.has_imaging_frame_list) if other.has_imaging_frame_list is not None else None,
                    sorted(other.has_data_file_list) if other.has_data_file_list is not None else None,
                    sorted(other.has_source_system_list) if other.has_source_system_list is not None else None
                )


    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------

