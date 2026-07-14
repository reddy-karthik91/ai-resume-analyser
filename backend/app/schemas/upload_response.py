from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from app.schemas.upload_schema import UploadMetadataSchema

@dataclass
class UploadResponseSchema:
    """Standardized response schema for successful file upload."""
    message: str
    data: UploadMetadataSchema
    success: bool = True
    errors: Optional[list] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict:
        """Serialize response data to match standard API envelope."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data.to_dict() if self.data else None,
            "errors": self.errors,
            "timestamp": self.timestamp
        }
