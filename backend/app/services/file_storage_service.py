import os
import uuid
from datetime import datetime
from werkzeug.datastructures import FileStorage

class FileStorageService:
    """Service responsible for low-level filesystem storage operations."""

    def save_file(self, file: FileStorage, upload_dir: str) -> dict:
        """
        Ensures the directory exists, generates a unique filename format,
        saves the file to disk, and returns details of the saved file.
        
        Args:
            file: The Werkzeug FileStorage object to save.
            upload_dir: The directory where the file should be saved.
            
        Returns:
            A dictionary containing:
                - storedFilename: The generated unique file name.
                - fileSize: The size of the file in bytes.
                - uploadedAt: ISO-8601 UTC timestamp of the upload.
        """
        # Ensure upload directory exists
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename: <uuid>_<timestamp>.pdf
        unique_id = uuid.uuid4().hex
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        stored_filename = f"{unique_id}_{timestamp}.pdf"

        # Resolve full target file path
        filepath = os.path.join(upload_dir, stored_filename)

        # Calculate file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset pointer to start before saving

        # Save file to disk
        file.save(filepath)

        return {
            "storedFilename": stored_filename,
            "fileSize": file_size,
            "uploadedAt": datetime.utcnow().isoformat() + "Z"
        }
