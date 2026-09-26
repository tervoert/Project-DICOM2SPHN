"""
sphn_hash.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNHash class, which represents the SPHN Hash concept in the SPHN schema.
"""

from typing import Self

from pydantic import Field, field_validator, model_validator

from ..sphn_schema_graph import SPHN, SPHN_IND, SPHNSchemaGraph
from ..tools import generate_id, is_clean_string, is_valid_string
from .sphn_concept import SPHNConcept


#
# The SPHN Hash class representing the SPHN Hash concept in the SPHN schema.
#
class SPHNHash(SPHNConcept):

    has_algorithm: str                      # (1:1) xsd:string SPHN Hash_algorithm ValueSet member
    has_string_value: str                   # (1:1) xsd:string

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())
     
    @field_validator('has_string_value', mode='after')
    @classmethod
    def validate_string(cls, value: str) -> str:
        if not is_valid_string(value):
            raise ValueError(f'SPHN has_string_value value {value} is not a valid string')
        return value

    @model_validator(mode='after')
    def validate_sphn_hash_algorithm_value_set_member(self) -> Self:
        if not is_clean_string(self.has_algorithm):
            raise ValueError(f'SPHN has_algorithm value {self.has_algorithm} is not a valid clean string')
        if not self.sphn_schema.is_sphn_hash_algorithm_value_set_member(self.has_algorithm):
            raise ValueError(f'{self.has_algorithm} is not a SPHN hash algorithm value set member')
        return self

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

        if self.has_algorithm is not None:
            json_dict_content_inline[f"{SPHN.hasAlgorithm.n3(self.sphn_schema.namespace_manager())}"] = {
                "iri": SPHN_IND + self.has_algorithm
            }

        if self.has_string_value is not None:
            json_dict_content_inline[f"{SPHN.hasStringValue.n3(self.sphn_schema.namespace_manager())}"] = self.has_string_value

        # Return the JSON description of the reference to the instance
        return json_dict_content_inline


    #
    # Edwin 2026-08-05
    #
    def is_similar(self, other) -> bool :
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_algorithm == other.has_algorithm \
            and self.has_string_value == other.has_string_value 

    # ----------------------------------------------------------------------------------------------------------
    # Private functions
    # ----------------------------------------------------------------------------------------------------------
