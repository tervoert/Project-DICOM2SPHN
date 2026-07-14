"""
sphn_data_release.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNDataRelease class, which represents the SPHN DataRelease concept in the SPHN schema.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from rdflib import URIRef
from .sphn_schema_graph import SPHNSchemaGraph, SPHN
from .tools import is_valid_string, generate_id
from .sphn_data_provider import SPHNDataProvider

#
# The SPHN DataRelease class representing the SPHN DataRelease concept in the SPHN schema.
#
class SPHNDataRelease(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    has_data_provider: SPHNDataProvider                 # (1:1) SPHN DataProvider
    conforms_to: URIRef                                 # (1:1) dcterms:conformsTo URI
    has_extraction_datetime: datetime                   # (1:1) xsd:dateTime

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())
   
    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------


    #
    # Edwin 2025-07-18
    #

    # "sphn:DataRelease": { 
    #     "id": "1666216800", 
    #     "sphn:hasExtractionDateTime": "2022-10-20T12:00:00.000" 
    # }
    
    #     Note: "conforms to" is ignored?

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

        if self.has_extraction_datetime is not None:
            json_dict[f"{SPHN.hasExtractionDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_extraction_datetime.isoformat(timespec='milliseconds')
            #.strftime("%Y-%m-%dT%H:%M:%S")

        return json_dict

    #
    # Edwin 2026-07-13
    #
    def is_complete(self):
        """
        Checks if all mandatory metadata is available
        """

        # result = isinstance(self.has_data_provider, SPHNDataProvider) \
        #          and self.has_data_provider.is_complete() \
        #          and is_valid_string(self.conforms_to) \
        #          and isinstance(self.has_extraction_datetime, datetime)
    
        result = self.has_data_provider.is_complete()
        
        return result
    
    #
    # Edwin 2026-07-13
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

        # Checking if the conforms to is similar
        if self.conforms_to != other.conforms_to:
            # Not similar
            return False
        
        # Checking if the extraction date time is similar
        if self.has_extraction_datetime != other.has_extraction_datetime:
            # Not similar
            return False

        # Checking if the data provider is similar
        if not isinstance(other.has_data_provider, type(self.has_data_provider)):
            # Not similar
            return False
        if self.has_data_provider is not None \
           and not self.has_data_provider.is_similar(other.has_data_provider):
            # Not similar
            return False

        # Similar
        return True

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
