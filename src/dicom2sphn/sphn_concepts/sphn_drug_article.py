"""
sphn_drug_article.py:
    Part of the example dicom2sphn package. 
    It contains the SPHNDrugArticle class, which represents the SPHN Drug Article concept in the SPHN schema.
"""

from pydantic import Field, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import already_in_list, are_similar_lists, generate_id, is_valid_string
from .sphn_code import SPHNCode
from .sphn_concept import SPHNConcept
from .sphn_pharmaceutical_dose_form import SPHNPharmaceuticalDoseForm
from .sphn_source_system import SPHNSourceSystem


#
# The SPHN Drug Article class representing the SPHN Drug Article concept in the SPHN schema.
#
class SPHNDrugArticle(SPHNConcept):

    has_code: SPHNCode|None=None                                        # (0:1) SPHN Code
    has_name: str|None=None                                             # (0:1) xsd:string
    has_manufactured_dose_form: SPHNPharmaceuticalDoseForm|None=None    # (0:1) xsd:string
    has_source_system_list: list[SPHNSourceSystem]                      # (1:n) SPHN SourceSystem (list)

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())
     
    @field_validator('has_name', mode='after')
    @classmethod
    def validate_string(cls, value: str|None=None) -> str|None:
        if value is not None and not is_valid_string(value):
            raise ValueError(f"SPHN 'has_name' value '{value}' is not a valid string")
        return value

    @field_validator('has_source_system_list', mode='after')  
    @classmethod
    def validate_source_system_list(cls, value: list[SPHNSourceSystem]) -> list[SPHNSourceSystem]:
        if len(value) == 0:
            raise ValueError("SPHN 'has_source_system' list must be a non-empty list.")
        if not all(isinstance(item, SPHNSourceSystem) for item in value):
            raise TypeError("One or more items in the SPHN 'has_source_system' list are not SPHN SourceSystem instances.")
        return value


    # ----------------------------------------------------------------------------------------------------------
    # Public functions
    # ----------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-05
    #
    def add_sphn_source_system(self, source_system: SPHNSourceSystem) -> None:
        """ 
        Adds the source_system to the list
        """
        # Checks
        assert isinstance(source_system, SPHNSourceSystem)

        if not already_in_list(source_system, self.has_source_system_list):
            self.has_source_system_list.append(source_system)


    #
    # Edwin 2026-08-13
    #
    # It is not a Core Concept
    def get_json_dict(self, content: dict, source_concept_id: str|None=None) -> dict:
        """ 
        Gets the dict for json output
        """
        # Checks
        assert isinstance(content, dict)
        assert source_concept_id is None or is_valid_string(source_concept_id)        

        # Inline, not a core concept, no reference to separate content description
        json_dict_content_inline = {
            "id": f"{self.id}"
        }

        if self.has_name is not None:
            json_dict_content_inline[f"{SPHN.hasName.n3(self.sphn_schema.namespace_manager())}"] = self.has_name

        if self.has_code is not None:
            json_dict_content_inline[f"{SPHN.hasCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_code.get_json_dict(content, self.id)

        if self.has_manufactured_dose_form is not None:
            json_dict_content_inline[f"{SPHN.hasManufacturedDoseForm.n3(self.sphn_schema.namespace_manager())}"] = self.has_manufactured_dose_form.get_json_dict(content, self.id)

        if self.has_source_system_list is not None and len(self.has_source_system_list)>0:
            json_dict_content_inline[f"{SPHN.hasSourceSystem.n3(self.sphn_schema.namespace_manager())}"] = [source_system.get_json_dict(content, self.id) for source_system in self.has_source_system_list]

        return json_dict_content_inline

    
    #
    # Edwin 2026-08-13
    #
    def is_similar(self, other) -> bool :
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_name == other.has_name \
            and ((self.has_manufactured_dose_form is None and other.has_manufactured_dose_form is None) \
                 or (self.has_manufactured_dose_form is not None and other.has_manufactured_dose_form is not None \
                     and self.has_manufactured_dose_form.is_similar(other.has_manufactured_dose_form))) \
            and ((self.has_code is None and other.has_code is None) \
                 or (self.has_code is not None and other.has_code is not None \
                     and self.has_code.is_similar(other.has_code))) \
            and are_similar_lists(self.has_source_system_list, other.has_source_system_list)

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
