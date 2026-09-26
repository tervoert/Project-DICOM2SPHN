"""
sphn_body_height.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNBodyHeight class, which represents the SPHN Body Height concept in the SPHN schema.
"""
from datetime import datetime

from pydantic import Field

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_concept import SPHNConcept
from .sphn_data_determination import SPHNDataDetermination
from .sphn_quantity import SPHNQuantity


#
# The SPHN Body Height class representing the SPHN Body Height concept in the SPHN schema.
#
class SPHNBodyHeight(SPHNConcept):

    has_quantity: SPHNQuantity                                 # (1:1) SPHN Quantity
    has_date_time: datetime|None=None                          # (0:1) xsd:dateTime
    has_data_determination: SPHNDataDetermination|None=None    # (0:1) SPHNDataDetermination

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

        if self.has_quantity is not None:
            json_dict_content_inline[f"{SPHN.hasQuantity.n3(self.sphn_schema.namespace_manager())}"] = self.has_quantity.get_json_dict(content, self.id)

        if self.has_date_time is not None:
            json_dict_content_inline[f"{SPHN.hasDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_date_time.isoformat(timespec='milliseconds')

        if self.has_data_determination is not None:
            json_dict_content_inline[f"{SPHN.hasDataDetermination.n3(self.sphn_schema.namespace_manager())}"] = self.has_data_determination.get_json_dict(content, self.id)

        # Return the JSON description
        return json_dict_content_inline


    #
    # Edwin 2026-08-05
    #
    def is_similar(self, other) -> bool :
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_date_time == other.has_date_time \
            and self.has_quantity.is_similar(other.has_quantity) \
            and ((self.has_data_determination is None and other.has_data_determination is None) \
                 or (self.has_data_determination is not None and other.has_data_determination is not None \
                     and self.has_data_determination.is_similar(other.has_data_determination)))

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------

