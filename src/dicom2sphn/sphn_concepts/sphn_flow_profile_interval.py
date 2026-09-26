"""
sphn_flow_profile_interval.py:
    Part of the example dicom2sphn package. 
    It contains the SPHNFlowProfileInterval class, which represents the SPHN Flow Profile Interval concept in the SPHN schema.
"""

from datetime import datetime

from pydantic import Field

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_concept import SPHNConcept
from .sphn_quantity import SPHNQuantity


#
# The SPHN Flow Profile Interval class representing the SPHN Flow Profile Interval concept in the SPHN schema.
class SPHNFlowProfileInterval(SPHNConcept):

    has_start_datetime: datetime|None=None                              # (0:1) xsd:dateTime
    has_end_datetime: datetime|None=None                                # (0:1) xsd:dateTime
    has_duration: SPHNQuantity|None=None                                # (0:1) SPHN Quantity
    has_volume: SPHNQuantity|None=None                                  # (0:1) SPHN Quantity
    has_volumetric_flow_rate: SPHNQuantity|None=None                    # (0:1) SPHN Quantity

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())

    # ----------------------------------------------------------------------------------------------------------
    # Public functions
    # ----------------------------------------------------------------------------------------------------------

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

        if self.has_start_date_time is not None:
            json_dict_content_inline[f"{SPHN.hasStartDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_start_date_time.isoformat(timespec='milliseconds')

        if self.has_end_date_time is not None:
            json_dict_content_inline[f"{SPHN.hasEndDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_end_date_time.isoformat(timespec='milliseconds')

        if self.has_duration is not None:
            json_dict_content_inline[f"{SPHN.hasDuration.n3(self.sphn_schema.namespace_manager())}"] = self.has_duration.get_json_dict(content, self.id)

        if self.has_volume is not None:
            json_dict_content_inline[f"{SPHN.hasVolume.n3(self.sphn_schema.namespace_manager())}"] = self.has_volume.get_json_dict(content, self.id)

        if self.has_volumetric_flow_rate is not None:
            json_dict_content_inline[f"{SPHN.hasVolumetricFlowRate.n3(self.sphn_schema.namespace_manager())}"] = self.has_volumetric_flow_rate.get_json_dict(content, self.id)

        # Return the JSON description
        return json_dict_content_inline

    
    #
    # Edwin 2026-08-13
    #
    def is_similar(self, other) -> bool :
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_start_datetime == other.has_start_datetime \
            and self.has_end_datetime == other.has_end_datetime \
            and ((self.has_duration is None and other.has_duration is None) \
                 or (self.has_duration is not None and other.has_duration is not None \
                     and self.has_duration.is_similar(other.has_duration))) \
            and ((self.has_volume is None and other.has_volume is None) \
                 or (self.has_volume is not None and other.has_volume is not None \
                     and self.has_volume.is_similar(other.has_volume))) \
            and ((self.has_volumetric_flow_rate is None and other.has_volumetric_flow_rate is None) \
                 or (self.has_volumetric_flow_rate is not None and other.has_volumetric_flow_rate is not None \
                     and self.has_volumetric_flow_rate.is_similar(other.has_volumetric_flow_rate)))

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
