from datetime import datetime
from dataclasses import dataclass

@dataclass(frozen=True)
class DocumentIndexEntry:
    """Immutable domain model representing document metadata in the repository layer."""
    document_id: str
    original_filename: str
    stored_filename: str
    file_size: int
    uploaded_at: datetime
