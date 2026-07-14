import os
import uuid
from datetime import datetime, timezone
from werkzeug.datastructures import FileStorage
from app.repositories.document.document_repository import DocumentRepository
from app.schemas.document.document_index_entry import DocumentIndexEntry
from app.schemas.upload_schema import UploadMetadataSchema

class FileStorageService:
    """Service responsible for low-level filesystem storage operations and metadata registration."""

    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    def save_file(self, file: FileStorage, upload_dir: str) -> UploadMetadataSchema:
        """
        Ensures the directory exists, generates a unique filename format,
        saves the file to disk, registers metadata using DocumentRepository,
        and returns details of the saved file as UploadMetadataSchema.
        
        Args:
            file: The Werkzeug FileStorage object to save.
            upload_dir: The directory where the file should be saved.
            
        Returns:
            An UploadMetadataSchema instance containing file details.
        """
        # Ensure upload directory exists
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename: <uuid>_<timestamp>.pdf
        unique_id = uuid.uuid4().hex
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        stored_filename = f"{unique_id}_{timestamp}.pdf"

        # Resolve full target file path
        filepath = os.path.join(upload_dir, stored_filename)

        # Calculate file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset pointer to start before saving

        # Save file to disk
        file.save(filepath)

        uploaded_at = datetime.now(timezone.utc)

        # Map to DocumentIndexEntry DTO using raw Python datetime
        index_entry = DocumentIndexEntry(
            document_id=unique_id,
            original_filename=file.filename or "unknown",
            stored_filename=stored_filename,
            file_size=file_size,
            uploaded_at=uploaded_at
        )

        # Persist index entry using the injected repository abstraction
        self.repository.save(index_entry)

        # Map and return UploadMetadataSchema DTO for upload workflow boundaries
        return UploadMetadataSchema(
            uploadId=unique_id,
            originalFilename=file.filename or "unknown",
            storedFilename=stored_filename,
            fileSize=file_size,
            uploadedAt=uploaded_at.isoformat().replace("+00:00", "Z")
        )
