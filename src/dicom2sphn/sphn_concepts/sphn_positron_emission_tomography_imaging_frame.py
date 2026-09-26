"""
sphn_positron_emission_tomography_imaging_frame.py: 
    Part of the example dicom2sphn package.
    It contains the SPHNPositronEmissionTomographyImagingFrame class, which represents the SPHN Positron Emission Tomography Imaging Frame concept in the SPHN schema.
"""

from datetime import datetime
from typing import Self

from pydantic import Field, ValidationInfo, field_validator, model_validator

from ..sphn_schema_graph import SPHN, SPHN_IND, SPHNSchemaGraph
from ..tools import (
    already_in_list,
    are_similar_lists,
    generate_id,
    is_clean_string,
    is_valid_string,
)
from .sphn_anatomical_projection import SPHNAnatomicalProjection
from .sphn_body_site import SPHNBodySite
from .sphn_code import SPHNCode
from .sphn_data_compression_algorithm import SPHNDataCompressionAlgorithm
from .sphn_image_dimensions import SPHNImageDimensions
from .sphn_imaging_frame import SPHNImagingFrame
from .sphn_imaging_metric import SPHNImagingMetric
from .sphn_physiologic_state import SPHNPhysiologicState
from .sphn_radiopharmaceutical_administration_event import (
    SPHNRadiopharmaceuticalAdministrationEvent,
)
from .sphn_synchronization import SPHNSynchronization


