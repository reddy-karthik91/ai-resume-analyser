import os
import json
import logging
import threading
from datetime import datetime
from typing import Optional
from app.repositories.document.document_repository import DocumentRepository
from app.schemas.document.document_index_entry import DocumentIndexEntry

logger = logging.getLogger(__name__)

class FilesystemDocumentRepository(DocumentRepository):
    """
    Filesystem-backed repository implementing document metadata indexing.
    
    Uses a single, shared JSON index file protected by a threading.Lock to prevent concurrent corruption.
    """

    def __init__(self, index_path: str = None):
        if index_path is None:
            # Resolve default path: backend/storage/documents/index.json
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            index_path = os.path.join(base_dir, "storage", "documents", "index.json")
        
        self.index_path = index_path
        self._lock = threading.Lock()

    def _load_index(self) -> dict:
        """Loads the document index from the JSON file. If file is missing or corrupted, returns an empty dict."""
        if not os.path.exists(self.index_path):
            return {}
        try:
            with open(self.index_path, 'r') as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(
                "Document index file is corrupted or unreadable. Initializing empty index.",
                extra={
                    "exception_type": type(e).__name__,
                    "error_message": str(e),
                    "index_path": self.index_path
                }
            )
            # Safe fallback: return empty dictionary to recover
            return {}

    def _save_index(self, index: dict) -> None:
        """Saves the document index to the JSON file, ensuring directories exist."""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        try:
            with open(self.index_path, 'w') as f:
                json.dump(index, f, indent=4)
        except IOError as e:
            logger.error(
                "Failed to write document index to filesystem.",
                extra={
                    "exception_type": type(e).__name__,
                    "error_message": str(e),
                    "index_path": self.index_path
                }
            )
            raise e

    def save(self, entry: DocumentIndexEntry) -> None:
        """Thread-safe save or update of a document metadata entry."""
        from uuid import UUID
        doc_id = entry.document_id
        try:
            doc_id = str(UUID(doc_id))
        except ValueError:
            pass

        with self._lock:
            index = self._load_index()
            
            # Convert datetime to ISO-8601 string for serialization
            iso_timestamp = entry.uploaded_at.isoformat()
            if entry.uploaded_at.tzinfo is None:
                # Add Z if it is a naive UTC datetime
                iso_timestamp += "Z"
            elif iso_timestamp.endswith("+00:00"):
                # Clean up +00:00 to Z
                iso_timestamp = iso_timestamp[:-6] + "Z"

            index[doc_id] = {
                "document_id": doc_id,
                "original_filename": entry.original_filename,
                "stored_filename": entry.stored_filename,
                "file_size": entry.file_size,
                "uploaded_at": iso_timestamp
            }
            self._save_index(index)
            
            logger.info(
                "Document metadata indexed successfully",
                extra={
                    "document_id": doc_id,
                    "stored_filename": entry.stored_filename,
                    "original_filename": entry.original_filename,
                    "file_size": entry.file_size,
                    "success": True
                }
            )

    def get(self, document_id: str) -> Optional[DocumentIndexEntry]:
        """Thread-safe retrieval of a document metadata entry."""
        from uuid import UUID
        doc_id = document_id
        try:
            doc_id = str(UUID(doc_id))
        except ValueError:
            pass

        with self._lock:
            index = self._load_index()
            data = index.get(doc_id)
            if not data:
                return None
            
            # Parse ISO-8601 string back to datetime
            iso_str = data["uploaded_at"]
            if iso_str.endswith("Z"):
                # Replace trailing 'Z' with UTC offset '+00:00' for Python 3.9 compatibility
                iso_str = iso_str[:-1] + "+00:00"
            
            try:
                uploaded_at = datetime.fromisoformat(iso_str)
            except ValueError as e:
                logger.error(
                    "Invalid date format in document index entry.",
                    extra={
                        "document_id": doc_id,
                        "uploaded_at_raw": data["uploaded_at"],
                        "exception_type": type(e).__name__
                    }
                )
                raise e

            return DocumentIndexEntry(
                document_id=data["document_id"],
                original_filename=data["original_filename"],
                stored_filename=data["stored_filename"],
                file_size=data["file_size"],
                uploaded_at=uploaded_at
            )
