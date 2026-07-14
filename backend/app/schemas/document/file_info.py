from dataclasses import dataclass

@dataclass(frozen=True)
class DocumentFileInfo:
    """Immutable data transfer object representing physical file details of the uploaded document."""
    original_filename: str
    stored_filename: str
    file_size: int  # in bytes
