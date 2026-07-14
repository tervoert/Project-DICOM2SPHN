"""
sphn_code.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNCode class, which represents the SPHN Code concept in the SPHN schema.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from .sphn_schema_graph import SPHNSchemaGraph, SPHN, SPHN_DCM, UCUM, EDAM, SNOMED
from .tools import is_valid_string, generate_id

# The implemented coding systems 
CodingSystemList = ['SNOMED-CT', 'UCUM', 'DCM', 'UID', 'EDAM']

#
# The SPHN Code class representing the SPHN Code concept in the SPHN schema.
#
class SPHNCode(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    has_coding_system_and_version: str      # (1:1) xsd:string
    has_identifier: str                     # (1:1) xsd:string
    has_name: str|None=None                 # (0:1) xsd:string

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())
     
    @field_validator('has_coding_system_and_version', 'has_identifier', mode='after')  
    @classmethod
    def validate_string(cls, value: str) -> str:
        if not is_valid_string(value):
            raise ValueError(f'{value} is not a valid string')
        return value  

    @field_validator('has_name', mode='after')  
    @classmethod
    def validate_string_or_none(cls, value: str|None) -> str|None:
        if value is not None and not is_valid_string(value):
            raise ValueError(f'{value} is not a valid string')
        return value  

    @field_validator('has_coding_system_and_version', mode='after')  
    @classmethod
    def validate_coding_system_and_version(cls, value: str) -> str:
        if value not in CodingSystemList:
            raise ValueError(f'{value} is not an implemented coding system')
        return value  

    # ----------------------------------------------------------------------------------------------------------
    # Public functions
    # ----------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-07-06
    #

    # 
    # Example Terminology:
    #

    # "sphn:hasCode": {
    #     "termid": "SNOMED-CT-74886007",
    #     "iri": "http://snomed.info/id/74886007",
    #     "sourceConceptID": "7e27d80d-8517-4536-8f02-0e557cd80cc2"
    # }

    # 
    # Example Code:
    #

    # "sphn:hasInstitutionCode": {
    #     "id": "dd7b189b01644a9cb9a3270d3fec43a9",
    #     "sphn:hasCodingSystemAndVersion": "UID",
    #     "sphn:hasIdentifier": "CHE-888-888-888",
    #     "sphn:hasName": "University of Switzerland"
    #     "sourceConceptID": "7e27d80d-8517-4536-8f02-0e557cd80cc2"
    # }

    def get_json_dict(self, content: dict|None=None, source_concept_id: str|None=None) -> dict:
        """ 
        Gets the dict for json output (for the special concepts)
        """
        # Checks
        assert content is None or isinstance(content, dict)
        assert source_concept_id is None or is_valid_string(source_concept_id)
        
        assert self.is_complete()

        # Check if it is a Terminology or Code
        if self.has_coding_system_and_version in ['SNOMED-CT','DCM','UCUM','EDAM']:

            # It is a Terminology
    
            # Inline, not a core concept, no reference to separate content description
            json_dict_content_inline = {
                "termid": self.has_coding_system_and_version + "-" + self.has_identifier
            }

            # Check which Terminology
            if self.has_coding_system_and_version == 'SNOMED-CT':
                json_dict_content_inline["iri"] = SNOMED + self.has_identifier

            elif self._has_coding_system_and_version == 'DCM':
                json_dict_content_inline["iri"] = SPHN_DCM + self.has_identifier

            elif self._has_coding_system_and_version == 'UCUM':
                json_dict_content_inline["iri"] = UCUM + self.has_identifier

            elif self._has_coding_system_and_version == 'EDAM':
                json_dict_content_inline["iri"] = EDAM + self.has_identifier

            else:
                # This should never happen
                raise ValueError("Unknown Terminology")

        else:
            # It is a Code

            # Inline, not a core concept, no reference to separate content description
            json_dict_content_inline = {
                "id": f"{self.id}"
            }

            if self.has_coding_system_and_version is not None:
                json_dict_content_inline[f"{SPHN.hasCodingSystemAndVersion.n3(self.sphn_schema.namespace_manager())}"] = self.has_coding_system_and_version

            if self.has_identifier is not None:
                json_dict_content_inline[f"{SPHN.hasIdentifier.n3(self.sphn_schema.namespace_manager())}"] = self.has_identifier

            if self.has_name is not None:
                json_dict_content_inline[f"{SPHN.hasName.n3(self.sphn_schema.namespace_manager())}"] = self.has_name

        if source_concept_id is not None:
            json_dict_content_inline["SourceConceptID"] = source_concept_id

        return json_dict_content_inline

    #
    # Edwin 2026-07-06
    #
    def is_complete(self) -> bool:
        """
        Checks if all mandatory metadata is available
        """

        # result = is_valid_string(self._has_coding_system_and_version) \
        #          and self._has_coding_system_and_version in coding_systems \
        #          and is_valid_string(self._has_identifier) \
        #          and (self._has_name is None or is_valid_string(self._has_name))
        
        result = True

        return result

    #
    # Edwin 2026-07-07
    #
    def is_similar(self, other) -> bool:
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

        # Checking if the coding system is similar
        if self.has_coding_system_and_version != other.has_coding_system_and_version:
            # Not similar
            return False
        
        # Checking if the identifier is similar
        if self.has_identifier != other.has_identifier:
            # Not similar
            return False
        
        # Checking if the name is similar
        if self.has_name != other.has_name:
            # Not similar
            return False

        # Similar
        return True

    # ----------------------------------------------------------------------------------------------------------
    # Private functions
    # ----------------------------------------------------------------------------------------------------------
