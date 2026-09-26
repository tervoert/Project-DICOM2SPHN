"""
sphn_contrast_agent_phase.py: 
    Part of the example dicom2sphn package.
    It contains the SPHNContrastAgentPhase class, which represents the SPHN Contrast Agent Phase concept in the SPHN schema.
"""

from pydantic import Field

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_body_site import SPHNBodySite
from .sphn_code import SPHNCode
from .sphn_concept import SPHNConcept


#
#
# The SPHN Contrast Agent Phase class representing the SPHN Contrast Agent Phase concept in the SPHN schema.
#
class SPHNContrastAgentPhase(SPHNConcept):

    has_timing_code: SPHNCode|None=None                             # (0:1) SPHN Code
    has_localization: SPHNBodySite|None=None                        # (0:1) SPHN BodySite

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
        Gets the dict for json output
        """
        # Checks
        assert content is None or isinstance(content, dict)
        assert source_concept_id is None or is_valid_string(source_concept_id)        
        
        # Inline, not a core concept, no reference to separate content description
        json_dict_content_inline = {
            "id": f"{self.id}"
        }

        if self.has_timing_code is not None:
            json_dict_content_inline[f"{SPHN.hasTimingCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_timing_code.get_json_dict(content, self.id)

        if self.has_localization is not None:
            json_dict_content_inline[f"{SPHN.hasLocalization.n3(self.sphn_schema.namespace_manager())}"] = self.has_localization.get_json_dict(content, self.id)

        # Return the JSON description
        return json_dict_content_inline


    #
    # Edwin 2026-08-13
    #
    def is_similar(self, other, rel_tol: float=1e-4, abs_tol: float=1e-9) -> bool:
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and ((self.has_timing_code is None and other.has_timing_code is None) \
                 or (self.has_timing_code is not None and other.has_timing_code is not None \
                     and self.has_timing_code.is_similar(other.has_timing_code))) \
            and ((self.has_localization is None and other.has_localization is None) \
                 or (self.has_localization is not None and other.has_localization is not None \
                     and self.has_localization.is_similar(other.has_localization)))

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------

