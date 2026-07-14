import uuid
import unittest
from dataclasses import asdict, FrozenInstanceError
from app.schemas.document import (
    DocumentType,
    DocumentFileInfo,
    DocumentMetadata,
    PageContent,
    ParsedDocument
)

class TestDocumentDomainModel(unittest.TestCase):
    """Unit tests for validating the ParsedDocument domain model hierarchy."""

    def test_dataclass_construction_and_composition(self):
        """Test successful instantiation and nested composition of domain models."""
        doc_id = uuid.uuid4()
        
        file_info = DocumentFileInfo(
            original_filename="resume.pdf",
            stored_filename="abcdef_20260714T120000.pdf",
            file_size=102400
        )
        
        metadata = DocumentMetadata(
            page_count=2,
            word_count=500,
            character_count=3000,
            parsing_time_ms=150,
            has_extractable_text=True,
            language="en"
        )
        
        page1 = PageContent(
            page_number=1,
            text="Hello Page 1",
            word_count=250,
            character_count=1500,
            has_text=True
        )
        
        page2 = PageContent(
            page_number=2,
            text="Hello Page 2",
            word_count=250,
            character_count=1500,
            has_text=True
        )
        
        parsed_doc = ParsedDocument(
            document_id=doc_id,
            document_type=DocumentType.RESUME,
            file=file_info,
            metadata=metadata,
            pages=[page1, page2],
            text="Hello Page 1\nHello Page 2",
            parsing_successful=True
        )
        
        # Assert composition
        self.assertEqual(parsed_doc.document_id, doc_id)
        self.assertEqual(parsed_doc.document_type, DocumentType.RESUME)
        self.assertEqual(parsed_doc.file.original_filename, "resume.pdf")
        self.assertEqual(parsed_doc.metadata.page_count, 2)
        self.assertEqual(len(parsed_doc.pages), 2)
        self.assertEqual(parsed_doc.pages[0].text, "Hello Page 1")
        self.assertTrue(parsed_doc.parsing_successful)

    def test_frozen_dataclass_immutability(self):
        """Assert that all domain dataclasses are frozen (immutable) and raise errors on mutation."""
        file_info = DocumentFileInfo(
            original_filename="a.pdf",
            stored_filename="b.pdf",
            file_size=10
        )
        
        with self.assertRaises(FrozenInstanceError):
            # Attempting to mutate an immutable field
            file_info.file_size = 20  # type: ignore

        metadata = DocumentMetadata(
            page_count=1,
            word_count=10,
            character_count=50,
            parsing_time_ms=10,
            has_extractable_text=True
        )
        with self.assertRaises(FrozenInstanceError):
            metadata.page_count = 2  # type: ignore

        page = PageContent(
            page_number=1,
            text="text",
            word_count=1,
            character_count=4,
            has_text=True
        )
        with self.assertRaises(FrozenInstanceError):
            page.text = "new"  # type: ignore

        parsed_doc = ParsedDocument(
            document_id=uuid.uuid4(),
            file=file_info,
            metadata=metadata,
            pages=[page],
            text="text",
            parsing_successful=True
        )
        with self.assertRaises(FrozenInstanceError):
            parsed_doc.text = "new text"  # type: ignore

    def test_asdict_serialization(self):
        """Assert that dataclasses.asdict() recursively serializes the composed aggregate."""
        doc_id = uuid.uuid4()
        file_info = DocumentFileInfo("a.pdf", "b.pdf", 100)
        metadata = DocumentMetadata(1, 10, 50, 10, True, "en")
        page = PageContent(1, "text", 10, 50, True)
        
        parsed_doc = ParsedDocument(
            document_id=doc_id,
            document_type=DocumentType.JOB_DESCRIPTION,
            file=file_info,
            metadata=metadata,
            pages=[page],
            text="text",
            parsing_successful=True
        )
        
        serialized = asdict(parsed_doc)
        
        # Verify structure
        self.assertEqual(serialized["document_id"], doc_id)
        self.assertEqual(serialized["document_type"], DocumentType.JOB_DESCRIPTION)
        self.assertEqual(serialized["file"]["original_filename"], "a.pdf")
        self.assertEqual(serialized["metadata"]["page_count"], 1)
        self.assertEqual(serialized["pages"][0]["text"], "text")
        self.assertTrue(serialized["parsing_successful"])

    def test_edge_cases_and_defaults(self):
        """Assert handling of zero counts, empty strings, and default Enum values."""
        doc_id = uuid.uuid4()
        file_info = DocumentFileInfo("", "", 0)
        metadata = DocumentMetadata(
            page_count=0,
            word_count=0,
            character_count=0,
            parsing_time_ms=0,
            has_extractable_text=False
        )
        
        parsed_doc = ParsedDocument(
            document_id=doc_id,
            file=file_info,
            metadata=metadata,
            pages=[],
            text="",
            parsing_successful=False
        )
        
        # Verify default document_type is UNKNOWN
        self.assertEqual(parsed_doc.document_type, DocumentType.UNKNOWN)
        self.assertEqual(parsed_doc.metadata.language, None)
        self.assertEqual(parsed_doc.metadata.page_count, 0)
        self.assertEqual(len(parsed_doc.pages), 0)
        self.assertEqual(parsed_doc.text, "")
        self.assertFalse(parsed_doc.parsing_successful)
