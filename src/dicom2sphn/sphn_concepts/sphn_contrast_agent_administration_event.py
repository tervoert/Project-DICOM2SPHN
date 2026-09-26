"""
sphn_contrast_agent_administration_event.py:
    Part of the example dicom2sphn package. 
    It contains the SPHNContrastAgentAdministrationEvent class, which represents the SPHN Contrast Agent Administration Event concept in the SPHN schema.
"""

from datetime import datetime

from pydantic import Field, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import already_in_list, are_similar_lists, generate_id, is_valid_string
from .sphn_administrative_case import SPHNAdministrativeCase
from .sphn_code import SPHNCode
from .sphn_contrast_agent import SPHNContrastAgent
from .sphn_drug_administration_event import SPHNDrugAdministrationEvent
from .sphn_flow_profile_interval import SPHNFlowProfileInterval
from .sphn_quantity import SPHNQuantity
from .sphn_source_system import SPHNSourceSystem
from .sphn_subject_pseudo_identifier import SPHNSubjectPseudoIdentifier
from .sphn_time_pattern import SPHNTimePattern


#
# The SPHNContrastAgentAdministrationEvent class representing the SPHN Contrast Agent Administration Event concept in the SPHN schema.
#
class SPHNContrastAgentAdministrationEvent(SPHNDrugAdministrationEvent):

    has_start_date_time: datetime                                        # (1:1) xsd:dateTime
    has_end_date_time: datetime|None=None                                # (0:1) xsd:dateTime
    has_drug: SPHNContrastAgent                                         # (1:1) SPHN Contrast Agent
    has_administration_route_code: SPHNCode|None=None                   # (0:1) SPHN Code
    has_reason_to_stop_code: SPHNCode|None=None                         # (0:1) SPHN Code
    has_duration: SPHNQuantity|None=None                                # (0:1) SPHN Quantity
    has_time_pattern: SPHNTimePattern|None=None                         # (0:1) SPHN Time Pattern
    has_flow_profile_interval: SPHNFlowProfileInterval|None=None        # (0:1) SPHN Flow Profile Interval

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

        if not already_in_list(source_system, self.has_source_system_list):
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

        if self.has_start_date_time is not None:
            json_dict_content[f"{SPHN.hasStartDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_start_date_time.isoformat(timespec='milliseconds')

        if self.has_end_date_time is not None:
            json_dict_content[f"{SPHN.hasEndDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_end_date_time.isoformat(timespec='milliseconds')

        if self.has_duration is not None:
            json_dict_content[f"{SPHN.hasDuration.n3(self.sphn_schema.namespace_manager())}"] = self.has_duration.get_json_dict(content, self.id)

        if self.has_time_pattern is not None:
            json_dict_content[f"{SPHN.hasTimePattern.n3(self.sphn_schema.namespace_manager())}"] = self.has_time_pattern.get_json_dict(content, self.id)

        if self.has_drug is not None:
            json_dict_content[f"{SPHN.hasDrug.n3(self.sphn_schema.namespace_manager())}"] = self.has_drug.get_json_dict(content, self.id)

        if self.has_flow_profile_interval is not None:
            json_dict_content[f"{SPHN.hasFlowProfileInterval.n3(self.sphn_schema.namespace_manager())}"] = self.has_flow_profile_interval.get_json_dict(content, self.id)

        if self.has_administration_route_code is not None:
            json_dict_content[f"{SPHN.hasAdministrationRouteCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_administration_route_code.get_json_dict(content, self.id)

        if self.has_reason_to_stop_code is not None:
            json_dict_content[f"{SPHN.hasReasonToStopCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_reason_to_stop_code.get_json_dict(content, self.id)

        if self.has_administrative_case is not None:
            json_dict_content[f"{SPHN.hasAdministrativeCase.n3(self.sphn_schema.namespace_manager())}"] = self.has_administrative_case.get_json_dict(content, self.id)

        if self.has_source_system_list is not None and len(self.has_source_system_list)>0:
            json_dict_content[f"{SPHN.hasSourceSystem.n3(self.sphn_schema.namespace_manager())}"] = [source_system.get_json_dict(content, self.id) for source_system in self.has_source_system_list]

        # subject = <prefix:classname>
        subject = f"{SPHN.ContrastAgentAdministrationEvent.n3(self.sphn_schema.namespace_manager())}"
        
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
    def is_similar(self, other) -> bool :
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_start_date_time == other.has_start_date_time \
            and self.has_end_date_time == other.has_end_date_time \
            and ((self.has_drug is None and other.has_drug is None) \
                 or (self.has_drug is not None and other.has_drug is not None \
                     and self.has_drug.is_similar(other.has_drug))) \
            and ((self.has_administrative_route_code is None and other.has_administrative_route_code is None) \
                 or (self.has_administrative_route_code is not None and other.has_administrative_route_code is not None \
                     and self.has_administrative_route_code.is_similar(other.has_administrative_route_code))) \
            and ((self.has_reason_to_stop_code is None and other.has_reason_to_stop_code is None) \
                 or (self.has_reason_to_stop_code is not None and other.has_reason_to_stop_code is not None \
                     and self.has_reason_to_stop_code.is_similar(other.has_reason_to_stop_code))) \
            and ((self.has_duration is None and other.has_duration is None) \
                 or (self.has_duration is not None and other.has_duration is not None \
                     and self.has_duration.is_similar(other.has_duration))) \
            and ((self.has_time_pattern is None and other.has_time_pattern is None) \
                 or (self.has_time_pattern is not None and other.has_time_pattern is not None \
                     and self.has_time_pattern.is_similar(other.has_time_pattern))) \
            and ((self.has_flow_profile_interval is None and other.has_flow_profile_interval is None) \
                 or (self.has_flow_profile_interval is not None and other.has_flow_profile_interval is not None \
                     and self.has_flow_profile_interval.is_similar(other.has_flow_profile_interval))) \
            and self.has_subject_pseudo_identifier.is_similar(other.has_subject_pseudo_identifier) \
            and ((self.has_administrative_case is None and other.has_administrative_case is None) \
                 or (self.has_administrative_case is not None and other.has_administrative_case is not None \
                     and self.has_administrative_case.is_similar(other.has_administrative_case))) \
            and are_similar_lists(self.has_source_system_list, other.has_source_system_list)

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
