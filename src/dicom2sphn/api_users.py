
from pydantic import BaseModel, Field, SecretStr

class OrthancRestAPIUser(BaseModel):
    """Pydantic model for Orthanc REST API settings and user credentials."""
    base_url: str = Field(..., description="Base URL for the Orthanc REST API", examples=["http://localhost:8042"])
    username: str = Field(..., description="Orthanc REST API username", examples=["orthanc_user"])
    password: SecretStr = Field(..., description="Orthanc REST API password", examples=["orthanc_password"])

class DicomwebAPIUser(BaseModel):
    """Pydantic model for DICOMweb API user credentials."""
    base_url: str = Field(..., description="Base URL for the Orthanc REST API", examples=["http://localhost/dicom-web:8042"])
    username: str = Field(..., description="DICOMweb API username", examples=["dicomweb_user"])
    password: SecretStr = Field(..., description="DICOMweb API password", examples=["dicomweb_password"])

class DatabaseAPIUser(BaseModel):
    """Pydantic model for database user credentials."""
    user: str = Field(..., description="Database username", examples=["database_user"])
    password: SecretStr = Field(..., description="Database password", examples=["database_password"])
