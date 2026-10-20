"""
sphn_radiopharmaceutical_administration_event.py:
    Part of the example dicom2sphn package. 
    It contains the SPHNRadiopharmaceuticalAdministrationEvent class, which represents the SPHN Radiopharmaceutical Administration Event concept in the SPHN schema.
"""

from datetime import datetime

from pydantic import Field, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_administrative_case import SPHNAdministrativeCase
from .sphn_code import SPHNCode
from .sphn_drug_administration_event import SPHNDrugAdministrationEvent
from .sphn_quantity import SPHNQuantity
from .sphn_radiopharmaceutical import SPHNRadiopharmaceutical
from .sphn_source_system import SPHNSourceSystem
from .sphn_subject_pseudo_identifier import SPHNSubjectPseudoIdentifier
from .sphn_time_pattern import SPHNTimePattern


#
# The SPHN Radiopharmaceutical Administration Event class representing the SPHN Radiopharmaceutical Administration Event concept in the SPHN schema.
#
class SPHNRadiopharmaceuticalAdministrationEvent(SPHNDrugAdministrationEvent):

    has_start_datetime: datetime                                       # (1:1) xsd:dateTime
    has_end_datetime: datetime|None=None                               # (0:1) xsd:dateTime
    has_drug: SPHNRadiopharmaceutical                                   # (1:1) SPHN Radiopharmaceutical
    has_administration_route_code: SPHNCode|None=None                   # (0:1) SPHN Code
    has_reason_to_stop_code: SPHNCode|None=None                         # (0:1) SPHN Code
    has_duration: SPHNQuantity|None=None                                # (0:1) SPHN Quantity
    has_time_pattern: SPHNTimePattern|None=None                         # (0:1) SPHN Time Pattern

    has_subject_pseudo_identifier: SPHNSubjectPseudoIdentifier          # (1:1) SPHN Subject Pseudo Identifier
    has_administrative_case: SPHNAdministrativeCase|None=None           # (0:1) SPHN Administrative Case
    has_source_system_list: list[SPHNSourceSystem]                      # (1:n) SPHN SourceSystem (list)
    
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
    # Edwin 2026-08-013
    #
    #  It is a Core Concept
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

        if self.has_duration is not None:
            json_dict_content[f"{SPHN.hasDuration.n3(self.sphn_schema.namespace_manager())}"] = self.has_duration.get_json_dict(content, self.id)

        if self.has_time_pattern is not None:
            json_dict_content[f"{SPHN.hasTimePattern.n3(self.sphn_schema.namespace_manager())}"] = self.has_time_pattern.get_json_dict(content, self.id)

        if self.has_drug is not None:
            json_dict_content[f"{SPHN.hasDrug.n3(self.sphn_schema.namespace_manager())}"] = self.has_drug.get_json_dict(content, self.id)

        if self.has_administration_route_code is not None:
            json_dict_content[f"{SPHN.hasAdministrationRouteCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_administration_route_code.get_json_dict(content, self.id)

        if self.has_reason_to_stop_code is not None:
            json_dict_content[f"{SPHN.hasReasonToStopCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_reason_to_stop_code.get_json_dict(content, self.id)

        if self.has_administrative_case is not None:
            json_dict_content[f"{SPHN.hasAdministrativeCase.n3(self.sphn_schema.namespace_manager())}"] = self.has_administrative_case.get_json_dict(content, self.id)

        if self.has_source_system_list is not None and len(self.has_source_system_list)>0:
            json_dict_content[f"{SPHN.hasSourceSystem.n3(self.sphn_schema.namespace_manager())}"] = [source_system.get_json_dict(content, self.id) for source_system in self.has_source_system_list]

        # subject = <prefix:classname>
        subject = f"{SPHN.RadiopharmaceuticalAdministrationEvent.n3(self.sphn_schema.namespace_manager())}"
        
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
                    self.has_drug, 
                    self.has_administration_route_code, 
                    self.has_reason_to_stop_code, 
                    self.has_duration, 
                    self.has_time_pattern, 
                    self.has_subject_pseudo_identifier, 
                    self.has_administrative_case, 
                    sorted(self.has_source_system_list) if self.has_source_system_list is not None else None
                ) == (
                    other.has_start_datetime, 
                    other.has_end_datetime, 
                    other.has_drug, 
                    other.has_administration_route_code, 
                    other.has_reason_to_stop_code, 
                    other.has_duration, 
                    other.has_time_pattern, 
                    other.has_subject_pseudo_identifier, 
                    other.has_administrative_case, 
                    sorted(other.has_source_system_list) if other.has_source_system_list is not None else None
                )



    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
