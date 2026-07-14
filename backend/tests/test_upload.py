import io
import os
import shutil
import unittest
from flask import current_app
from app import create_app

class UploadTestCase(unittest.TestCase):
    """Unit tests for the Resume Upload feature."""

    def setUp(self):
        """Setup mock application and temporary upload folder."""
        self.app = create_app("development")
        self.app.config["TESTING"] = True
        
        # Set a temporary upload directory inside backend/tests
        self.test_upload_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_uploads"
        )
        self.app.config["UPLOAD_FOLDER"] = self.test_upload_dir
        self.client = self.app.test_client()

    def tearDown(self):
        """Clean up temporary upload files."""
        if os.path.exists(self.test_upload_dir):
            shutil.rmtree(self.test_upload_dir)

    def test_upload_success(self):
        """Assert that a valid PDF file uploads successfully and returns proper metadata."""
        data = {
            "file": (io.BytesIO(b"%PDF-1.4 mock content"), "test_resume.pdf", "application/pdf")
        }
        response = self.client.post(
            "/api/v1/resumes/upload",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 201)
        json_data = response.get_json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["message"], "Resume uploaded successfully.")
        self.assertIsNotNone(json_data["data"])
        self.assertIsNotNone(json_data["data"]["uploadId"])
        self.assertEqual(json_data["data"]["originalFilename"], "test_resume.pdf")
        self.assertTrue(json_data["data"]["storedFilename"].endswith(".pdf"))
        self.assertIn("_", json_data["data"]["storedFilename"])
        self.assertEqual(json_data["data"]["fileSize"], len(b"%PDF-1.4 mock content"))
        self.assertIsNotNone(json_data["data"]["uploadedAt"])
        self.assertIsNone(json_data["errors"])

    def test_upload_missing_file(self):
        """Assert error is returned when 'file' is not in request."""
        response = self.client.post(
            "/api/v1/resumes/upload",
            data={},
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 400)
        json_data = response.get_json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["message"], "File is required")
        self.assertIn("No file part in request", json_data["errors"])

    def test_upload_empty_filename(self):
        """Assert error is returned when file has an empty filename."""
        data = {
            "file": (io.BytesIO(b"%PDF-1.4 mock content"), "", "application/pdf")
        }
        response = self.client.post(
            "/api/v1/resumes/upload",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 400)
        json_data = response.get_json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["message"], "File is required")
        self.assertTrue(
            "No selected file" in json_data["errors"] or 
            "No file part in request" in json_data["errors"]
        )


    def test_upload_uppercase_extension(self):
        """Assert uppercase file extensions (e.g. .PDF) are supported and succeed."""
        data = {
            "file": (io.BytesIO(b"%PDF-1.4 mock content"), "RESUME.PDF", "application/pdf")
        }
        response = self.client.post(
            "/api/v1/resumes/upload",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 201)
        json_data = response.get_json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["originalFilename"], "RESUME.PDF")

    def test_upload_invalid_mime_type(self):
        """Assert that non-PDF MIME type throws 415 error even if extension is PDF."""
        data = {
            "file": (io.BytesIO(b"%PDF-1.4 mock content"), "test.pdf", "text/plain")
        }
        response = self.client.post(
            "/api/v1/resumes/upload",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 415)
        json_data = response.get_json()
        self.assertFalse(json_data["success"])
        self.assertEqual(
            json_data["message"],
            "The uploaded file format is unsupported. Only PDF files are allowed."
        )

    def test_upload_invalid_extension(self):
        """Assert that non-PDF file extension throws 415 error."""
        data = {
            "file": (io.BytesIO(b"some txt content"), "test.txt", "application/pdf")
        }
        response = self.client.post(
            "/api/v1/resumes/upload",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 415)
        json_data = response.get_json()
        self.assertFalse(json_data["success"])

    def test_upload_file_too_large(self):
        """Assert that files larger than 5 MB trigger a size validation error."""
        # 5 MB + 1 byte of mock PDF content
        large_data = b"%PDF-1.4 mock content " + b"x" * (5 * 1024 * 1024)
        data = {
            "file": (io.BytesIO(large_data), "test.pdf", "application/pdf")
        }
        response = self.client.post(
            "/api/v1/resumes/upload",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 400)
        json_data = response.get_json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["message"], "File size exceeds the maximum limit of 5 MB.")


    def test_upload_zero_byte_pdf(self):
        """Assert that zero-byte files trigger validation errors."""
        data = {
            "file": (io.BytesIO(b""), "test.pdf", "application/pdf")
        }
        response = self.client.post(
            "/api/v1/resumes/upload",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 400)
        json_data = response.get_json()
        self.assertFalse(json_data["success"])
        self.assertIn("empty (0 bytes)", json_data["errors"][0])

    def test_upload_duplicate_successive(self):
        """Assert successive uploads succeed independently and generate distinct file paths."""
        data1 = {
            "file": (io.BytesIO(b"%PDF-1.4 file 1"), "test_resume.pdf", "application/pdf")
        }
        data2 = {
            "file": (io.BytesIO(b"%PDF-1.4 file 2"), "test_resume.pdf", "application/pdf")
        }
        
        r1 = self.client.post(
            "/api/v1/resumes/upload",
            data=data1,
            content_type="multipart/form-data"
        )
        r2 = self.client.post(
            "/api/v1/resumes/upload",
            data=data2,
            content_type="multipart/form-data"
        )
        
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 201)
        
        j1 = r1.get_json()
        j2 = r2.get_json()
        
        self.assertNotEqual(j1["data"]["storedFilename"], j2["data"]["storedFilename"])
        self.assertTrue(os.path.exists(os.path.join(self.test_upload_dir, j1["data"]["storedFilename"])))
        self.assertTrue(os.path.exists(os.path.join(self.test_upload_dir, j2["data"]["storedFilename"])))

    def test_upload_missing_content_type(self):
        """Assert validation error occurs when Content-Type is missing (empty)."""
        data = {
            "file": (io.BytesIO(b"%PDF-1.4 mock content"), "test.pdf", "")
        }
        response = self.client.post(
            "/api/v1/resumes/upload",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 415)
        json_data = response.get_json()
        self.assertFalse(json_data["success"])
