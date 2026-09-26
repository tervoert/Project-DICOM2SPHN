"""
sphn_discharge.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNDischarge class, which represents the SPHN Discharge concept in the SPHN schema.
"""
from datetime import datetime

from pydantic import Field

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_concept import SPHNConcept
from .sphn_location import SPHNLocation


#
# The SPHN Discharge class representing the SPHN Discharge concept in the SPHN schema.
#
class SPHNDischarge(SPHNConcept):

    has_date_time: datetime                        # (1:1) xsd:dateTime
    has_target_location: SPHNLocation|None=None    # (0:1) SPHN Location

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

        if self.has_date_time is not None:
            json_dict_content_inline[f"{SPHN.hasDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_date_time.isoformat(timespec='milliseconds')

        if self.has_target_location is not None:
            json_dict_content_inline[f"{SPHN.hasTargetLocation.n3(self.sphn_schema.namespace_manager())}"] = self.has_target_location.get_json_dict(content, self.id)

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
            and self.has_date_time == other.has_date_time \
            and ((self.has_target_location is None and other.has_target_location is None) \
                 or (self.has_target_location is not None and other.has_target_location is not None \
                     and self.has_target_location.is_similar(other.has_target_location)))
    
    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
    