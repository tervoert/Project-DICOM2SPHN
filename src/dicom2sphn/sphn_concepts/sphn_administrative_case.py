"""
sphn_administrative_case.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNAdministrativeCase class, which represents the SPHN Administrative Case concept in the SPHN schema.
"""

from pydantic import Field, ValidationInfo, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import already_in_list, are_similar_lists, generate_id, is_valid_string
from .sphn_admission import SPHNAdmission
from .sphn_care_handling import SPHNCareHandling
from .sphn_concept import SPHNConcept
from .sphn_discharge import SPHNDischarge
from .sphn_source_system import SPHNSourceSystem
from .sphn_subject_pseudo_identifier import SPHNSubjectPseudoIdentifier


#
# The SPHN Administrative Case class representing the SPHN Administrative Case concept in the SPHN schema.
#
class SPHNAdministrativeCase(SPHNConcept):

    has_admission: SPHNAdmission                                   # (1:1) SPHN Admission
    has_subject_pseudo_identifier: SPHNSubjectPseudoIdentifier     # (1:1) SPHN SubjectPseudoIdentifier
    has_source_system_list: list[SPHNSourceSystem]                 # (1:n) SPHN SourceSystem (list)
    has_identifier: str|None=None                                  # (0:1) xsd:string
    has_discharge: SPHNDischarge|None=None                         # (0:1) SPHN Discharge
    has_care_handling: SPHNCareHandling|None=None                  # (0:1) SPHN CareHandling

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


    @field_validator('has_identifier', mode='after')  
    @classmethod
    def validate_identifier(cls, value: str, info: ValidationInfo) -> str:
        if value is not None and not is_valid_string(value):
            raise ValueError(f'SPHN {info.field_name} value is not a valid string')
        return value

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-05
    #
    # It is a Core Concept
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

        if self.has_identifier is not None:
            json_dict_content[f"{SPHN.hasIdentifier.n3(self.sphn_schema.namespace_manager())}"] = self.has_identifier

        if self.has_admission is not None:
            json_dict_content[f"{SPHN.hasAdmission.n3(self.sphn_schema.namespace_manager())}"] = self.has_admission.get_json_dict(content, self.id)

        if self.has_discharge is not None:
            json_dict_content[f"{SPHN.hasDischarge.n3(self.sphn_schema.namespace_manager())}"] = self.has_discharge.get_json_dict(content, self.id)

        if self.has_care_handling is not None:
            json_dict_content[f"{SPHN.hasCareHandling.n3(self.sphn_schema.namespace_manager())}"] = self.has_care_handling.get_json_dict(content, self.id)

        if self.has_source_system_list is not None and len(self.has_source_system_list)>0:
            json_dict_content[f"{SPHN.hasSourceSystem.n3(self.sphn_schema.namespace_manager())}"] = [source_system.get_json_dict(content, self.id) for source_system in self.has_source_system_list]

        # subject = <prefix:classname>
        subject = f"{SPHN.AdministrativeCase.n3(self.sphn_schema.namespace_manager())}"
        
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
            and self.has_identifier == other.has_identifier \
            and self.has_admission.is_similar(other.has_admission) \
            and self.has_subject_pseudo_identifier.is_similar(other.has_subject_pseudo_identifier) \
            and ((self.has_discharge is None and other.has_discharge is None) \
                or (self.has_discharge is not None and other.has_discharge is not None \
                    and self.has_discharge.is_similar(other.has_discharge))) \
            and ((self.has_care_handling is None and other.has_care_handling is None) \
                or (self.has_care_handling is not None and other.has_care_handling is not None \
                    and self.has_care_handling.is_similar(other.has_care_handling))) \
            and are_similar_lists(self.has_source_system_list, other.has_source_system_list)    

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
