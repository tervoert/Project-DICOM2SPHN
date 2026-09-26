"""
sphn_care_handling.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNCareHandling class, which represents the SPHN Care Handling concept in the SPHN schema.
"""

from pydantic import Field, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import already_in_list, are_similar_lists, generate_id, is_valid_string
from .sphn_code import SPHNCode
from .sphn_concept import SPHNConcept
from .sphn_source_system import SPHNSourceSystem


#
# The SPHN Care Handling class representing the SPHN Care Handling concept in the SPHN schema.
#
class SPHNCareHandling(SPHNConcept):

    has_type_code: SPHNCode                            # (1:1) SPHN Quantity
    has_source_system_list: list[SPHNSourceSystem]     # (1:n) SPHN SourceSystem (list)

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
    # Edwin 2026-07-21
    #
    # It is not a Core Concept
    def get_json_dict(self, content: dict|None=None, source_concept_id: str|None=None) -> dict:
        """ 
        Gets the dict for json output
        """
        # Checks
        assert content is None or isinstance(content, dict)
        assert source_concept_id is None or is_valid_string(source_concept_id)        
        
        assert self.is_complete()

        # Inline, not a core concept, no reference to separate content description
        json_dict_content_inline = {
            "id": f"{self.id}"
        }

        if self.has_type_code is not None:
            json_dict_content_inline[f"{SPHN.hasTypeCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_type_code.get_json_dict(content, self.id)

        if self.has_source_system_list is not None and len(self.has_source_system_list)>0:
            json_dict_content_inline[f"{SPHN.hasSourceSystem.n3(self.sphn_schema.namespace_manager())}"] = [source_system.get_json_dict(content, self.id) for source_system in self.has_source_system_list]

        # Return the JSON description
        return json_dict_content_inline


    #
    # Edwin 2026-07-21
    #
    def is_similar(self, other: SPHNConcept) -> bool :
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_type_code.is_similar(other.has_type_code) \
            and are_similar_lists(self.has_source_system_list, other.has_source_system_list)

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
