"""
sphn_software.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNSoftware class, which represents the SPHN Software concept in the SPHN schema.
"""

from pydantic import Field, ValidationInfo, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_concept import SPHNConcept


#
# The SPHN Software class representing the SPHN Software concept in the SPHN schema.
#
class SPHNSoftware(SPHNConcept):

    has_name: str                                   # (1:1) xsd:string
    has_version: str                                # (1:1) xsd:string
    has_description: str|None=None                  # (0:1) xsd:string          # Not in DICOM
    has_uniform_resource_locator: str|None=None     # (0:1) xsd:string          # Not in DICOM

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())
     
    @field_validator('has_name', 'has_version', mode='after')  
    @classmethod
    def validate_string(cls, value: str, info: ValidationInfo) -> str:
        if not is_valid_string(value):
            raise ValueError(f"SPHN '{info.field_name}' value '{value}' is not a valid string")
        return value  

    @field_validator('has_description', 'has_uniform_resource_locator', mode='after')
    @classmethod
    def validate_string_or_none(cls, value: str|None, info: ValidationInfo) -> str|None:
        if value is not None and not is_valid_string(value):
            raise ValueError(f"SPHN '{info.field_name}' value '{value}' is not a valid string")
        return value  

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

        if self.has_name is not None:
            json_dict_content_inline[f"{SPHN.hasName.n3(self.sphn_schema.namespace_manager())}"] = self.has_name

        if self.has_version is not None:
            json_dict_content_inline[f"{SPHN.hasVersion.n3(self.sphn_schema.namespace_manager())}"] = self.has_version

        if self.has_description is not None:
            json_dict_content_inline[f"{SPHN.hasDescription.n3(self.sphn_schema.namespace_manager())}"] = self.has_description

        if self.has_uniform_resource_locator is not None:
            json_dict_content_inline[f"{SPHN.hasUniformResourceLocator.n3(self.sphn_schema.namespace_manager())}"] = self.has_uniform_resource_locator

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
            and self.has_name == other.has_name \
            and self.has_version == other.has_version \
            and self.has_description == other.has_description \
            and self.has_uniform_resource_locator == other.has_uniform_resource_locator

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
