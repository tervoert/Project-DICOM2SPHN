"""
sphn_data_determination.py: 
    Part of the example dicom2sphn package.
    It contains the SPHNDataDetermination class, which represents the SPHN DataDetermination concept in the SPHN schema.
"""

from pydantic import Field

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_code import SPHNCode
from .sphn_concept import SPHNConcept


#
# The SPHN DataDetermination class representing the SPHN DataDetermination concept in the SPHN schema.
#
class SPHNDataDetermination(SPHNConcept):

    has_method_code: SPHNCode               # (1:1) SPHN Code

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())
   
    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-05
    #
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

        if self.has_method_code is not None:
            json_dict_content_inline[f"{SPHN.hasMethodCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_method_code.get_json_dict(content, self.id)

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
            and self.has_method_code.is_similar(other.has_method_code)

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
