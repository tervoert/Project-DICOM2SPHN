"""
sphn_imaging_procedure.py: 
    Part of the example dicom2sphn package.
    It contains the SPHNImagingProcedure class, which represents the SPHN ImagingProcedure concept in the SPHN schema.
"""

from datetime import datetime

from pydantic import Field, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import already_in_list, are_similar_lists, generate_id, is_valid_string
from .sphn_administrative_case import SPHNAdministrativeCase
from .sphn_administrative_sex import SPHNAdministrativeSex
from .sphn_age import SPHNAge
from .sphn_body_height import SPHNBodyHeight
from .sphn_body_mass_index import SPHNBodyMassIndex
from .sphn_body_site import SPHNBodySite
from .sphn_body_weight import SPHNBodyWeight
from .sphn_code import SPHNCode
from .sphn_concept import SPHNConcept
from .sphn_imaging_series import SPHNImagingSeries
from .sphn_intent import SPHNIntent
from .sphn_source_system import SPHNSourceSystem
from .sphn_subject_pseudo_identifier import SPHNSubjectPseudoIdentifier


#
# The SPHN ImagingProcedure class representing the SPHN ImagingProcedure concept in the SPHN schema.
#
class SPHNImagingProcedure(SPHNConcept):
    
    has_start_datetime: datetime|None=None                              # (0:1) xsd:dateTime
    has_end_datetime: datetime|None=None                                # (0:1) xsd:dateTime                # Not in DICOM
    has_description: str|None=None                                      # (0:1) xsd:string

    has_subject_age: SPHNAge|None=None                                  # (0:1) SPHN Age
    has_subject_body_height: SPHNBodyHeight|None=None                   # (0:1) SPHN BodyHeight
    has_subject_body_weight: SPHNBodyWeight|None=None                   # (0:1) SPHN BodyWeight
    has_subject_body_mass_index: SPHNBodyMassIndex|None=None            # (0:1) SPHN BodyMassIndex
    has_subject_administrative_sex: SPHNAdministrativeSex|None=None     # (0:1) SPHN AdministrativeSex
    has_subject_pregnancy_status_code: SPHNCode|None=None               # (0:1) SPHN Code or SPHN Terminology
    has_intent: SPHNIntent|None=None                                    # (0:1) SPHN Intent                 # Not Implemented
    
    has_body_site_list: list[SPHNBodySite]|None=None                    # (0:n) SPHN BodySite (list)        # Not Implemented
    has_code_list: list[SPHNCode]                                       # (1:n) SPHN Code or SPHN Terminology (list)
    has_imaging_series_list: list[SPHNImagingSeries]|None=None          # (0:n) SPHN ImagingSeries (list)

    has_administrative_case: SPHNAdministrativeCase|None=None           # (0:1) SPHN AdministrativeCase     # Not Implemented

    has_subject_pseudo_identifier: SPHNSubjectPseudoIdentifier          # (1:1) SPHN Subject Pseudo Identifier
    has_source_system_list: list[SPHNSourceSystem]                      # (1:n) SPHN SourceSystem (list)

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())


    @field_validator('has_description', mode='after')
    @classmethod
    def validate_string_or_none(cls, value: str|None) -> str|None:
        if value is not None and not is_valid_string(value):
            raise ValueError(f"SPHN 'has_description' value '{value}' is not a valid string")
        return value  

    @field_validator('has_body_site_list', mode='after')
    @classmethod
    def validate_body_site_list(cls, value: list[SPHNBodySite]|None) -> list[SPHNBodySite]|None:
        if value is not None:
            if len(value) == 0:
                raise ValueError("SPHN 'has_body_site_list' must be a non-empty list or None")
            if not all(isinstance(item, SPHNBodySite) for item in value):
                raise TypeError("One or more items in 'has_body_site_list' are not SPHN BodySite instances")
        return value

    @field_validator('has_code_list', mode='after')
    @classmethod
    def validate_code_list(cls, value: list[SPHNCode]) -> list[SPHNCode]:
        if len(value) == 0:
            raise ValueError("SPHN 'has_code_list' must be a non-empty list")
        if not all(isinstance(item, SPHNCode) for item in value):
            raise TypeError("One or more items in 'has_code_list' are not SPHN Code instances")
        return value

    @field_validator('has_imaging_series_list', mode='after')
    @classmethod
    def validate_imaging_series_list(cls, value: list[SPHNImagingSeries]|None) -> list[SPHNImagingSeries]|None:
        if value is not None:
            if len(value) == 0:
                raise ValueError("SPHN 'has_imaging_series_list' must be a non-empty list or None")
            if not all(isinstance(item, SPHNImagingSeries) for item in value):
                raise TypeError("One or more items in 'has_imaging_series_list' are not SPHN ImagingSeries instances")
        return value

    @field_validator('has_source_system_list', mode='after')  
    @classmethod
    def validate_source_system_list(cls, value: list[SPHNSourceSystem]) -> list[SPHNSourceSystem]:
        if len(value) == 0:
            raise ValueError("SPHN 'has_source_system' list must be a non-empty list.")
        if not all(isinstance(item, SPHNSourceSystem) for item in value):
            raise TypeError("One or more items in the SPHN 'has_source_system' list are not SPHN SourceSystem instances.")
        return value

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-05
    # (Not used)
    def add_body_site(self, body_site: SPHNBodySite) -> None:
        """ 
        Adds the body_site to the list
        """
        # Checks
        assert isinstance(body_site, SPHNBodySite)

        if self.has_body_site_list is None:
            self.has_body_site_list = [body_site]
        else:
            if not already_in_list(body_site, self.has_body_site_list):
                self.has_body_site_list.append(body_site)


    #
    # Edwin 2026-08-05
    # (Not used)
    def add_code(self, code: SPHNCode) -> None:
        """ 
        Adds the code to the list
        """
        # Checks
        assert isinstance(code, SPHNCode)

        if not already_in_list(code, self.has_code_list):
            self.has_code_list.append(code)


    #
    # Edwin 2026-08-05
    # (Not used)
    def add_imaging_series(self, imaging_series: SPHNImagingSeries) -> None:
        """ 
        Adds the imaging_series to the list
        """
        # Checks
        assert isinstance(imaging_series, SPHNImagingSeries)

        if self.has_imaging_series_list is None:
            self.has_imaging_series_list = [imaging_series]
        else:
            if not already_in_list(imaging_series, self.has_imaging_series_list):
                self.has_imaging_series_list.append(imaging_series)

    #
    # Edwin 2026-08-05
    # (Not used)
    def add_sphn_source_system(self, source_system: SPHNSourceSystem) -> None:
        """ 
        Adds the source_system to the list
        """
        # Checks
        assert isinstance(source_system, SPHNSourceSystem)

        if not already_in_list(source_system, self.has_source_system_list):
            self.has_source_system_list.append(source_system)


    #
    # Edwin 2026-08-05
    #
    # It is a Core Concept
    def get_json_dict(self, content: dict, source_concept_id: str|None=None) -> dict:
        """ 
        Gets the dict for json output
        """
        # Checks
        assert isinstance(content, dict)
        assert source_concept_id is None or is_valid_string(source_concept_id)        
        
        # Part 1: Create the JSON description of the reference to the instance
        
        json_dict_ref = {
            "id": f"{self.id}"
        }

        # Part 2: Create the JSON description of the instance for the 'content'

        json_dict_content = {
            "id": f"{self.id}"
        }

        if self.has_start_datetime is not None:
            json_dict_content[f"{SPHN.hasStartDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_start_datetime.isoformat(timespec='milliseconds')

        if self.has_end_datetime is not None:
            json_dict_content[f"{SPHN.hasEndDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_end_datetime.isoformat(timespec='milliseconds')

        if self.has_description is not None:
            json_dict_content[f"{SPHN.hasDescription.n3(self.sphn_schema.namespace_manager())}"] = self.has_description

        if self.has_subject_age is not None:
            json_dict_content[f"{SPHN.hasSubjectAge.n3(self.sphn_schema.namespace_manager())}"] = self.has_subject_age.get_json_dict(content, self.id)

        if self.has_subject_body_height is not None:
            json_dict_content[f"{SPHN.hasSubjectBodyHeight.n3(self.sphn_schema.namespace_manager())}"] = self.has_subject_body_height.get_json_dict(content, self.id)

        if self.has_subject_body_weight is not None:
            json_dict_content[f"{SPHN.hasSubjectBodyWeight.n3(self.sphn_schema.namespace_manager())}"] = self.has_subject_body_weight.get_json_dict(content, self.id)

        if self.has_subject_body_mass_index is not None:
            json_dict_content[f"{SPHN.hasSubjectBodyMassIndex.n3(self.sphn_schema.namespace_manager())}"] = self.has_subject_body_mass_index.get_json_dict(content, self.id)

        if self.has_subject_administrative_sex is not None:
            json_dict_content[f"{SPHN.hasSubjectAdministrativeSex.n3(self.sphn_schema.namespace_manager())}"] = self.has_subject_administrative_sex.get_json_dict(content, self.id)

        if self.has_subject_pregnancy_status_code is not None:
            json_dict_content[f"{SPHN.hasSubjectPregnancyStatusCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_subject_pregnancy_status_code.get_json_dict(content, self.id)

        if self.has_intent is not None:
            json_dict_content[f"{SPHN.hasIntent.n3(self.sphn_schema.namespace_manager())}"] = self.has_intent.get_json_dict(content, self.id)

        if self.has_body_site_list is not None and len(self.has_body_site_list)>0:
            json_dict_content[f"{SPHN.hasBodySite.n3(self.sphn_schema.namespace_manager())}"] = [body_site.get_json_dict(content, self.id) for body_site in self.has_body_site_list]

        if self.has_code_list is not None and len(self.has_code_list)>0:
            json_dict_content[f"{SPHN.hasCode.n3(self.sphn_schema.namespace_manager())}"] = [code.get_json_dict(content, self.id) for code in self.has_code_list]

        if self.has_imaging_series_list is not None and len(self.has_imaging_series_list)>0:
            json_dict_content[f"{SPHN.hasImagingSeries.n3(self.sphn_schema.namespace_manager())}"] = [imaging_series.get_json_dict(content, self.id) for imaging_series in self.has_imaging_series_list]

        if self.has_administrative_case is not None:
            json_dict_content[f"{SPHN.hasAdministrativeCase.n3(self.sphn_schema.namespace_manager())}"] = self.has_administrative_case.get_json_dict(content, self.id)

        if self.has_source_system_list is not None and len(self.has_source_system_list)>0:
            json_dict_content[f"{SPHN.hasSourceSystem.n3(self.sphn_schema.namespace_manager())}"] = [source_system.get_json_dict(content, self.id) for source_system in self.has_source_system_list]

        # subject = <prefix:classname>
        subject = f"{SPHN.ImagingProcedure.n3(self.sphn_schema.namespace_manager())}"
        
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
    # Edwin 2026-08-05
    #
    def is_similar(self, other: SPHNConcept) -> bool :
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_start_datetime == other.has_start_datetime \
            and self.has_end_datetime == other.has_end_datetime \
            and self.has_description == other.has_description \
            and self.has_subject_pseudo_identifier.is_similar(other.has_subject_pseudo_identifier) \
            and ((self.has_subject_age is None and other.has_subject_age is None) \
                 or (self.has_subject_age is not None and other.has_subject_age is not None \
                     and self.has_subject_age.is_similar(other.has_subject_age))) \
            and ((self.has_subject_body_height is None and other.has_subject_body_height is None) \
                 or (self.has_subject_body_height is not None and other.has_subject_body_height is not None \
                     and self.has_subject_body_height.is_similar(other.has_subject_body_height))) \
            and ((self.has_subject_body_weight is None and other.has_subject_body_weight is None) \
                 or (self.has_subject_body_weight is not None and other.has_subject_body_weight is not None \
                     and self.has_subject_body_weight.is_similar(other.has_subject_body_weight))) \
            and ((self.has_subject_body_mass_index is None and other.has_subject_body_mass_index is None) \
                 or (self.has_subject_body_mass_index is not None and other.has_subject_body_mass_index is not None \
                     and self.has_subject_body_mass_index.is_similar(other.has_subject_body_mass_index))) \
            and ((self.has_subject_administrative_sex is None and other.has_subject_administrative_sex is None) \
                 or (self.has_subject_administrative_sex is not None and other.has_subject_administrative_sex is not None \
                     and self.has_subject_administrative_sex.is_similar(other.has_subject_administrative_sex))) \
            and ((self.has_subject_pregnancy_status_code is None and other.has_subject_pregnancy_status_code is None) \
                 or (self.has_subject_pregnancy_status_code is not None and other.has_subject_pregnancy_status_code is not None \
                     and self.has_subject_pregnancy_status_code.is_similar(other.has_subject_pregnancy_status_code))) \
            and ((self.has_administrative_case is None and other.has_administrative_case is None) \
                 or (self.has_administrative_case is not None and other.has_administrative_case is not None \
                     and self.has_administrative_case.is_similar(other.has_administrative_case))) \
            and ((self.has_intent is None and other.has_intent is None) \
                 or (self.has_intent is not None and other.has_intent is not None \
                     and self.has_intent.is_similar(other.has_intent))) \
            and ((self.has_body_site_list is None and other.has_body_site_list is None) \
                 or (self.has_body_site_list is not None and other.has_body_site_list is not None \
                     and are_similar_lists(self.has_body_site_list, other.has_body_site_list))) \
            and ((self.has_imaging_series_list is None and other.has_imaging_series_list is None) \
                 or (self.has_imaging_series_list is not None and other.has_imaging_series_list is not None \
                     and are_similar_lists(self.has_imaging_series_list, other.has_imaging_series_list))) \
            and are_similar_lists(self.has_code_list, other.has_code_list) \
            and are_similar_lists(self.has_source_system_list, other.has_source_system_list)
            
    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
