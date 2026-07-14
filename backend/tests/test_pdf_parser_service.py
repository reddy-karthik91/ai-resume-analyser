import os
import uuid
import shutil
import tempfile
import unittest
import fitz  # PyMuPDF
from app.services.pdf_parser_service import PdfParserService
from app.schemas.document import DocumentFileInfo
from app.exceptions.api_exceptions import InvalidResumeException

class TestPdfParserService(unittest.TestCase):
    """Unit tests for validating the PdfParserService extraction and error handling."""

    @classmethod
    def setUpClass(cls):
        # Create a temp resources folder for PDF generation
        cls.test_dir = tempfile.mkdtemp()
        cls.resources_dir = os.path.join(cls.test_dir, "resources")
        os.makedirs(cls.resources_dir, exist_ok=True)

        # 1. Single Page PDF
        cls.single_page_path = os.path.join(cls.resources_dir, "single_page.pdf")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "John Doe Resume\nExperience: Software Engineer at Google.\nSkills: Python, Go, SQL.")
        doc.save(cls.single_page_path)
        doc.close()

        # 2. Multi Page PDF
        cls.multi_page_path = os.path.join(cls.resources_dir, "multi_page.pdf")
        doc = fitz.open()
        p1 = doc.new_page()
        p1.insert_text((50, 50), "John Doe Page 1\nExperience: Google")
        p2 = doc.new_page()
        p2.insert_text((50, 50), "John Doe Page 2\nEducation: Stanford University")
        doc.save(cls.multi_page_path)
        doc.close()

        # 3. Blank PDF
        cls.blank_path = os.path.join(cls.resources_dir, "blank.pdf")
        doc = fitz.open()
        doc.new_page()
        doc.save(cls.blank_path)
        doc.close()

        # 4. Unicode PDF
        cls.unicode_path = os.path.join(cls.resources_dir, "unicode.pdf")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Resume: Jérôme & Niña\nSkills: C++, Python, Español, Français.")
        doc.save(cls.unicode_path)
        doc.close()

        # 5. PDF with Tables
        cls.table_path = os.path.join(cls.resources_dir, "table.pdf")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Company | Role | Years\nGoogle | SWE | 2\nMeta | Senior SWE | 3")
        doc.save(cls.table_path)
        doc.close()

        # 6. PDF with Lists
        cls.list_path = os.path.join(cls.resources_dir, "list.pdf")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Skills:\n• Python\n• Go\n• Cloud computing")
        doc.save(cls.list_path)
        doc.close()

        # 7. Image-only PDF (drawing a vector shape, no text)
        cls.image_only_path = os.path.join(cls.resources_dir, "image_only.pdf")
        doc = fitz.open()
        page = doc.new_page()
        page.draw_rect((50, 50, 150, 150), color=(1, 0, 0), fill=(0, 1, 0))
        doc.save(cls.image_only_path)
        doc.close()

        # 8. Password Protected PDF
        cls.password_path = os.path.join(cls.resources_dir, "password_protected.pdf")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Top Secret contents")
        # Encrypt with owner/user passwords
        doc.save(cls.password_path, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="password", owner_pw="owner")
        doc.close()

        # 9. Corrupted PDF (invalid file header)
        cls.corrupted_path = os.path.join(cls.resources_dir, "corrupted.pdf")
        with open(cls.corrupted_path, "wb") as f:
            f.write(b"%PDF-1.4 corrupted metadata stream content")

    @classmethod
    def tearDownClass(cls):
        # Remove the temp resources folder
        shutil.rmtree(cls.test_dir)

    def setUp(self):
        self.parser = PdfParserService()
        self.doc_id = uuid.uuid4().hex
        self.file_info = DocumentFileInfo(
            original_filename="sample.pdf",
            stored_filename=f"{self.doc_id}_20260714T120000.pdf",
            file_size=1024
        )

    def test_single_page_pdf(self):
        """Assert single page PDF extracts correct text and metadata counts."""
        parsed = self.parser.parse(self.single_page_path, self.file_info)
        
        self.assertTrue(parsed.parsing_successful)
        self.assertEqual(parsed.metadata.page_count, 1)
        self.assertTrue(parsed.metadata.has_extractable_text)
        self.assertIn("John Doe Resume", parsed.text)
        self.assertEqual(len(parsed.pages), 1)
        self.assertTrue(parsed.pages[0].has_text)
        self.assertGreater(parsed.metadata.parsing_time_ms, -1)

    def test_multi_page_pdf(self):
        """Assert page extraction order and content splits for multi-page documents."""
        parsed = self.parser.parse(self.multi_page_path, self.file_info)
        
        self.assertEqual(parsed.metadata.page_count, 2)
        self.assertEqual(parsed.pages[0].page_number, 1)
        self.assertIn("Page 1", parsed.pages[0].text)
        self.assertEqual(parsed.pages[1].page_number, 2)
        self.assertIn("Page 2", parsed.pages[1].text)
        self.assertIn("Stanford University", parsed.text)

    def test_blank_pdf(self):
        """Assert empty pages are not skipped and are marked as not containing text."""
        parsed = self.parser.parse(self.blank_path, self.file_info)
        
        self.assertEqual(parsed.metadata.page_count, 1)
        self.assertFalse(parsed.metadata.has_extractable_text)
        self.assertEqual(parsed.text, "")
        self.assertFalse(parsed.pages[0].has_text)

    def test_unicode_pdf(self):
        """Assert unicode characters are preserved in parsed text."""
        parsed = self.parser.parse(self.unicode_path, self.file_info)
        
        self.assertIn("Jérôme", parsed.text)
        self.assertIn("Niña", parsed.text)
        self.assertIn("Español", parsed.text)

    def test_tables_and_bullet_lists(self):
        """Assert tables and bullet list delimiters are kept intact during text extraction."""
        table_parsed = self.parser.parse(self.table_path, self.file_info)
        self.assertIn("Company | Role", table_parsed.text)

        list_parsed = self.parser.parse(self.list_path, self.file_info)
        self.assertTrue("• Python" in list_parsed.text or "· Python" in list_parsed.text)

    def test_image_only_pdf(self):
        """Assert image-only (non-text) PDFs parse successfully with has_extractable_text=False."""
        parsed = self.parser.parse(self.image_only_path, self.file_info)
        
        self.assertEqual(parsed.metadata.page_count, 1)
        self.assertFalse(parsed.metadata.has_extractable_text)
        self.assertEqual(parsed.text, "")

    def test_password_protected_pdf_rejection(self):
        """Assert password protected PDF files raise InvalidResumeException."""
        with self.assertRaises(InvalidResumeException) as ctx:
            self.parser.parse(self.password_path, self.file_info)
        self.assertIn("password protected", str(ctx.exception))

    def test_corrupted_pdf_rejection(self):
        """Assert corrupted or malformed PDF files raise InvalidResumeException."""
        with self.assertRaises(InvalidResumeException):
            self.parser.parse(self.corrupted_path, self.file_info)

    def test_file_not_found(self):
        """Assert missing PDF file paths raise InvalidResumeException."""
        with self.assertRaises(InvalidResumeException) as ctx:
            self.parser.parse("/invalid/path/to/missing.pdf", self.file_info)
        self.assertIn("not found on disk", str(ctx.exception))
