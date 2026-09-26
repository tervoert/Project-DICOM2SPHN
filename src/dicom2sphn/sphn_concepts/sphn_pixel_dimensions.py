"""
sphn_pixel_dimensions.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNPixelDimensions class, which represents the SPHN Pixel Dimensions concept in the SPHN schema.
"""

from pydantic import Field

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_concept import SPHNConcept
from .sphn_quantity import SPHNQuantity


#
# The SPHN Pixel Dimensions class representing the SPHN Pixel Dimensions concept in the SPHN schema.
#
class SPHNPixelDimensions(SPHNConcept):

    has_row_spacing: SPHNQuantity|None=None           # (0:1) SPHN Quantity
    has_column_spacing: SPHNQuantity|None=None        # (0:1) SPHN Quantity

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())

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

        if self.has_row_spacing is not None:
            json_dict_content_inline[f"{SPHN.hasRowSpacing.n3(self.sphn_schema.namespace_manager())}"] = self.has_row_spacing.get_json_dict(content, self.id)

        if self.has_column_spacing is not None:
            json_dict_content_inline[f"{SPHN.hasColumnSpacing.n3(self.sphn_schema.namespace_manager())}"] = self.has_column_spacing.get_json_dict(content, self.id)

        # Return the JSON description
        return json_dict_content_inline

    
    #
    # Edwin 2026-08-05
    #
    def is_similar(self, other: SPHNConcept) -> bool:
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and (self.has_row_spacing is None and other.has_row_spacing is None \
                 or (self.has_row_spacing is not None and other.has_row_spacing is not None \
                     and self.has_row_spacing.is_similar(other.has_row_spacing))) \
            and (self.has_column_spacing is None and other.has_column_spacing is None \
                 or (self.has_column_spacing is not None and other.has_column_spacing is not None \
                     and self.has_column_spacing.is_similar(other.has_column_spacing)))

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------

