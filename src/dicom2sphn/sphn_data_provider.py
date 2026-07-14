"""
sphn_data_provider.py: 
    Part of the example dicom2sphn package.
    It contains the SPHNDataProvider class, which represents the SPHN DataProvider concept in the SPHN schema.
"""

from typing_extensions import Self
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .sphn_schema_graph import SPHNSchemaGraph, SPHN, SPHN_IND
from .tools import is_valid_string, generate_id, is_clean_string
from .sphn_code import SPHNCode
from .sphn_department import SPHNDepartment

#
# The SPHN DataProvider class representing the SPHN DataProvider concept in the SPHN schema.
#
class SPHNDataProvider(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    has_institution_code: SPHNCode                    # (1:1) SPHN Code
    has_department: SPHNDepartment|None=None          # (0:1) SPHN Department
    has_category: str|None=None                       # (0:1) SPHN DataProvider_category ValueSet member

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())
     
   
    @field_validator('has_institution_code', mode='after')  
    @classmethod
    def validate_completeness(cls, value: SPHNCode) -> SPHNCode:
        if not value.is_complete():
            raise ValueError('SPHN Code instance is not complete')
        return value  
    
    @field_validator('has_department', mode='after')  
    @classmethod
    def validate_none_or_completeness(cls, value: SPHNDepartment|None) -> SPHNDepartment|None:
        if value is not None and not value.is_complete():
            raise ValueError('SPHN Department instance is not complete')
        return value  

    @field_validator('has_category', mode='after')  
    @classmethod
    def validate_string_or_none(cls, value: str|None) -> str|None:
        if value is not None and not is_clean_string(value):
            raise ValueError('SPHN DataProvider category string value is not a valid clean string')
        return value  

    @model_validator(mode='after')
    def validate_sphn_data_provider_category_value_set_member(self) -> Self:
        if self.has_category is not None and not self.sphn_schema.is_sphn_data_provider_category_value_set_member(self.has_category):
            raise ValueError(f'{self.has_category} is not a SPHN DataProvider category value set member')
        return self

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-07-09
    #

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

    def get_json_dict_special(self, content: dict|None=None, source_concept_id: str|None=None) -> dict:
        """ 
        Gets the dict for json output (for the special concepts)
        """
        # Checks
        assert content is None or isinstance(content, dict)
        assert source_concept_id is None or is_valid_string(source_concept_id)        

        assert self.is_complete()

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
    # Edwin 2026-07-09
    #
    def is_complete(self):
        """
        Checks if all mandatory metadata is available
        """

        # result = isinstance(self.has_institution_code, SPHNCode) \
        #          and self.has_institution_code.is_complete() \
        #          and (self.has_department is None 
        #               or (isinstance(self.has_department, SPHNDepartment) 
        #                   and self.has_department.is_complete())) \
        #          and (self.has_category is None 
        #               or (is_clean_string(self.has_category) \
        #                   and self.sphn_schema.is_sphn_data_provider_category_value_set_member(self.has_category)))
        
        result = self.has_institution_code.is_complete() \
                 and (self.has_department is None or self.has_department.is_complete())
        
        return result
    
    #
    # Edwin 2026-07-09
    #
    def is_similar(self, other):
        """
        Compare this instance with another instance of the same class
        """
        # Checks
        assert self.is_complete()

        # Check if type is similar
        if not isinstance(other, type(self)):
            # Not similar
            return False

        assert other.is_complete()

        # Checking if the institution code is similar
        if not isinstance(other.has_institution_code, type(self.has_institution_code)):
            # Not similar
            return False
        if self.has_institution_code is not None \
           and not self.has_institution_code.is_similar(other.has_institution_code):
            # Not similar
            return False

        # Checking if the department is similar
        if not isinstance(other.has_department, type(self.has_department)):
            # Not similar
            return False
        if self.has_department is not None \
           and not self.has_department.is_similar(other.has_department):
            # Not similar
            return False

        # Checking if the category is similar
        if self.has_category != other.has_category:
            # Not similar
            return False

        # Similar
        return True

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
