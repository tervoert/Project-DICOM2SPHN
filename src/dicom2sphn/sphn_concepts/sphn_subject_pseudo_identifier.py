"""
sphn_subject_pseudo_identifier.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNSubjectPseudoIdentifier class, which represents the SPHN SubjectPseudoIdentifier concept in the SPHN schema.
"""

from pydantic import Field, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import are_similar_lists, generate_id, is_valid_string
from .sphn_concept import SPHNConcept
from .sphn_data_provider import SPHNDataProvider


#
# The SPHN SubjectPseudoIdentifier class representing the SPHN SubjectPseudoIdentifier concept in the SPHN schema.
#
class SPHNSubjectPseudoIdentifier(SPHNConcept):

    has_identifier: str                                 # (1:1) xsd:string
    has_data_provider: SPHNDataProvider                 # (1:1) SPHN DataProvider
    has_shared_identifier_list: list[str]|None=None     # (0:n) xsd:anyURI          # Not implemented

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())


    @field_validator('has_identifier', mode='after')  
    @classmethod
    def validate_string(cls, value: str) -> str:
        if not is_valid_string(value):
            raise ValueError(f"SPHN 'has_identifier' value '{value}' is not a valid string")
        return value  

    @field_validator('has_shared_identifier_list', mode='after')  
    @classmethod
    def validate_shared_identifier_list(cls, value: list[str]|None) -> list[str]|None:
        if value is not None:
            if len(value) == 0:
                raise ValueError("SPHN 'has_shared_identifier_list' must be a non-empty list or None")
            if not all(is_valid_string(item) for item in value):
                raise TypeError("One or more items in the 'has_shared_identifier_list' are not valid strings")
        return value

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    # "sphn:SubjectPseudoIdentifier": { 
    #      "id": "patient_1", 
    #      "sphn:hasIdentifier": "patient_1"
    # }

    #
    # Edwin 2026-08-05
    #
    # This is a Special Concept
    # - No content and no source_concept_id are provided
    #
    def get_json_dict(self, content: dict|None=None, source_concept_id: str|None=None) -> dict:
        """ 
        Gets the dict for json output (Special Concept)
        """
        # Checks
        assert content is None or isinstance(content, dict)
        assert source_concept_id is None or is_valid_string(source_concept_id)        

        json_dict = {
            "id": f"{self.id}"
        }

        if self.has_identifier is not None:
            json_dict[f"{SPHN.hasIdentifier.n3(self.sphn_schema.namespace_manager())}"] = self.has_identifier

        return json_dict


    #
    # Edwin 2026-08-05
    #
    def is_similar(self, other: SPHNConcept) -> bool:
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_identifier == other.has_identifier \
            and self.has_data_provider.is_similar(other.has_data_provider) \
            and ((self.has_shared_identifier_list is None and other.has_shared_identifier_list is None) \
                 or (self.has_shared_identifier_list is not None and other.has_shared_identifier_list is not None \
                     and are_similar_lists(self.has_shared_identifier_list, other.has_shared_identifier_list)))

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------

