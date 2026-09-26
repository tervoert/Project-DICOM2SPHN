"""
sphn_time_pattern.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNTimePattern class, which represents the SPHN Time Pattern concept in the SPHN schema.
"""

from pydantic import Field

from dicom2sphn.sphn_concepts.sphn_code import SPHNCode

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_concept import SPHNConcept
from .sphn_quantity import SPHNQuantity


#
# The SPHN Time Pattern class representing the SPHN Time Pattern concept in the SPHN schema.
#
class SPHNTimePattern(SPHNConcept):

    has_offset: SPHNQuantity|None=None                                  # (0:1) SPHN Quantity
    has_frequency: SPHNQuantity|None=None                               # (0:1) SPHN Quantity
    has_type_code: SPHNCode|None=None                                   # (0:1) SPHN Code
    has_time_of_day_code: SPHNCode|None=None                            # (0:1) SPHN Code

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-13
    #
    # It is not a Core Concept
    def get_json_dict(self, content: dict|None=None, source_concept_id: str|None=None) -> dict:
        """ 
        Gets the dict for json output (for the special concepts)
        """
        # Checks
        assert content is None or isinstance(content, dict)
        assert source_concept_id is None or is_valid_string(source_concept_id)        

        # Inline, not a core concept, no reference to separate content description
        json_dict_content_inline = {
            "id": f"{self.id}"
        }

        if self.has_offset is not None:
            json_dict_content_inline[f"{SPHN.hasOffset.n3(self.sphn_schema.namespace_manager())}"] = self.has_offset.get_json_dict(content, self.id)

        if self.has_frequency is not None:
            json_dict_content_inline[f"{SPHN.hasFrequency.n3(self.sphn_schema.namespace_manager())}"] = self.has_frequency.get_json_dict(content, self.id)

        if self.has_type_code is not None:
            json_dict_content_inline[f"{SPHN.hasTypeCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_type_code.get_json_dict(content, self.id)

        if self.has_time_of_day_code is not None:
            json_dict_content_inline[f"{SPHN.hasTimeOfDayCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_time_of_day_code.get_json_dict(content, self.id)

        return json_dict_content_inline

    
    #
    # Edwin 2026-08-13
    #
    def is_similar(self, other: SPHNConcept) -> bool:
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and (self.has_offset is None and other.has_offset is None \
                 or (self.has_offset is not None and other.has_offset is not None \
                     and self.has_offset.is_similar(other.has_offset))) \
            and (self.has_frequency is None and other.has_frequency is None \
                 or (self.has_frequency is not None and other.has_frequency is not None \
                     and self.has_frequency.is_similar(other.has_frequency))) \
            and (self.has_type_code is None and other.has_type_code is None \
                 or (self.has_type_code is not None and other.has_type_code is not None \
                        and self.has_type_code.is_similar(other.has_type_code))) \
            and (self.has_time_of_day_code is None and other.has_time_of_day_code is None \
                 or (self.has_time_of_day_code is not None and other.has_time_of_day_code is not None \
                        and self.has_time_of_day_code.is_similar(other.has_time_of_day_code))) \

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------

