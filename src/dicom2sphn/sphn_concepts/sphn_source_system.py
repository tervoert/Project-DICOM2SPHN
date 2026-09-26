"""
sphn_source_system.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNSourceSystem class, which represents the SPHN SourceSystem concept in the SPHN schema.
"""

from typing import Self

from pydantic import Field, field_validator, model_validator

from ..sphn_schema_graph import SPHN, SPHN_IND, SPHNSchemaGraph
from ..tools import generate_id, is_clean_string, is_valid_string
from .sphn_concept import SPHNConcept
from .sphn_healthcare_primary_information_system import (
    SPHNHealthcarePrimaryInformationSystem,
)


#
# The SPHN SourceSystem class representing the SPHN SourceSystem concept in the SPHN schema.
#
class SPHNSourceSystem(SPHNConcept):

    has_name: str|None=None                                 # (0:1) xsd:string
    has_purpose: str|None=None                              # (0:1) SPHN SourceSystem_purpose valueset member
    has_category: str|None=None                             # (0:1) SPHN SourceSystem_category valueset member
    has_primary_system: \
        SPHNHealthcarePrimaryInformationSystem|None=None    # (0:1) SPHN HealthcarePrimaryInformationSystem

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())


    @field_validator('has_name', mode='after')  
    @classmethod
    def validate_name(cls, value: str|None) -> str|None:
        if value is not None and not is_valid_string(value):
            raise ValueError(f"SPHN 'has_name' value '{value}' is not a valid string")
        return value  

    @model_validator(mode='after')
    def validate_sphn_source_system_purpose_category_value_set_member(self) -> Self:
        if self.has_purpose is not None:
            if not is_clean_string(self.has_purpose):
                raise ValueError(f"SPHN 'has_purpose' value '{self.has_purpose}' is not a valid clean string")
            if not self.sphn_schema.is_sphn_source_system_purpose_value_set_member(self.has_purpose):
                raise ValueError(f"SPHN 'has_purpose' value '{self.has_purpose}' is not a SPHN SourceSystem purpose value set member")
        if self.has_category is not None:
            if not is_clean_string(self.has_category):
                raise ValueError(f"SPHN 'has_category' value '{self.has_category}' is not a valid clean string")
            if not self.sphn_schema.is_sphn_source_system_category_value_set_member(self.has_category):
                raise ValueError(f"SPHN 'has_category' value '{self.has_category}' is not a SPHN SourceSystem category value set member")
        return self

    # ----------------------------------------------------------------------------------------------------------
    # Public functions
    # ----------------------------------------------------------------------------------------------------------

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

        if self.has_name is not None:
            json_dict_content[f"{SPHN.hasName.n3(self.sphn_schema.namespace_manager())}"] = self.has_name

        if self.has_purpose is not None:
            json_dict_content[f"{SPHN.hasPurpose.n3(self.sphn_schema.namespace_manager())}"] = {
                "iri": SPHN_IND + self.has_purpose
            }

        if self.has_category is not None:
            json_dict_content[f"{SPHN.hasCategory.n3(self.sphn_schema.namespace_manager())}"] = {
                "iri": SPHN_IND + self.has_category
            }

        if self.has_primary_system is not None:
            json_dict_content[f"{SPHN.hasPrimarySystem.n3(self.sphn_schema.namespace_manager())}"] = self.has_primary_system.get_json_dict(content, self.id)

        # subject = <prefix:classname>
        subject = f"{SPHN.SourceSystem.n3(self.sphn_schema.namespace_manager())}"
        
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
    # Edwin 2026-08-05
    #
    def is_similar(self, other: SPHNConcept) -> bool:
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_name == other.has_name \
            and self.has_purpose == other.has_purpose \
            and self.has_category == other.has_category \
            and ((self.has_primary_system is None and other.has_primary_system is None) \
                 or (self.has_primary_system is not None and other.has_primary_system is not None \
                    and self.has_primary_system.is_similar(other.has_primary_system)))
    
    # ----------------------------------------------------------------------------------------------------------
    # Private functions
    # ----------------------------------------------------------------------------------------------------------
