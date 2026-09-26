"""
sphn_quantity.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNQuantity class, which represents the SPHN Quantity concept in the SPHN schema.
"""
from math import isclose
from typing import Self

from pydantic import Field, model_validator

from ..sphn_schema_graph import SPHN, SPHN_IND, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_concept import SPHNConcept
from .sphn_unit import SPHNUnit


#
# The SPHN Quantity class representing the SPHN Quantity concept in the SPHN schema.
#
class SPHNQuantity(SPHNConcept):

    has_value: int|float                    # (1:1) xsd:double
    has_unit: SPHNUnit                      # (1:1) SPHN Unit
    has_comparator: str|None=None           # (0:1) SPHN Comparator ValueSet member

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())


    @model_validator(mode='after')
    def validate_sphn_comparator_value_set_member(self) -> Self:
        if self.has_comparator is not None:
            if not is_valid_string(self.has_comparator):
                raise ValueError(f"SPHN 'has_comparator' value '{self.has_comparator}' is not a valid string")
            if not self.sphn_schema.is_sphn_comparator_value_set_member(self.has_comparator):
                raise ValueError(f"SPHN 'has_comparator' value '{self.has_comparator}' is not a SPHN Comparator value set member")
        return self

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

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

        if self.has_value is not None:
            json_dict_content_inline[f"{SPHN.hasValue.n3(self.sphn_schema.namespace_manager())}"] = self.has_value

        if self.has_unit is not None:
            json_dict_content_inline[f"{SPHN.hasUnit.n3(self.sphn_schema.namespace_manager())}"] = self.has_unit.get_json_dict(content, self.id)

        if self.has_comparator is not None:
            json_dict_content_inline[f"{SPHN.hasComparator.n3(self.sphn_schema.namespace_manager())}"] = {
                "iri": SPHN_IND + self.has_comparator
            }

        # Return the JSON description
        return json_dict_content_inline


    #
    # Edwin 2026-08-05
    #
    def is_similar(self, other: SPHNConcept, rel_tol: float=1e-4, abs_tol: float=1e-9) -> bool :
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_comparator == other.has_comparator \
            and self.has_unit.is_similar(other.has_unit) \
            and isinstance(other.has_value, type(self.has_value)) \
            and ((isinstance(self.has_value, int) and self.has_value == other.has_value) \
                 or (isinstance(self.has_value, float) and isclose(self.has_value, other.has_value, rel_tol=rel_tol, abs_tol=abs_tol)))

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
