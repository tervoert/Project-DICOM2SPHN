"""
sphn_image_dimensions.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNImageDimensions class, which represents the SPHN Image Dimensions concept in the SPHN schema.
"""
from pydantic import Field

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_concept import SPHNConcept
from .sphn_pixel_dimensions import SPHNPixelDimensions
from .sphn_quantity import SPHNQuantity


#
# The SPHN Image Dimensions class representing the SPHN Image Dimensions concept in the SPHN schema.
#
class SPHNImageDimensions(SPHNConcept):

    has_number_of_rows: SPHNQuantity|None=None              # (0:1) SPHN Quantity
    has_number_of_columns: SPHNQuantity|None=None           # (0:1) SPHN Quantity
    has_number_of_slices: SPHNQuantity|None=None            # (0:1) SPHN Quantity
    has_slice_spacing: SPHNQuantity|None=None               # (0:1) SPHN Quantity
    has_slice_thickness: SPHNQuantity|None=None             # (0:1) SPHN Quantity
    has_pixel_dimensions: SPHNPixelDimensions|None=None     # (0:1) SPHN PixelDimensions
        
    # Not part of the SPHN schema
    has_number_of_samples_per_pixel: SPHNQuantity|None=None # (0:1) SPHN Quantity

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

        if self.has_number_of_rows is not None:
            json_dict_content_inline[f"{SPHN.hasNumberOfRows.n3(self.sphn_schema.namespace_manager())}"] = self.has_number_of_rows.get_json_dict(content, self.id)

        if self.has_number_of_columns is not None:
            json_dict_content_inline[f"{SPHN.hasNumberOfColumns.n3(self.sphn_schema.namespace_manager())}"] = self.has_number_of_columns.get_json_dict(content, self.id)

        if self.has_number_of_slices is not None:
            json_dict_content_inline[f"{SPHN.hasNumberOfSlices.n3(self.sphn_schema.namespace_manager())}"] = self.has_number_of_slices.get_json_dict(content, self.id)

        if self.has_slice_spacing is not None:
            json_dict_content_inline[f"{SPHN.hasSliceSpacing.n3(self.sphn_schema.namespace_manager())}"] = self.has_slice_spacing.get_json_dict(content, self.id)

        if self.has_slice_thickness is not None:
            json_dict_content_inline[f"{SPHN.hasSliceThickness.n3(self.sphn_schema.namespace_manager())}"] = self.has_slice_thickness.get_json_dict(content, self.id)

        if self.has_pixel_dimensions is not None:
            json_dict_content_inline[f"{SPHN.hasPixelDimensions.n3(self.sphn_schema.namespace_manager())}"] = self.has_pixel_dimensions.get_json_dict(content, self.id)

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
            and ((self.has_number_of_rows is None and other.has_number_of_rows is None) \
                 or (self.has_number_of_rows is not None and other.has_number_of_rows is not None \
                     and self.has_number_of_rows.is_similar(other.has_number_of_rows))) \
            and ((self.has_number_of_columns is None and other.has_number_of_columns is None) \
                 or (self.has_number_of_columns is not None and other.has_number_of_columns is not None \
                     and self.has_number_of_columns.is_similar(other.has_number_of_columns))) \
            and ((self.has_number_of_slices is None and other.has_number_of_slices is None) \
                 or (self.has_number_of_slices is not None and other.has_number_of_slices is not None \
                     and self.has_number_of_slices.is_similar(other.has_number_of_slices))) \
            and ((self.has_slice_spacing is None and other.has_slice_spacing is None) \
                 or (self.has_slice_spacing is not None and other.has_slice_spacing is not None \
                     and self.has_slice_spacing.is_similar(other.has_slice_spacing))) \
            and ((self.has_slice_thickness is None and other.has_slice_thickness is None) \
                 or (self.has_slice_thickness is not None and other.has_slice_thickness is not None \
                     and self.has_slice_thickness.is_similar(other.has_slice_thickness))) \
            and ((self.has_pixel_dimensions is None and other.has_pixel_dimensions is None) \
                 or (self.has_pixel_dimensions is not None and other.has_pixel_dimensions is not None \
                     and self.has_pixel_dimensions.is_similar(other.has_pixel_dimensions)))

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
