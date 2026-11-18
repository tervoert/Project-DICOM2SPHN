"""
sphn_physiologic_state.py: 
    Part of the example dicom2sphn package.
    It contains the SPHNPhysiologicState class, which represents the SPHN Physiologic State concept in the SPHN schema.
"""

from pydantic import Field

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_code import SPHNCode
from .sphn_concept import SPHNConcept


#
# The SPHN Physiologic State class representing the SPHN Physiologic State concept in the SPHN schema.
#
class SPHNPhysiologicState(SPHNConcept):

    has_code: SPHNCode                                 # (1:1) SPHN Code or Terminology

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())

    # ----------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-10-19
    #
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
                    self.has_code,
                ) == (
                    other.has_code,
                )

    # ----------------------------------------------------------------------------------------------------------
    # Public functions
    # ----------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-13
    #
    # This is a Normal Concept
    def get_json_dict(self, content: dict|None=None, source_concept_id: str|None=None, write_target_concept: bool=False) -> dict:
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

        if write_target_concept is True:
            json_dict_content_inline["target_concept"] = SPHN.PhysiologicState

        if self.has_code is not None:
            json_dict_content_inline[f"{SPHN.hasCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_code.get_json_dict(content, self.id)

        # Return the JSON description
        return json_dict_content_inline

