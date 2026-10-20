"""
sphn_data_file.py: 
    Part of the example dicom2sphn package.
    It contains the SPHNDataFile class, which represents the SPHN DataFile concept in the SPHN schema.
"""

from datetime import datetime
from typing import Self

from pydantic import Field, ValidationInfo, field_validator, model_validator

from ..sphn_schema_graph import SPHN, SPHN_IND, SPHNSchemaGraph
from ..tools import (
    generate_id,
    is_clean_string,
    is_valid_string,
)
from .sphn_code import SPHNCode
from .sphn_concept import SPHNConcept
from .sphn_hash import SPHNHash
from .sphn_source_system import SPHNSourceSystem
from .sphn_subject_pseudo_identifier import SPHNSubjectPseudoIdentifier


#
# The SPHN DataFile class representing the SPHN DataFile concept in the SPHN schema.
#
class SPHNDataFile(SPHNConcept):

    has_name: str|None=None                                                             # (0:1) xsd:string 
    has_encoding: str|None=None                                                         # (0:1) SPHN Data_File_Encoding ValueSet member
    has_uniform_resource_identifier: str|None=None                                      # (0:1) xsd:string
    has_creation_datetime: datetime|None=None                                          # (0:1) xsd:dateTime
    has_format_code: SPHNCode|None=None                                                 # (0:1) SPHN Code
    has_hash: SPHNHash|None=None                                                        # (0:1) SPHN Hash
    has_subject_pseudo_identifier_list: list[SPHNSubjectPseudoIdentifier]|None=None     # (0:n) SPHN SubjectPseudoIdentifier (list)
    has_source_system_list: list[SPHNSourceSystem]                                      # (1:n) SPHN SourceSystem (list)

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())


    @field_validator('has_name', 'has_uniform_resource_identifier', mode='after')
    @classmethod
    def validate_string_or_none(cls, value: str|None, info: ValidationInfo) -> str|None:
        if value is not None and not is_valid_string(value):
            raise ValueError(f'SPHN {info.field_name} value is not a valid string or None')
        return value  

    @field_validator('has_subject_pseudo_identifier_list', mode='after')
    @classmethod
    def validate_subject_pseudo_identifier_list(cls, value: list[SPHNSubjectPseudoIdentifier]|None) -> list[SPHNSubjectPseudoIdentifier]|None:
        if value is not None:
            if len(value) == 0:
                raise ValueError('SPHN has_subject_pseudo_identifier_list must be a non-empty list or None')
            if not all(isinstance(item, SPHNSubjectPseudoIdentifier) for item in value):
                raise TypeError('One or more items in has_subject_pseudo_identifier_list are not SPHNSubjectPseudoIdentifier instances.')
        return value

    @field_validator('has_source_system_list', mode='after')  
    @classmethod
    def validate_source_system_list(cls, value: list[SPHNSourceSystem]) -> list[SPHNSourceSystem]:
        if len(value) == 0:
            raise ValueError("SPHN 'has_source_system' list must be a non-empty list.")
        if not all(isinstance(item, SPHNSourceSystem) for item in value):
            raise TypeError("One or more items in the SPHN 'has_source_system' list are not SPHN SourceSystem instances.")
        return value

    @model_validator(mode='after')
    def validate_sphn_data_file_encoding_value_set_member(self) -> Self:
        if self.has_encoding is not None:
            if not is_clean_string(self.has_encoding):
                raise ValueError(f"SPHN has_encoding value '{self.has_encoding}' is not a valid clean string")
            if not self.sphn_schema.is_sphn_data_file_encoding_value_set_member(self.has_encoding):
                raise ValueError(f"SPHN has_encoding value '{self.has_encoding}' is not a SPHN DataFile encoding value set member")
        return self

    # ----------------------------------------------------------------------------------------------------------
    # Public functions
    # ----------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-05
    #
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

        if self.has_encoding is not None:
            json_dict_content[f"{SPHN.hasEncoding.n3(self.sphn_schema.namespace_manager())}"] = {
                "iri": SPHN_IND + self.has_encoding
            }

        if self.has_creation_datetime is not None:
            json_dict_content[f"{SPHN.hasCreationDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_creation_datetime.isoformat(timespec='milliseconds')

        if self.has_uniform_resource_identifier is not None:
            json_dict_content[f"{SPHN.hasUniformResourceIdentifier.n3(self.sphn_schema.namespace_manager())}"] = self.has_uniform_resource_identifier

        if self.has_name is not None:
            json_dict_content[f"{SPHN.hasName.n3(self.sphn_schema.namespace_manager())}"] = self.has_name

        if self.has_format_code is not None:
            json_dict_content[f"{SPHN.hasFormatCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_format_code.get_json_dict(content, self.id)

        if self.has_hash is not None:
            json_dict_content[f"{SPHN.hasHash.n3(self.sphn_schema.namespace_manager())}"] = self.has_hash.get_json_dict(content, self.id)

        if self.has_source_system_list is not None and len(self.has_source_system_list)>0:
            json_dict_content[f"{SPHN.hasSourceSystem.n3(self.sphn_schema.namespace_manager())}"] = [source_system.get_json_dict(content, self.id) for source_system in self.has_source_system_list]

        # subject = <prefix:classname>
        subject = f"{SPHN.DataFile.n3(self.sphn_schema.namespace_manager())}"
        
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
                    self.has_name, 
                    self.has_encoding, 
                    self.has_uniform_resource_identifier, 
                    self.has_creation_datetime, 
                    self.has_format_code, 
                    self.has_hash, 
                    sorted(self.has_subject_pseudo_identifier_list) if self.has_subject_pseudo_identifier_list is not None else None, 
                    sorted(self.has_source_system_list) if self.has_source_system_list is not None else None
                ) == (
                    other.has_name, 
                    other.has_encoding, 
                    other.has_uniform_resource_identifier, 
                    other.has_creation_datetime, 
                    other.has_format_code, 
                    other.has_hash, 
                    sorted(other.has_subject_pseudo_identifier_list) if other.has_subject_pseudo_identifier_list is not None else None, 
                    sorted(other.has_source_system_list) if other.has_source_system_list is not None else None
                )

    # ----------------------------------------------------------------------------------------------------------
    # Private functions
    # ----------------------------------------------------------------------------------------------------------
