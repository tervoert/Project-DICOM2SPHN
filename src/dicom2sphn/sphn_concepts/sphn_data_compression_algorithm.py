"""
sphn_data_compression_algorithm.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNDataCompressionAlgorithm class, which represents the SPHN Data Compression Algorithm concept in the SPHN schema.
"""
from typing import Self

from pydantic import Field, ValidationInfo, field_validator, model_validator

from ..sphn_schema_graph import SPHN, SPHN_IND, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_concept import SPHNConcept
from .sphn_quantity import SPHNQuantity


#
# The SPHN Data Compression Algorithm class representing the SPHN Data Compression Algorithm concept in the SPHN schema.
#
class SPHNDataCompressionAlgorithm(SPHNConcept):

    has_name: str|None=None                         # (0:1) xsd:string
    has_version: str|None=None                      # (0:1) xsd:string
    has_description: str|None=None                  # (0:1) xsd:string          # Not in DICOM
    has_uniform_resource_locator: str|None=None     # (0:1) xsd:string          # Not in DICOM

    has_type: str|None=None                         # (0:1) SPHN DataCompressionAlgorithm_type (ValueSet member)
    has_method: str|None=None                       # (0:1) SPHN DataCompressionAlgorithm_method (ValueSet member)
    has_ratio: SPHNQuantity|None=None               # (0:1) SPHN Quantity

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())
     

    @field_validator('has_name', 'has_version','has_description', 'has_uniform_resource_locator', mode='after')
    @classmethod
    def validate_string_or_none(cls, value: str|None, info: ValidationInfo) -> str|None:
        if value is not None and not is_valid_string(value):
            raise ValueError(f'SPHN {info.field_name} value is not a valid string or None')
        return value  

    @field_validator('has_ratio', mode='after')  
    @classmethod
    def validate_ratio(cls, value: SPHNQuantity|None, info: ValidationInfo) -> SPHNQuantity|None:
        if value is not None and value.has_value <= 0:
            raise ValueError(f'SPHN {info.field_name} value must be greater than 0')
        return value

    @model_validator(mode='after')
    def validate_sphn_data_compression_algorithm_type_value_set_member(self) -> Self:
        if self.has_type is not None and not self.sphn_schema.is_sphn_data_compression_algorithm_type_value_set_member(self.has_type):
            raise ValueError(f'SPHN has_type value {self.has_type} is not a SPHN Data Compression Algorithm type value set member or None')
        return self

    @model_validator(mode='after')
    def validate_sphn_data_compression_algorithm_method_value_set_member(self) -> Self:
        if self.has_method is not None and not self.sphn_schema.is_sphn_data_compression_algorithm_method_value_set_member(self.has_method):
            raise ValueError(f'SPHN has_method value {self.has_method} is not a SPHN Data Compression Algorithm method value set member or None')
        return self

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

        if self.has_type is not None:
            json_dict_content_inline[f"{SPHN.hasType.n3(self.sphn_schema.namespace_manager())}"] = {
                "iri": SPHN_IND + self.has_type
            }

        if self.has_method is not None:
            json_dict_content_inline[f"{SPHN.hasMethod.n3(self.sphn_schema.namespace_manager())}"] = {
                "iri": SPHN_IND + self.has_method
            }

        if self.has_ratio is not None:
            json_dict_content_inline[f"{SPHN.hasRatio.n3(self.sphn_schema.namespace_manager())}"] = self.has_ratio.get_json_dict(content, self.id)

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
            and self.has_uniform_resource_locator == other.has_uniform_resource_locator \
            and self.has_type == other.has_type \
            and self.has_method == other.has_method \
            and ((self.has_ratio is None and other.has_ratio is None) \
                 or (self.has_ratio is not None and other.has_ratio is not None \
                     and self.has_ratio.is_similar(other.has_ratio)))

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
