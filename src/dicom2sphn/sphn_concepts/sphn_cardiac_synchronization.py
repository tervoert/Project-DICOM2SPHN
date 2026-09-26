"""
sphn_cardiac_synchronization.py: 
    Part of the example dicom2sphn package.
    It contains the SPHNCardiacSynchronization class, which represents the SPHN Cardiac Synchronization concept in the SPHN schema.
"""

from typing import Self

from pydantic import Field, model_validator

from ..sphn_schema_graph import SPHN, SPHN_IND, SPHNSchemaGraph
from ..tools import generate_id, is_clean_string, is_valid_string
from .sphn_concept import SPHNConcept
from .sphn_synchronization import SPHNSynchronization


#
# The SPHN Cardiac Synchronization class representing the SPHN Cardiac Synchronization concept in the SPHN schema.
#
class SPHNCardiacSynchronization(SPHNSynchronization):

    has_method: str|None=None                               # (0:1) SPHN CardiacSynchronization_method ValueSet member
    has_signal_source: str|None=None                        # (0:1) SPHN CardiacSynchronization_signalSource ValueSet member

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())
     
   
    @model_validator(mode='after')
    def validate_sphn_cardiac_synchronization_method_value_set_member(self) -> Self:
        if self.has_method is not None:
            if not is_clean_string(self.has_method):
                raise ValueError("SPHN 'has_method' value is not a valid clean string")
            if not self.sphn_schema.is_sphn_cardiac_synchronization_method_value_set_member(self.has_method):
                raise ValueError(f"SPHN 'has_method' value: '{self.has_method}' is not a SPHN 'CardiacSynchronization_method' value set member")
        return self

    @model_validator(mode='after')
    def validate_sphn_cardiac_synchronization_signal_source_value_set_member(self) -> Self:
        if self.has_signal_source is not None:
            if not is_clean_string(self.has_signal_source):
                raise ValueError("SPHN 'has_signal_source' value is not a valid clean string")
            if not self.sphn_schema.is_sphn_cardiac_synchronization_signal_source_value_set_member(self.has_signal_source):
                raise ValueError(f"SPHN 'has_signal_source' value: '{self.has_signal_source}' is not a SPHN 'CardiacSynchronization_signalSource' value set member")
        return self

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

        json_dict = {
            "id": f"{self.id}"
        }

        if self.has_method is not None:
            json_dict[f"{SPHN.hasMethod.n3(self.sphn_schema.namespace_manager())}"] = {
                "iri": SPHN_IND + self.has_method
            }

        if self.has_signal_source is not None:
            json_dict[f"{SPHN.hasSignalSource.n3(self.sphn_schema.namespace_manager())}"] = {
                "iri": SPHN_IND + self.has_signal_source
            }

        return json_dict

    
    #
    # Edwin 2026-08-13
    #
    def is_similar(self, other: SPHNConcept) -> bool:
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_method == other.has_method \
            and self.has_signal_source == other.has_signal_source
            
    
    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