#
# The SPHNPositronEmissionTomographyImagingFrame class representing the SPHN Positron Emission Tomography Imaging Frame concept in the SPHN schema.
#
class SPHNPositronEmissionTomographyImagingFrame(SPHNImagingFrame):

    has_start_datetime: datetime|None=None                              # (0:1) xsd:dateTime                # Not implemented 
    has_end_datetime: datetime|None=None                                # (0:1) xsd:dateTime                # Not in DICOM
    has_image_dimensions: SPHNImageDimensions|None=None                 # (0:1) SPHN ImageDimensions
    has_content_qualification: str|None=None                            # (0:1) SPHN ImagingFrame_contentQualification ValueSet member
    has_imaging_metric: SPHNImagingMetric|None=None                     # (0:1) SPHN ImagingMetric          # Not implemented
    has_anatomical_projection: SPHNAnatomicalProjection|None=None       # (0:1) SPHN AnatomicalProjection   # Not implemented
    has_type_list: list[str]|None=None                                  # (0:n) SPHN ImagingFrame_type ValueSet member (list)
    has_body_site_list: list[SPHNBodySite]|None=None                    # (0:n) SPHN BodySite (list)
    has_algorithm_list: list[SPHNDataCompressionAlgorithm]|None=None    # (0:n) SPHN DataCompressionAlgorithm (list)

    has_radiopharmaceutical_administration_event: SPHNRadiopharmaceuticalAdministrationEvent|None=None  # (0:1) SPHN RadiopharmaceuticalAdministrationEvent
    has_subject_physiologic_state: SPHNPhysiologicState|None=None                                       # (0:1) SPHN PhysiologicState
    has_cardiac_procedural_state_code: SPHNCode|None=None                                               # (0:1) SPHN Code
    has_synchronization: SPHNSynchronization|None=None                                                  # (0:1) SPHN Synchronisation

    # Additional Properties
    # image_position = None
    # image_position_ucum_unit = None
    # image_orientation_row = None
    # image_orientation_column = None
    # image_orientation_normal = None
    # slice_location = None

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())


    @field_validator('has_body_site_list', mode='after')  
    @classmethod
    def validate_body_site_list(cls, value: list[SPHNBodySite]|None, info: ValidationInfo) -> list[SPHNBodySite]|None:
        if value is not None:
            if len(value) == 0:
                raise ValueError("SPHN 'has_body_site' list must be a non-empty list or None")
            if not all(isinstance(item, SPHNBodySite) for item in value):
                raise TypeError("One or more items in SPHN 'has_body_site' list are not SPHN BodySite instances")
        return value

    @field_validator('has_algorithm_list', mode='after')  
    @classmethod
    def validate_algorithm_list(cls, value: list[SPHNDataCompressionAlgorithm]|None, info: ValidationInfo) -> list[SPHNDataCompressionAlgorithm]|None:
        if value is not None:
            if len(value) == 0:
                raise ValueError("SPHN 'has_algorithm' list must be a non-empty list or None")
            if not all(isinstance(item, SPHNDataCompressionAlgorithm) for item in value):
                raise TypeError("One or more items in SPHN 'has_algorithm' list are not SPHN DataCompressionAlgorithm instances.")
        return value

    @model_validator(mode='after')
    def validate_imaging_frame_type_list(self) -> Self:
        if self.has_type_list is not None:
            if len(self.has_type_list) == 0:
                raise ValueError("SPHN 'has_type' list must be a non-empty list or None")
            if not all(is_clean_string(item) for item in self.has_type_list):
                raise ValueError("One or more items in SPHN 'has_type' list are not valid clean strings")
            if not all(self.sphn_schema.is_sphn_imaging_frame_type_value_set_member(item) for item in self.has_type_list):
                raise ValueError("One or more items in SPHN 'has_type' list are not members of the SPHN 'ImagingFrame_type' value set")
        return self

    @model_validator(mode='after')
    def validate_content_qualification_value_set_member(self) -> Self:
        if self.has_content_qualification is not None:
            if not is_clean_string(self.has_content_qualification):
                raise ValueError("SPHN 'has_content_qualification' value is not a valid clean string")
            if not self.sphn_schema.is_sphn_imaging_frame_content_qualification_value_set_member(self.has_content_qualification):
                raise ValueError(f"SPHN 'has_content_qualification' value: '{self.has_content_qualification}' is not a member of the SPHN 'ImagingFrame_contentQualification' value set")
        return self

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-05
    # (Not used)
    def add_image_type(self, image_type: str) -> None:
        """ 
        Adds the type to the list
        """
        # Checks
        assert is_clean_string(image_type)
        assert self.sphn_schema.is_sphn_imaging_frame_type_value_set_member(image_type)

        if self.has_type_list is None:
            self.has_type_list = [image_type]
        else:
            if image_type not in self.has_type_list:
                self.has_type_list.append(image_type)


    #
    # Edwin 2026-08-05
    # (Not used)
    def add_sphn_body_site(self, body_site: SPHNBodySite) -> None:
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
    def add_sphn_data_compression_algorithm(self, data_compression_algorithm: SPHNDataCompressionAlgorithm) -> None:
        """ 
        Adds the data_compression_algorithm to the list
        """
        # Checks
        assert isinstance(data_compression_algorithm, SPHNDataCompressionAlgorithm)

        if self.has_algorithm_list is None:
            self.has_algorithm_list = [data_compression_algorithm]
        else:
            if not already_in_list(data_compression_algorithm, self.has_algorithm_list):
                self.has_algorithm_list.append(data_compression_algorithm)


    #
    # Edwin 2026-08-13
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

        if self.has_start_datetime is not None:
            json_dict_content_inline[f"{SPHN.hasStartDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_start_datetime.isoformat(timespec='milliseconds')

        if self.has_end_datetime is not None:
            json_dict_content_inline[f"{SPHN.hasEndDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_end_datetime.isoformat(timespec='milliseconds')

        if self.has_type_list is not None and len(self.has_type_list)>0:
            json_dict_content_inline[f"{SPHN.hasType.n3(self.sphn_schema.namespace_manager())}"] = [{"iri": SPHN_IND + image_type} for image_type in self.has_type_list]

        if self.has_image_dimensions is not None:
            json_dict_content_inline[f"{SPHN.hasImageDimensions.n3(self.sphn_schema.namespace_manager())}"] = self.has_image_dimensions.get_json_dict(content, self.id)

        if self.has_body_site_list is not None and len(self.has_body_site_list)>0:
            json_dict_content_inline[f"{SPHN.hasBodySite.n3(self.sphn_schema.namespace_manager())}"] = [body_site.get_json_dict(content, self.id) for body_site in self.has_body_site_list]

        if self.has_algorithm_list is not None and len(self.has_algorithm_list)>0:
            json_dict_content_inline[f"{SPHN.hasAlgorithm.n3(self.sphn_schema.namespace_manager())}"] = [algorithm.get_json_dict(content, self.id) for algorithm in self.has_algorithm_list]

        if self.has_content_qualification is not None:
            json_dict_content_inline[f"{SPHN.hasContentQualification.n3(self.sphn_schema.namespace_manager())}"] = {
                "iri": SPHN_IND + self.has_content_qualification
            }

        if self.has_imaging_metric is not None:
            json_dict_content_inline[f"{SPHN.hasImagingMetric.n3(self.sphn_schema.namespace_manager())}"] = self.has_imaging_metric.get_json_dict(content, self.id)

        if self.has_anatomical_projection is not None:
            json_dict_content_inline[f"{SPHN.hasAnatomicalProjection.n3(self.sphn_schema.namespace_manager())}"] = self.has_anatomical_projection.get_json_dict(content, self.id)

        # Added
        if self.has_radiopharmaceutical_administration_event is not None:
            json_dict_content_inline[f"{SPHN.hasRadiopharmaceuticalAdministrationEvent.n3(self.sphn_schema.namespace_manager())}"] = self.has_radiopharmaceutical_administration_event.get_json_dict(content, self.id)

        if self.has_subject_physiologic_state is not None:
            json_dict_content_inline[f"{SPHN.hasSubjectPhysiologicState.n3(self.sphn_schema.namespace_manager())}"] = self.has_subject_physiologic_state.get_json_dict(content, self.id)

        if self.has_cardiac_procedural_state_code is not None:
            json_dict_content_inline[f"{SPHN.hasCardiacProceduralStateCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_cardiac_procedural_state_code.get_json_dict(content, self.id)

        if self.has_synchronization is not None:
            json_dict_content_inline[f"{SPHN.hasSynchronization.n3(self.sphn_schema.namespace_manager())}"] = self.has_synchronization.get_json_dict(content, self.id)

        # Return the JSON description
        return json_dict_content_inline


    #
    # Edwin 2026-08-13
    #
    def is_similar(self, other, rel_tol: float=1e-4, abs_tol: float=1e-9) -> bool:
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.has_start_datetime == other.has_start_datetime \
            and self.has_end_datetime == other.has_end_datetime \
            and self.has_content_qualification == other.has_content_qualification \
            and sorted(self.has_type_list) == sorted(other.has_type_list) \
            and ((self.has_image_dimensions is None and other.has_image_dimensions is None) \
                 or (self.has_image_dimensions is not None and other.has_image_dimensions is not None \
                     and self.has_image_dimensions.is_similar(other.has_image_dimensions))) \
            and ((self.has_imaging_metric is None and other.has_imaging_metric is None) \
                 or (self.has_imaging_metric is not None and other.has_imaging_metric is not None \
                     and self.has_imaging_metric.is_similar(other.has_imaging_metric))) \
            and ((self.has_anatomical_projection is None and other.has_anatomical_projection is None) \
                 or (self.has_anatomical_projection is not None and other.has_anatomical_projection is not None \
                     and self.has_anatomical_projection.is_similar(other.has_anatomical_projection))) \
            and ((self.has_body_site_list is None and other.has_body_site_list is None) \
                 or (self.has_body_site_list is not None and other.has_body_site_list is not None \
                     and are_similar_lists(self.has_body_site_list, other.has_body_site_list))) \
            and ((self.has_algorithm_list is None and other.has_algorithm_list is None) \
                 or (self.has_algorithm_list is not None and other.has_algorithm_list is not None \
                     and are_similar_lists(self.has_algorithm_list, other.has_algorithm_list))) \
            and ((self.has_radiopharmaceutical_administration_event is None and other.has_radiopharmaceutical_administration_event is None) \
                 or (self.has_radiopharmaceutical_administration_event is not None and other.has_radiopharmaceutical_administration_event is not None \
                     and self.has_radiopharmaceutical_administration_event.is_similar(other.has_radiopharmaceutical_administration_event))) \
            and ((self.has_subject_physiologic_state is None and other.has_subject_physiologic_state is None) \
                 or (self.has_subject_physiologic_state is not None and other.has_subject_physiologic_state is not None \
                     and self.has_subject_physiologic_state.is_similar(other.has_subject_physiologic_state))) \
            and ((self.has_cardiac_procedural_state_code is None and other.has_cardiac_procedural_state_code is None) \
                 or (self.has_cardiac_procedural_state_code is not None and other.has_cardiac_procedural_state_code is not None \
                     and self.has_cardiac_procedural_state_code.is_similar(other.has_cardiac_procedural_state_code))) \
            and ((self.has_synchronization is None and other.has_synchronization is None) \
                 or (self.has_synchronization is not None and other.has_synchronization is not None \
                     and self.has_synchronization.is_similar(other.has_synchronization)))

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------

