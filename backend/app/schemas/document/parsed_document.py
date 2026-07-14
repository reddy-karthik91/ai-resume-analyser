from dataclasses import dataclass, field
from uuid import UUID
from typing import List
from app.schemas.document.document_type import DocumentType
from app.schemas.document.file_info import DocumentFileInfo
from app.schemas.document.metadata import DocumentMetadata
from app.schemas.document.page import PageContent

@dataclass(frozen=True)
class ParsedDocument:
    """Immutable root aggregate domain model representing a successfully parsed document."""
    document_id: UUID
    file: DocumentFileInfo
    metadata: DocumentMetadata
    pages: List[PageContent]
    text: str
    parsing_successful: bool
    document_type: DocumentType = DocumentType.UNKNOWN
