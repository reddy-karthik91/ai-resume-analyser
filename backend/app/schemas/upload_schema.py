from dataclasses import dataclass, asdict

@dataclass
class UploadMetadataSchema:
    """Dataclass schema representing the metadata returned upon successful upload."""
    uploadId: str
    originalFilename: str
    storedFilename: str
    fileSize: int
    uploadedAt: str

    def to_dict(self) -> dict:
        """Serialize the dataclass to a standard Python dictionary."""
        return asdict(self)
