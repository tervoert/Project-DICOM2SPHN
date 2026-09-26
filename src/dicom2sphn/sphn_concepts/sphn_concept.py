"""
sphn_concept.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNConcept Abstract Class, which represents the top level concept in the SPHN schema.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict

from ..sphn_schema_graph import SPHNSchemaGraph


#
# The SPHN Concept Abstract Class representing the top level concept in the SPHN schema.
#
class SPHNConcept(ABC, BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)
   
    sphn_schema: SPHNSchemaGraph
    id: str

    @abstractmethod
    def get_json_dict(self, content: dict|None=None, source_concept_id: str|None=None) -> dict:
        pass

    @abstractmethod
    def is_similar(self, other: Any, rel_tol: float=1e-4, abs_tol: float=1e-9) -> bool:
        pass

