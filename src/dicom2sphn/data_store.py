"""
data_store.py: 
    Part of the example dicom2sphn package.
    It contains the DataStore class, which handles data storage.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from .sphn_data_provider import SPHNDataProvider
from .sphn_data_release import SPHNDataRelease
from .sphn_source_system import SPHNSourceSystem

class DataStore(BaseModel):
    """
    A class to handle data storage.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    sphn_data_release: SPHNDataRelease
    sphn_data_provider: SPHNDataProvider
    sphn_source_system: SPHNSourceSystem

    
