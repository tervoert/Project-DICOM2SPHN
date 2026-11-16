"""
sphn_radiopharmaceutical.py:
    Part of the example dicom2sphn package. 
    It contains the SPHNRadiopharmaceutical class, which represents the SPHN Radiopharmaceutical concept in the SPHN schema.
"""

from pydantic import Field, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_concept import UnorderedList
from .sphn_drug import SPHNDrug
from .sphn_drug_article import SPHNDrugArticle
from .sphn_quantity import SPHNQuantity
from .sphn_radionuclide import SPHNRadionuclide
from .sphn_source_system import SPHNSourceSystem
from .sphn_substance import SPHNSubstance


#
# The SPHN Radiopharmaceutical class representing the SPHN Radiopharmaceutical concept in the SPHN schema.
#
class SPHNRadiopharmaceutical(SPHNDrug):

    has_article: SPHNDrugArticle|None=None                              # (0:1) SPHN Drug Article
    has_quantity: SPHNQuantity|None=None                                # (0:1) SPHN Quantity
    has_radionuclide_list: list[SPHNRadionuclide]|None=None             # (0:n) SPHN Radionuclide (list)
    has_active_ingredient_list: list[SPHNSubstance]|None=None           # (0:n) SPHN Substance (list)
    has_inactive_ingredient_list: list[SPHNSubstance]|None=None         # (0:n) SPHN Substance (list)
    has_source_system_list: list[SPHNSourceSystem]                      # (1:n) SPHN SourceSystem (list)

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())

    @field_validator('has_radionuclide_list', mode='after')  
    @classmethod
    def validate_radionuclide_list(cls, value: list[SPHNRadionuclide]|None=None) -> list[SPHNRadionuclide]|None:
        if value is not None:
            if len(value) == 0:
                raise ValueError("SPHN 'has_radionuclide_list' must be a non-empty list or None.")
            if not all(isinstance(item, SPHNRadionuclide) for item in value):
                raise TypeError("One or more items in the 'has_radionuclide_list' are not SPHN Radionuclide instances.")
        return value

    @field_validator('has_active_ingredient_list', mode='after')  
    @classmethod
    def validate_active_ingredient_list(cls, value: list[SPHNSubstance]|None=None) -> list[SPHNSubstance]|None:
        if value is not None:
            if len(value) == 0:
                raise ValueError("SPHN 'has_active_ingredient_list' must be a non-empty list or None.")
            if not all(isinstance(item, SPHNSubstance) for item in value):
                raise TypeError("One or more items in the 'has_active_ingredient_list' are not SPHN Substance instances.")
        return value

    @field_validator('has_inactive_ingredient_list', mode='after')  
    @classmethod
    def validate_inactive_ingredient_list(cls, value: list[SPHNSubstance]|None=None) -> list[SPHNSubstance]|None:
        if value is not None:
            if len(value) == 0:
                raise ValueError("SPHN 'has_inactive_ingredient_list' must be a non-empty list or None.")
            if not all(isinstance(item, SPHNSubstance) for item in value):
                raise TypeError("One or more items in the 'has_inactive_ingredient_list' are not SPHN Substance instances.")
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

    #
    # Edwin 2026-10-19
    #
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
                    self.has_quantity, 
                    self.has_article, 
                    UnorderedList(self.has_radionuclide_list), 
                    UnorderedList(self.has_active_ingredient_list), 
                    UnorderedList(self.has_inactive_ingredient_list), 
                    UnorderedList(self.has_source_system_list)
                ) == (
                    other.has_quantity, 
                    other.has_article, 
                    UnorderedList(other.has_radionuclide_list), 
                    UnorderedList(other.has_active_ingredient_list), 
                    UnorderedList(other.has_inactive_ingredient_list), 
                    UnorderedList(other.has_source_system_list)
                )

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

        if source_system not in self.has_source_system_list:
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

        if self.has_active_ingredient_list is not None and len(self.has_active_ingredient_list)>0:
            json_dict_content_inline[f"{SPHN.hasActiveIngredient.n3(self.sphn_schema.namespace_manager())}"] = [active_ingredient.get_json_dict(content, self.id) for active_ingredient in self.has_active_ingredient_list]

        if self.has_article is not None:
            json_dict_content_inline[f"{SPHN.hasArticle.n3(self.sphn_schema.namespace_manager())}"] = self.has_article.get_json_dict(content, self.id)

        if self.has_inactive_ingredient_list is not None and len(self.has_inactive_ingredient_list)>0:
            json_dict_content_inline[f"{SPHN.hasInactiveIngredient.n3(self.sphn_schema.namespace_manager())}"] = [inactive_ingredient.get_json_dict(content, self.id) for inactive_ingredient in self.has_inactive_ingredient_list]

        if self.has_quantity is not None:
            json_dict_content_inline[f"{SPHN.hasQuantity.n3(self.sphn_schema.namespace_manager())}"] = self.has_quantity.get_json_dict(content, self.id)

        if self.has_radionuclide_list is not None and len(self.has_radionuclide_list)>0:
            json_dict_content_inline[f"{SPHN.hasRadionuclide.n3(self.sphn_schema.namespace_manager())}"] = [radionuclide.get_json_dict(content, self.id) for radionuclide in self.has_radionuclide_list]

        if self.has_source_system_list is not None and len(self.has_source_system_list)>0:
            json_dict_content_inline[f"{SPHN.hasSourceSystem.n3(self.sphn_schema.namespace_manager())}"] = [source_system.get_json_dict(content, self.id) for source_system in self.has_source_system_list]

        return json_dict_content_inline

