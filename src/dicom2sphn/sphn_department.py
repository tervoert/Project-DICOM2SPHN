"""
sphn_department.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNDepartment class, which represents the SPHN Department concept in the SPHN schema.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from .sphn_schema_graph import SPHNSchemaGraph, SPHN
from .tools import is_valid_string, generate_id

#
# The SPHN Department class representing the SPHN Department concept in the SPHN schema.
#
class SPHNDepartment(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    has_name: str                           # (1:1) xsd:string

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())
     
    @field_validator('has_name', mode='after')  
    @classmethod
    def validate_string(cls, value: str) -> str:
        if not is_valid_string(value):
            raise ValueError(f'{value} is not a valid string')
        return value  

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-07-09
    #

    #
    # Example DataProvider/Department
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

    def get_json_dict(self, content: dict|None=None, source_concept_id: str|None=None) -> dict:
        """ 
        Gets the dict for json output (for the special concepts)
        """
        # Checks
        assert content is None or isinstance(content, dict)
        assert source_concept_id is None or is_valid_string(source_concept_id)        

        assert self.is_complete()

        # Inline, not a core concept, no reference to separate content description
        json_dict_content_inline = {
            "id": f"{self.id}"
        }

        if self.has_name is not None:
            json_dict_content_inline[f"{SPHN.hasName.n3(self.sphn_schema.namespace_manager())}"] = self.has_name

        return json_dict_content_inline

    #
    # Edwin 2026-07-09
    #
    def is_complete(self) -> bool:
        """
        Checks if all mandatory metadata is available
        """

        result = True

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

        # Checking if the name is similar
        if self.has_name != other.has_name:
            # Not similar
            return False

        # Similar
        return True

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
