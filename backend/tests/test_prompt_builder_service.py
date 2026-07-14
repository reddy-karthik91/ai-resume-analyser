import os
import tempfile
import unittest
import uuid
from dataclasses import asdict
from app.schemas.document import ParsedDocument, DocumentFileInfo, DocumentMetadata, PageContent, DocumentType
from app.exceptions.validation_exceptions import ValidationException
from app.services.prompt_builder_service import PromptBuilderService

class TestPromptBuilderService(unittest.TestCase):
    """Unit tests for validation of PromptBuilderService constructor caching and request compilation."""

    @classmethod
    def setUpClass(cls):
        # Create a temp directory for mock templates
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.templates_path = cls.temp_dir.name
        
        # Write mock prompt files
        cls.files = {
            "system_prompt.md": "MOCK SYSTEM PROMPT",
            "analysis_instructions.md": "MOCK INSTRUCTIONS",
            "output_schema.md": "MOCK SCHEMA",
            "scoring_rules.md": "MOCK SCORING",
            "recommendation_rules.md": "MOCK RECOMMENDATIONS"
        }
        for filename, content in cls.files.items():
            with open(os.path.join(cls.templates_path, filename), "w", encoding="utf-8") as f:
                f.write(content)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def setUp(self):
        # Setup valid mock ParsedDocument
        self.doc_id = uuid.uuid4()
        self.file_info = DocumentFileInfo("resume.pdf", "stored_resume.pdf", 1024)
        self.metadata = DocumentMetadata(1, 10, 50, 10, True, "en")
        self.page = PageContent(1, "Candidate: John Doe. Experienced engineer.", 10, 50, True)
        self.parsed_doc = ParsedDocument(
            document_id=self.doc_id,
            document_type=DocumentType.RESUME,
            file=self.file_info,
            metadata=self.metadata,
            pages=[self.page],
            text="Candidate: John Doe. Experienced engineer.",
            parsing_successful=True
        )

        # Instantiate service with temp directory
        self.service = PromptBuilderService(
            templates_dir=self.templates_path,
            default_model="test-model",
            temperature=0.3,
            top_p=0.8,
            max_output_tokens=1000,
            prompt_version="v2.0"
        )

    def test_successful_prompt_creation(self):
        """Assert build_prompt correctly compiles system and user prompts with cached assets."""
        req = self.service.build_prompt(self.parsed_doc)
        
        # Verify request parameters
        self.assertEqual(req.model, "test-model")
        self.assertEqual(req.temperature, 0.3)
        self.assertEqual(req.top_p, 0.8)
        self.assertEqual(req.max_output_tokens, 1000)
        self.assertEqual(req.prompt_version, "v2.0")

        # Verify user prompt includes resume text
        self.assertIn("John Doe", req.user_prompt)
        self.assertIn("Candidate Resume", req.user_prompt)

        # Verify merged system prompt sections
        self.assertIn("MOCK SYSTEM PROMPT", req.system_prompt)
        self.assertIn("MOCK INSTRUCTIONS", req.system_prompt)
        self.assertIn("MOCK SCHEMA", req.system_prompt)

    def test_caching_behavior(self):
        """Assert prompt templates are cached in memory and not read from disk during requests."""
        # Retrieve prompt compiled once
        req_first = self.service.build_prompt(self.parsed_doc)

        # Modify file on disk
        with open(os.path.join(self.templates_path, "system_prompt.md"), "w", encoding="utf-8") as f:
            f.write("MODIFIED SYSTEM PROMPT ON DISK")

        # Compile again and assert system prompt is STILL using the cached version
        req_second = self.service.build_prompt(self.parsed_doc)
        self.assertEqual(req_first.system_prompt, req_second.system_prompt)
        self.assertIn("MOCK SYSTEM PROMPT", req_second.system_prompt)
        self.assertNotIn("MODIFIED SYSTEM PROMPT ON DISK", req_second.system_prompt)

        # Reset templates file on disk
        with open(os.path.join(self.templates_path, "system_prompt.md"), "w", encoding="utf-8") as f:
            f.write("MOCK SYSTEM PROMPT")

    def test_invalid_parameters_rejected(self):
        """Assert invalid parsed document parameters raise ValidationExceptions."""
        # None document
        with self.assertRaises(ValidationException) as context:
            self.service.build_prompt(None)  # type: ignore
        self.assertEqual(context.exception.message, "Invalid parsed document.")

        # Empty text document
        empty_doc = ParsedDocument(
            document_id=self.doc_id,
            document_type=DocumentType.RESUME,
            file=self.file_info,
            metadata=self.metadata,
            pages=[],
            text="",
            parsing_successful=True
        )
        with self.assertRaises(ValidationException) as context:
            self.service.build_prompt(empty_doc)
        self.assertEqual(context.exception.message, "Resume contains no extractable text content.")

    def test_missing_prompt_asset_rejected(self):
        """Assert initializing service with missing prompt files raises ValidationExceptions."""
        # Create empty temp dir
        with tempfile.TemporaryDirectory() as empty_dir:
            with self.assertRaises(ValidationException) as context:
                PromptBuilderService(templates_dir=empty_dir)
            self.assertIn("Missing prompt template asset", context.exception.message)
