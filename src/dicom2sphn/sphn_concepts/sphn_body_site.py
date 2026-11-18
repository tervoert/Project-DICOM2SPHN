"""
sphn_body_site.py: 
    Part of the example dicom2sphn package.
    It contains the SPHNBodySite class, which represents the SPHN BodySite concept in the SPHN schema.
"""

from pydantic import Field

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_code import SPHNCode
from .sphn_concept import SPHNConcept
from .sphn_laterality import SPHNLaterality


#
# The SPHN Body Site class representing the SPHN Body Site concept in the SPHN schema.
#
class SPHNBodySite(SPHNConcept):

    has_code: SPHNCode                                # (1:1) SPHN Code
    has_laterality: SPHNLaterality|None=None          # (0:1) SPHN Laterality

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())

    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-10-19
    #
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
                    self.has_code, 
                    self.has_laterality
                ) == (
                    other.has_code, 
                    other.has_laterality
                )

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-05
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
            json_dict_content_inline["target_concept"] = SPHN.BodySite

        if self.has_code is not None:
            json_dict_content_inline[f"{SPHN.hasCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_code.get_json_dict(content, self.id)

        if self.has_laterality is not None:
            json_dict_content_inline[f"{SPHN.hasLaterality.n3(self.sphn_schema.namespace_manager())}"] = self.has_laterality.get_json_dict(content, self.id)

        # Return the JSON description
        return json_dict_content_inline

