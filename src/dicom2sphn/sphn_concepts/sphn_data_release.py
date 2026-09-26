"""
sphn_data_release.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNDataRelease class, which represents the SPHN DataRelease concept in the SPHN schema.
"""
from datetime import datetime

from pydantic import Field
from rdflib import URIRef

from ..sphn_schema_graph import SPHN, SPHNSchemaGraph
from ..tools import generate_id, is_valid_string
from .sphn_concept import SPHNConcept
from .sphn_data_provider import SPHNDataProvider


#
# The SPHN DataRelease class representing the SPHN DataRelease concept in the SPHN schema.
#
class SPHNDataRelease(SPHNConcept):

    has_data_provider: SPHNDataProvider                 # (1:1) SPHN DataProvider
    conforms_to: URIRef                                 # (1:1) dcterms:conformsTo URI
    has_extraction_datetime: datetime                   # (1:1) xsd:dateTime

    sphn_schema: SPHNSchemaGraph
    id: str = Field(default_factory=lambda: generate_id())
   
    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    # Example SPHN DataRelease:

    # "sphn:DataRelease": { 
    #     "id": "1666216800", 
    #     "sphn:hasExtractionDateTime": "2022-10-20T12:00:00.000" 
    # }
    
    # ToDo: Edwin 2026-08-05
    #     Note: "conforms to" is ignored?

    #
    # Edwin 2026-08-05
    #
    # This is a Special Concept
    # - No content and no source_concept_id are provided
    #
    def get_json_dict(self, content: dict|None=None, source_concept_id: str|None=None) -> dict:
        """ 
        Gets the dict for json output
        """
        # Checks
        assert content is None or isinstance(content, dict)
        assert source_concept_id is None or is_valid_string(source_concept_id)        

        json_dict = {
            "id": f"{self.id}"
        }

        if self.has_extraction_datetime is not None:
            json_dict[f"{SPHN.hasExtractionDateTime.n3(self.sphn_schema.namespace_manager())}"] = self.has_extraction_datetime.isoformat(timespec='milliseconds')
            #.strftime("%Y-%m-%dT%H:%M:%S")

        return json_dict

    
    #
    # Edwin 2026-08-05
    #
    def is_similar(self, other: SPHNConcept) -> bool:
        """
        Compare this instance with another instance of the same class
        """

        return isinstance(other, type(self)) \
            and self.conforms_to == other.conforms_to \
            and self.has_extraction_datetime == other.has_extraction_datetime \
            and self.has_data_provider.is_similar(other.has_data_provider)

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
