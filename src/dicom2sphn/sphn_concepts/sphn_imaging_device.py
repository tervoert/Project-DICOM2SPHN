"""
sphn_imaging_device.py: 
    Part of the example dicom2sphn package.
    It contains the SPHNImagingDevice class, which represents the SPHN ImagingDevice concept in the SPHN schema.
"""

from pydantic import Field, ValidationInfo, field_validator

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_code import SPHNCode
from .sphn_concept import SPHNConcept
from .sphn_software import SPHNSoftware


#
# The SPHN ImagingDevice class representing the SPHN ImagingDevice concept in the SPHN schema.
#
class SPHNImagingDevice(SPHNConcept):

    has_type_code: SPHNCode|None=None                 # (0:1) SPHN Code or SPHN Terminology   # Not in DICOM
    has_product_code: SPHNCode|None=None              # (0:1) SPHN Code or SPHN Terminology   # Not in DICOM
    has_software_list: list[SPHNSoftware]|None=None   # (0:n) SPHN Software (list)

    has_manufacturer_name: str|None=None              # (0:1) xsd:string
    has_model_name: str|None=None                     # (0:1) xsd:string

    # Not part of the SPHN schema
    has_serial_number: str|None=None                  # (0:1) xsd:string

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())


    @field_validator('has_software_list', mode='after')
    @classmethod
    def validate_list_of_completeness_or_none(cls, value: list[SPHNSoftware]|None, info: ValidationInfo) -> list[SPHNSoftware]|None:
        if value is not None:
            if len(value) == 0:
                raise ValueError('SPHN has_software_list must be a non-empty list or None')
            if not all(isinstance(item, SPHNSoftware) for item in value):
                raise TypeError('One or more items in SPHN has_software_list are not SPHNSoftware instances')
        return value

    @field_validator('has_manufacturer_name', 'has_model_name', 'has_serial_number', mode='after')
    @classmethod
    def validate_string_or_none(cls, value: str|None, info: ValidationInfo) -> str|None:
        if value is not None and not is_valid_string(value):
            raise ValueError(f"SPHN {info.field_name} string value '{value}' is not a valid string")
        return value

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-08-05
    #
    def add_sphn_software(self, software: SPHNSoftware) -> None:
        """ 
        Adds the sphn:Software to the list
        """
        # Checks
        assert isinstance(software, SPHNSoftware)

        if self.has_software_list is None:
            self.has_software_list = [software]
        else:
            if software not in self.has_software_list:
                self.has_software_list.append(software)


    #
    # Edwin 2026-08-05
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

        if self.has_type_code is not None:
            json_dict_content_inline[f"{SPHN.hasTypeCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_type_code.get_json_dict(content, self.id)

        if self.has_product_code is not None:
            json_dict_content_inline[f"{SPHN.hasProductCode.n3(self.sphn_schema.namespace_manager())}"] = self.has_product_code.get_json_dict(content, self.id)

        if self.has_manufacturer_name is not None:
            json_dict_content_inline[f"{SPHN.hasManufacturerName.n3(self.sphn_schema.namespace_manager())}"] = self.has_manufacturer_name

        if self.has_model_name is not None:
            json_dict_content_inline[f"{SPHN.hasModelName.n3(self.sphn_schema.namespace_manager())}"] = self.has_model_name

        if self.has_software_list is not None and len(self.has_software_list)>0:
            json_dict_content_inline[f"{SPHN.hasSoftware.n3(self.sphn_schema.namespace_manager())}"] = [software.get_json_dict(content, self.id) for software in self.has_software_list]

        # Return the JSON description
        return json_dict_content_inline


    #
    # Edwin 2026-10-19
    #
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
                    self.has_type_code, 
                    self.has_product_code, 
                    self.has_manufacturer_name, 
                    self.has_model_name, 
                    self.has_serial_number, 
                    sorted(self.has_software_list) if self.has_software_list is not None else None
                ) == (
                    other.has_type_code, 
                    other.has_product_code, 
                    other.has_manufacturer_name, 
                    other.has_model_name, 
                    other.has_serial_number, 
                    sorted(other.has_software_list) if other.has_software_list is not None else None
                )

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------



