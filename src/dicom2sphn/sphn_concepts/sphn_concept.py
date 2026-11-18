"""
sphn_concept.py: 
    Part of the example dicom2sphn package. 
    It contains the SPHNConcept Abstract Class, which represents the top level concept in the SPHN schema.
"""

from abc import ABC, abstractmethod

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
    def get_json_dict(self, content: dict|None=None, source_concept_id: str|None=None, write_target_concept: bool=False) -> dict:
        pass

    @abstractmethod
    def __eq__(self, other):
        pass

    # 
    # A quick comparison based on the id for sorting purposes.
    #
    def __lt__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.id < other.id


    #
    # Generic repr listing all model fields except the schema graph and the id.
    #
    def __repr__(self):
        args = ", ".join(
            f"{name}={getattr(self, name)!r}"
            for name in type(self).model_fields
            if name not in ("sphn_schema", "id")
        )
        return f"{self.__class__.__name__}({args})"


#
# Edwin 2026-11-16
#
class UnorderedList:
    """
    Wraps a list of SPHN concepts (or None) for an order-independent comparison in the __eq__ functions, e.g.:
        (self.has_code, UnorderedList(self.has_source_system_list)) == (other.has_code, UnorderedList(other.has_source_system_list))
    Two lists are equal when they have the same length and each item in one list equals (with __eq__, the content)
    a different item in the other list. The order and the (random) ids of the items do not matter.
    Note: Sorting the lists (with SPHNConcept.__lt__) does not work for this, as it sorts by the random id:
          two lists with items of the same content can then be sorted in a different order.
    """

    __slots__ = ("items",)

    def __init__(self, items: list|None):
        assert items is None or isinstance(items, list)
        self.items = items

    def __eq__(self, other):
        if not isinstance(other, UnorderedList):
            return NotImplemented

        if self.items is None or other.items is None:
            return self.items is None and other.items is None

        if len(self.items) != len(other.items):
            return False

        # Each item must match a different (not yet matched) item in the other list
        remaining = list(other.items)
        for item in self.items:
            for index, other_item in enumerate(remaining):
                if item == other_item:
                    del remaining[index]
                    break
            else:
                return False

        return True

    __hash__ = None  # mutable content, not hashable

    def __repr__(self):
        return f"UnorderedList({self.items!r})"
    