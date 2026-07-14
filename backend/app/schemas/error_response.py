from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ErrorResponseSchema:
    """Standardized response schema for API errors."""
    message: str
    errors: List[str] = field(default_factory=list)
    success: bool = False
    data: Optional[dict] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict:
        """Serialize error details to match standard API envelope."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "errors": self.errors,
            "timestamp": self.timestamp
        }
