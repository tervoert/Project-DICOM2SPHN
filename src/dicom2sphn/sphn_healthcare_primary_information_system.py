"""
sphn_healthcare_primary_information_system.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNHealthcarePrimaryInformationSystem class, which represents the SPHN HealthcarePrimaryInformationSystem concept in the SPHN schema.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from .sphn_schema_graph import SPHNSchemaGraph, SPHN
from .tools import is_valid_string, generate_id
from .sphn_code import SPHNCode
#
# The SPHN HealthcarePrimaryInformationSystem class representing the SPHN HealthcarePrimaryInformationSystem concept in the SPHN schema.
#
class SPHNHealthcarePrimaryInformationSystem(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    has_name: str|None=None                           # (0:1) xsd:string
    has_code: SPHNCode|None=None                      # (0:1) SPHN Code

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())

    @field_validator('has_name', mode='after')  
    @classmethod
    def validate_string_or_none(cls, value: str|None) -> str|None:
        if value is not None and not is_valid_string(value):
            raise ValueError(f'{value} is not a valid string')
        return value  

    # ----------------------------------------------------------------------------------------------------------
    # Public functions
    # ----------------------------------------------------------------------------------------------------------


    #
    # Edwin 2026-07-14
    #
    def get_json_dict(self, content: dict|None=None, source_concept_id: str|None=None) -> dict:
        """ 
        Gets the dict for json output
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

        if self.has_code is not None:
            json_dict_content_inline[f"{SPHN.hasCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_code.get_json_dict(content, self.id)

        # Return the JSON description of the reference to the instance
        return json_dict_content_inline

    #
    # Edwin 2026-07-14
    #
    # Old, not used
    #
    def get_json_dict_old(self, content: dict|None=None, source_concept_id: str|None=None) -> dict:
        """ 
        Gets the dict for json output
        """
        # Checks
        assert content is None or isinstance(content, dict)
        assert source_concept_id is None or is_valid_string(source_concept_id)        
        
        assert self.is_complete()

        # Part 1: Create the JSON description of the reference to the instance
        
        json_dict_ref = {
            "id": f"{self.id}"
        }

        # Part 2: Create the JSON description of the instance for the 'content'

        json_dict_content = {
            "id": f"{self.id}"
        }

        if self.has_name is not None:
            json_dict_content[f"{SPHN.hasName.n3(self.sphn_schema.namespace_manager())}"] = self.has_name

        if self._has_code is not None:
            json_dict_content[f"{SPHN.hasCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_code.get_json_dict(content, self.id)

        # subject = <prefix:classname>
        subject = f"{SPHN.HealthcarePrimaryInformationSystem.n3(self.sphn_schema.namespace_manager())}"
        
        # Check if 'subject'-list already exists in the JSON 'content'
        if subject in content:
            # 'Subject'-list does exist in the JSON 'content'
            # Check if instance JSON description is already in the 'subject'-list in the JSON 'content'
            subject_list = content[subject]
            for item_dict in subject_list:
                if "id" in item_dict and item_dict["id"] == self.id:
                    # Already in the 'subject'-list in 'content', we don't add it
                    break
            else:
                # Not in the 'subject'-list in 'content', so we can add it
                content[subject].append(json_dict_content)

        else:
            # 'Subject'-list does not exist in the JSON 'content'
            content[subject] = [json_dict_content]

        # Return the JSON description of the reference to the instance
        return json_dict_ref

    #
    # Edwin 2026-07-14
    #
    def is_complete(self) -> bool:
        """
        Checks if all mandatory metadata is available
        """

        # result = (self.has_name is None
        #               or is_valid_string(self.has_name)) \
        #          and (self.has_code is None 
        #               or (isinstance(self.has_code, SPHNCode) 
        #                   and self.has_code.is_complete()))

        result = self.has_code is None or self.has_code.is_complete()

        return result

    #
    # Edwin 2026-07-14
    #
    def is_similar(self, other) -> bool:
        """
        Compare this instance with another instance of the same class
        """

        assert self.is_complete()

        # Check if type is similar
        if not isinstance(other, type(self)):
            # Not similar
            return False

        assert other.is_complete()

        # Checking if the name is similar
        if self.has_name != other.has_name:
            # Not the same
            return False

        # Checking if the code is similar
        if not isinstance(other.has_code, type(self.has_code)):
            # Not similar
            return False
        if self._has_code is not None \
             and not self.has_code.is_similar(other.has_code):
            # Not the same
            return False

        return True

    # ----------------------------------------------------------------------------------------------------------
    # Private functions
    # ----------------------------------------------------------------------------------------------------------
