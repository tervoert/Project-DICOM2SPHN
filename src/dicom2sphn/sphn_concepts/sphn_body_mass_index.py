"""
sphn_body_mass_index.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNBodyMassIndex class, which represents the SPHN Body Mass Index concept in the SPHN schema.
"""
from datetime import datetime

from pydantic import Field, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import already_in_list, are_similar_lists, generate_id, is_valid_string
from .sphn_administrative_case import SPHNAdministrativeCase
from .sphn_concept import SPHNConcept
from .sphn_quantity import SPHNQuantity
from .sphn_source_system import SPHNSourceSystem
from .sphn_subject_pseudo_identifier import SPHNSubjectPseudoIdentifier


#
# The SPHN Body Mass Index class representing the SPHN Body Mass Index concept in the SPHN schema.
#
class SPHNBodyMassIndex(SPHNConcept):

    has_quantity: SPHNQuantity                                     # (1:1) SPHN Quantity
    has_subject_pseudo_identifier: SPHNSubjectPseudoIdentifier     # (1:1) SPHN SubjectPseudoIdentifier
    has_source_system_list: list[SPHNSourceSystem]                 # (1:n) SPHN SourceSystem (list)
    has_determination_date_time: datetime|None=None                # (0:1) xsd:dateTime
    has_administrative_case: SPHNAdministrativeCase|None=None      # (0:1) SPHN SPHNAdministrativeCase

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())


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
    #
    def add_sphn_source_system(self, source_system: SPHNSourceSystem) -> None:
        """ 
        Adds the source_system to the list
        """
        # Checks
        assert isinstance(source_system, SPHNSourceSystem)

        if not already_in_list(source_system, self.has_source_system_list):
            self.has_source_system_list.append(source_system)
    
    #
    # Edwin 2026-08-05
    #
    # Core Concept
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

        if self.has_quantity is not None:
            json_dict_content[f"{SPHN.hasQuantity.n3(self.sphn_schema.namespace_manager())}"] = self.has_quantity.get_json_dict(content, self.id)

        if self.has_determination_date_time is not None:
            json_dict_content[f"{SPHN.hasDeterminationDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_determination_date_time.isoformat(timespec='milliseconds')

        if self.has_administrative_case is not None:
            json_dict_content[f"{SPHN.hasAdministrativeCase.n3(self.sphn_schema.namespace_manager())}"] = self.has_administrative_case.get_json_dict(content, self.id)

        if self.has_source_system_list is not None and len(self.has_source_system_list)>0:
            json_dict_content[f"{SPHN.hasSourceSystem.n3(self.sphn_schema.namespace_manager())}"] = [source_system.get_json_dict(content, self.id) for source_system in self.has_source_system_list]

        # subject = <prefix:classname>
        subject = f"{SPHN.BodyMassIndex.n3(self.sphn_schema.namespace_manager())}"
        
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
    def is_similar(self, other) -> bool :
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_determination_date_time == other.has_determination_date_time \
            and self.has_quantity.is_similar(other.has_quantity) \
            and self.has_subject_pseudo_identifier.is_similar(other.has_subject_pseudo_identifier) \
            and ((self.has_administrative_case is None and other.has_administrative_case is None) \
                 or (self.has_administrative_case is not None and other.has_administrative_case is not None \
                     and self.has_administrative_case.is_similar(other.has_administrative_case))) \
            and are_similar_lists(self.has_source_system_list, other.has_source_system_list)


    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
    
