"""
context.py: 
    Part of the example dicom2sphn package.
    It contains the Context class, which holds the application context and configuration.
"""
from dicomweb_client.api import DICOMwebClient
from pydantic import BaseModel, ConfigDict, Field

from .api_users import DatabaseAPIUser, DicomwebAPIUser, OrthancRestAPIUser
from .data_store import DataStore
from .protocols import LoggerProtocol
from .sphn_schema_graph import SPHNSchemaGraph


class Context(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    logger: LoggerProtocol = Field(..., description="Logger for the application")
    
    sphn_schema: SPHNSchemaGraph | None = Field(None, description="SPHN RDF schema graph")

    data_store: DataStore | None = Field(None, description="Data store for storing collected data")

    dw_client: DICOMwebClient | None = Field(None, description="DICOMweb API client")

    orthanc_rest_api_user: OrthancRestAPIUser | None = Field(None, description="Orthanc REST API user credentials")
    dicomweb_api_user: DicomwebAPIUser | None = Field(None, description="DICOMweb API user credentials")
    database_api_user: DatabaseAPIUser | None = Field(None, description="Database user credentials")

    # ToDo: Edwin: Move to configuration file
    ALWAYS_ADD_SPHN_IMAGING_PROCEDURE: bool = True
    ALWAYS_ADD_SPHN_IMAGING_SERIES: bool = True
    ALWAYS_ADD_SPHN_IMAGING_FRAME: bool = True




