"""
context.py: 
    Part of the example dicom2sphn package.
    It contains the Context class, which holds the application context and configuration.
"""
from pydantic import BaseModel, Field, ConfigDict
from dicomweb_client.api import DICOMwebClient

from .protocols import LoggerProtocol
from .api_users import OrthancRestAPIUser, DicomwebAPIUser, DatabaseAPIUser
from .sphn_schema_graph import SPHNSchemaGraph
from .data_store import DataStore

class Context(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    logger: LoggerProtocol = Field(..., description="Logger for the application")
    
    sphn_schema: SPHNSchemaGraph | None = Field(None, description="SPHN RDF schema graph")

    data_store: DataStore | None = Field(None, description="Data store for storing collected data")

    dw_client: DICOMwebClient | None = Field(None, description="DICOMweb API client")

    valid_sop_classes: dict[str, str] | None = Field(None, description="Dictionary of valid SOP Class UIDs and their meanings", examples=[{"1.2.840.10008.5.1.4.1.1.77.1.6": "VL Whole Slide Microscopy Image Storage"}])

    orthanc_rest_api_user: OrthancRestAPIUser | None = Field(None, description="Orthanc REST API user credentials")
    dicomweb_api_user: DicomwebAPIUser | None = Field(None, description="DICOMweb API user credentials")
    database_api_user: DatabaseAPIUser | None = Field(None, description="Database user credentials")

