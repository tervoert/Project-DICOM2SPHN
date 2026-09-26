"""
sphn_location.py: 
    Part of the example dicom2sphn package.
    It contains the SPHNLocation class, which represents the SPHN Location concept in the SPHN schema.
"""

from pydantic import Field, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_code import SPHNCode
from .sphn_concept import SPHNConcept


#
# The SPHN Location class representing the SPHN Location concept in the SPHN schema.
#
class SPHNLocation(SPHNConcept):

    has_type_code: SPHNCode                # (1:1) SPHN Code or Terminology
    has_exact: str|None=None               # (0:1) xsd:string

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())
   

    @field_validator('has_exact', mode='after')  
    @classmethod
    def validate_string_or_none(cls, value: str|None) -> str|None:
        if value is not None and not is_valid_string(value):
            raise ValueError(f"SPHN has_exact value '{value}' is not a valid string")
        return value

    # ----------------------------------------------------------------------------------------------------------
    # Public functions
    # ----------------------------------------------------------------------------------------------------------

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

        if self.has_exact is not None:
            json_dict_content_inline[f"{SPHN.hasExact.n3(self.sphn_schema.namespace_manager())}"] = self.has_exact

        if self.has_type_code is not None:
            json_dict_content_inline[f"{SPHN.hasTypeCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_type_code.get_json_dict(content, self.id)

        # Return the JSON description
        return json_dict_content_inline


    #
    # Edwin 2026-08-05
    #
    def is_similar(self, other: SPHNConcept) -> bool :
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_type_code.is_similar(other.has_type_code) \
            and self.has_exact == other.has_exact

    # ----------------------------------------------------------------------------------------------------------
    # Private functions
    # ----------------------------------------------------------------------------------------------------------
