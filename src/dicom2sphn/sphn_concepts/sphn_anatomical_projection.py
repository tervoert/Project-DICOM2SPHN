"""
sphn_anatomical_projection.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNAnatomicalProjection class, which represents the SPHN Anatomical Projection concept in the SPHN schema.
"""

from pydantic import Field, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import already_in_list, are_similar_lists, generate_id, is_valid_string
from .sphn_code import SPHNCode
from .sphn_concept import SPHNConcept


#
# The SPHN Anatomical Projection class representing the SPHN Anatomical Projection concept in the SPHN schema.
#
class SPHNAnatomicalProjection(SPHNConcept):

    has_code: SPHNCode                                      # (1:1) SPHN Code
    has_modifier_code_list: list[SPHNCode]|None=None        # (0:n) SPHN Code (list)

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())


    @field_validator('has_modifier_code_list', mode='after')  
    @classmethod
    def validate_modifier_code_list(cls, value: list[SPHNCode]|None) -> list[SPHNCode]|None:
        if value is not None:
            if not isinstance(value, list) or len(value) == 0:
                raise ValueError('SPHN has_modifier_code_list must be a non-empty list or None')
            if not all(isinstance(item, SPHNCode) for item in value):
                raise TypeError('One or more items in the has_modifier_code_list are not SPHN Code instances')
        return value

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-05
    #
    def add_modifier_sphn_code(self, code: SPHNCode) -> None:
        """ 
        Adds the sphn:Code to the list
        """
        # Checks
        assert isinstance(code, SPHNCode)

        if self.has_modifier_code_list is None:
            self.has_modifier_code_list = [code]
        else:
            if not already_in_list(code, self.has_modifier_code_list):
                self.has_modifier_code_list.append(code)

    #
    # Edwin 2026-08-05
    #
    # It is not a Core Concept
    def get_json_dict(self, content: dict|None=None, source_concept_id: str|None=None) -> dict:
        """ 
        Gets the dict for json output
        """
        # Checks
        assert content is None or isinstance(content, dict)
        assert source_concept_id is None or is_valid_string(source_concept_id)        
        
        # Inline, not a core concept, no reference to separate content description
        json_dict_content_inline = {
            "id": f"{self.id}"
        }

        if self.has_code is not None:
            json_dict_content_inline[f"{SPHN.hasCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_code.get_json_dict(content, self.id)

        if self.has_modifier_code_list is not None and len(self.has_modifier_code_list)>0:
            json_dict_content_inline[f"{SPHN.hasModifierCode.n3(self.sphn_schema.namespace_manager())}"] = [modifier_code.get_json_dict(content, self.id) for modifier_code in self.has_modifier_code_list]

        # Return the JSON description
        return json_dict_content_inline


    #
    # Edwin 2026-08-05
    #
    def is_similar(self, other) -> bool:
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_code.is_similar(other.has_code) \
            and are_similar_lists(self.has_modifier_code_list, other.has_modifier_code_list)
    
    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
