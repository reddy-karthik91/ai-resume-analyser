from abc import ABC, abstractmethod
from typing import Optional
from app.schemas.document.document_index_entry import DocumentIndexEntry

class DocumentRepository(ABC):
    """Abstract base repository contract for managing document metadata index entries."""

    @abstractmethod
    def save(self, entry: DocumentIndexEntry) -> None:
        """
        Saves a document index entry to the persistent store.
        
        Args:
            entry: The DocumentIndexEntry DTO to persist.
        """
        pass

    @abstractmethod
    def get(self, document_id: str) -> Optional[DocumentIndexEntry]:
        """
        Retrieves a document index entry from the store by its identifier.
        
        Args:
            document_id: The document identifier.
            
        Returns:
            The DocumentIndexEntry if found, else None.
        """
        pass
