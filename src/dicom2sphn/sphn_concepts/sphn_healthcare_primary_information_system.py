"""
sphn_healthcare_primary_information_system.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNHealthcarePrimaryInformationSystem class, which represents the SPHN HealthcarePrimaryInformationSystem concept in the SPHN schema.
"""

from pydantic import Field, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_code import SPHNCode
from .sphn_concept import SPHNConcept


#
# The SPHN HealthcarePrimaryInformationSystem class representing the SPHN HealthcarePrimaryInformationSystem concept in the SPHN schema.
#
class SPHNHealthcarePrimaryInformationSystem(SPHNConcept):

    has_name: str|None=None                           # (0:1) xsd:string
    has_code: SPHNCode|None=None                      # (0:1) SPHN Code

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())


    @field_validator('has_name', mode='after')  
    @classmethod
    def validate_string_or_none(cls, value: str|None) -> str|None:
        if value is not None and not is_valid_string(value):
            raise ValueError(f'SPHN has_name value {value} is not a valid string or None')
        return value  

    # ----------------------------------------------------------------------------------------------------------
    # Public functions
    # ----------------------------------------------------------------------------------------------------------

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

        if self.has_name is not None:
            json_dict_content_inline[f"{SPHN.hasName.n3(self.sphn_schema.namespace_manager())}"] = self.has_name

        if self.has_code is not None:
            json_dict_content_inline[f"{SPHN.hasCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_code.get_json_dict(content, self.id)

        # Return the JSON description of the reference to the instance
        return json_dict_content_inline


    #
    # Edwin 2026-08-05
    #
    def is_similar(self, other) -> bool:
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_name == other.has_name \
            and ((self.has_code is None and other.has_code is None) \
                 or (self.has_code is not None and other.has_code is not None \
                     and self.has_code.is_similar(other.has_code)))
    
    # ----------------------------------------------------------------------------------------------------------
    # Private functions
    # ----------------------------------------------------------------------------------------------------------
