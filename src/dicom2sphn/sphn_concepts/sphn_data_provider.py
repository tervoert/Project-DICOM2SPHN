"""
sphn_data_provider.py: 
    Part of the example dicom2sphn package.
    It contains the SPHNDataProvider class, which represents the SPHN DataProvider concept in the SPHN schema.
"""

from typing import Self

from pydantic import Field, model_validator

from ..sphn_schema_graph import SPHN, SPHN_IND, SPHNSchemaGraph
from ..tools import generate_id, is_clean_string, is_valid_string
from .sphn_code import SPHNCode
from .sphn_concept import SPHNConcept
from .sphn_department import SPHNDepartment


#
# The SPHN DataProvider class representing the SPHN DataProvider concept in the SPHN schema.
#
class SPHNDataProvider(SPHNConcept):

    has_institution_code: SPHNCode                    # (1:1) SPHN Code
    has_department: SPHNDepartment|None=None          # (0:1) SPHN Department
    has_category: str|None=None                       # (0:1) SPHN DataProvider_category ValueSet member

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())
     
   
    @model_validator(mode='after')
    def validate_sphn_data_provider_category_value_set_member(self) -> Self:
        if self.has_category is not None:
            if not is_clean_string(self.has_category):
                raise ValueError(f'SPHN has_category value {self.has_category} is not a valid string')
            if not self.sphn_schema.is_sphn_data_provider_category_value_set_member(self.has_category):
                raise ValueError(f'SPHN has_category value {self.has_category} is not a SPHN DataProvider category value set member')
        return self

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Example DataProvider/Department/Category/InstitutionCode
    #

    # "sphn:DataProvider": {
    #     "id": "457105f5-65b5-4e65-aa62-396b6e5e24ac",
    #     "sphn:hasCategory": {
    #         "iri": "https://biomedit.ch/rdf/sphn-schema/sphn/individual#ExternalLaboratory"
    #     },
    #     "sphn:hasDepartment": {
    #         "id": "2f8b1b49-e6a0-4f95-b618-ca80d33e9b0e",
    #         "sphn:hasName": "Lorem"
    #     },
    #     "sphn:hasInstitutionCode": {
    #         "id": "d7f006b8-5866-47d1-ae3a-5fac09381783",
    #         "sphn:hasCodingSystemAndVersion": "reprehenderit accusantium illum illum",
    #         "sphn:hasIdentifier": "ID-60487647",
    #         "sphn:hasName": "odit architecto illum esse esse dolor elit. ipsum",
    #         "sourceConceptID": "457105f5-65b5-4e65-aa62-396b6e5e24ac"
    #     }
    # }

    #
    # Edwin 2026-08-05
    #
    # This is a Special Concept
    # - No content and no source_concept_id are provided
    #
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

        if self.has_institution_code is not None:
            json_dict[f"{SPHN.hasInstitutionCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_institution_code.get_json_dict(content, self.id)

        if self.has_category is not None:
            json_dict[f"{SPHN.hasCategory.n3(self.sphn_schema.namespace_manager())}"] = {
                "iri": SPHN_IND + self.has_category
            }

        if self.has_department is not None:
            json_dict[f"{SPHN.hasDepartment.n3(self.sphn_schema.namespace_manager())}"] = self.has_department.get_json_dict(content, self.id)

        return json_dict

    
    #
    # Edwin 2026-08-05
    #
    def is_similar(self, other: SPHNConcept) -> bool:
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_category == other.has_category \
            and self.has_institution_code.is_similar(other.has_institution_code) \
            and (self.has_department is None and other.has_department is None \
                or self.has_department is not None and other.has_department is not None \
                    and self.has_department.is_similar(other.has_department))
            
    
    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
