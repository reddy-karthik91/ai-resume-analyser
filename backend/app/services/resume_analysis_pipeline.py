import os
import logging
from flask import current_app
from uuid import UUID
from app.repositories.document.document_repository import DocumentRepository
from app.services.pdf_parser_service import PdfParserService
from app.services.upload_service import UploadService
from app.schemas.document.file_info import DocumentFileInfo
from app.schemas.document.parsed_document import ParsedDocument
from app.schemas.upload_schema import UploadMetadataSchema
from app.schemas.analysis.resume_analysis_result import ResumeAnalysisResult
from app.exceptions.validation_exceptions import ValidationException

logger = logging.getLogger(__name__)

class ResumeAnalysisPipeline:
    """
    Dedicated orchestration service coordinating the end-to-end resume analysis pipeline.
    
    Acts as the single entry point for high-level business workflow coordination.
    It receives all dependencies via constructor dependency injection.
    """

    def __init__(
        self,
        repository: DocumentRepository,
        parser_service: PdfParserService,
        upload_service: UploadService,
        prompt_builder_service=None,
        llm_service=None,
        analysis_formatter_service=None,
        gemini_service=None
    ):
        self.repository = repository
        self.parser_service = parser_service
        self.upload_service = upload_service
        self.prompt_builder_service = prompt_builder_service
        self.llm_service = llm_service or gemini_service
        self.analysis_formatter_service = analysis_formatter_service

    def upload_resume(self, file) -> UploadMetadataSchema:
        """
        Coordinates the validation and upload of a resume file.
        
        Delegates the operation to the UploadService.
        """
        return self.upload_service.upload_resume(file)

    def parse_resume(self, document_id: str) -> ParsedDocument:
        """
        Orchestrates retrieving metadata, locating the stored PDF,
        triggering text parsing, and returning a ParsedDocument DTO.
        
        Args:
            document_id: The document identifier (UUID string).
            
        Returns:
            A populated ParsedDocument aggregate root DTO.
        """
        logger.info(
            "Pipeline parse resume initiated",
            extra={
                "document_id": document_id,
                "processing_stage": "Orchestration Start"
            }
        )

        # 1. Retrieve DocumentIndexEntry from DocumentRepository
        entry = self.repository.get(document_id)
        if not entry:
            logger.error(
                "Pipeline parse failed - Document index entry not found",
                extra={
                    "document_id": document_id,
                    "processing_stage": "Retrieve Metadata",
                    "success": False
                }
            )
            raise ValidationException(
                message="Document not found",
                errors=["No upload matches the provided document identifier"]
            )

        # 2. Resolve file path
        upload_dir = current_app.config.get("UPLOAD_FOLDER")
        if not upload_dir:
            raise RuntimeError("UPLOAD_FOLDER is not configured in application settings.")

        file_path = os.path.join(upload_dir, entry.stored_filename)

        # 3. Verify file exists on disk
        if not os.path.exists(file_path):
            logger.error(
                "Pipeline parse failed - Stored PDF file is missing on disk",
                extra={
                    "document_id": document_id,
                    "stored_filename": entry.stored_filename,
                    "processing_stage": "Locate File",
                    "success": False
                }
            )
            raise ValidationException(
                message="Document file not found",
                errors=["The stored PDF file is missing on disk"]
            )

        # 4. Construct DocumentFileInfo from repository index entry
        file_info = DocumentFileInfo(
            original_filename=entry.original_filename,
            stored_filename=entry.stored_filename,
            file_size=entry.file_size
        )

        # 5. Call PdfParserService.parse(file_path, file_info)
        parsed_doc = self.parser_service.parse(file_path, file_info)

        logger.info(
            "Pipeline parse resume completed successfully",
            extra={
                "document_id": document_id,
                "stored_filename": entry.stored_filename,
                "processing_stage": "Orchestration Complete",
                "success": True
            }
        )

        return parsed_doc

    def build_prompt(self, extracted_text: str) -> str:
        """
        [PLACEHOLDER] Construct the optimized LLM prompt from the extracted text.
        
        Planned for Sprint 4: Will delegate to PromptBuilderService.
        """
        # TODO: Implement in Sprint 4
        pass

    def analyze_resume(self, document_id) -> ResumeAnalysisResult:
        """
        Coordinates the complete AI resume analysis flow.
        
        Args:
            document_id: The document identifier (UUID string or UUID object).
            
        Returns:
            A strongly-typed, fully validated ResumeAnalysisResult aggregate DTO.
        """
        doc_uuid = UUID(document_id) if isinstance(document_id, str) else document_id
        
        logger.info(
            "Pipeline analyze resume initiated",
            extra={
                "document_id": str(doc_uuid),
                "processing_stage": "Analysis Start"
            }
        )
        
        # 1. Retrieve ParsedDocument
        parsed_doc = self.parse_resume(str(doc_uuid))
        
        # Verify required service injections
        if not self.prompt_builder_service:
            raise RuntimeError("prompt_builder_service is not configured in ResumeAnalysisPipeline.")
        if not self.llm_service:
            raise RuntimeError("llm_service is not configured in ResumeAnalysisPipeline.")
        if not self.analysis_formatter_service:
            raise RuntimeError("analysis_formatter_service is not configured in ResumeAnalysisPipeline.")
            
        # 2. Compile PromptRequest using PromptBuilderService
        prompt_request = self.prompt_builder_service.build_prompt(parsed_doc)
        
        # 3. Execute using LLMService yielding PromptResponse
        prompt_response = self.llm_service.generate(prompt_request)
        
        # 4. Format PromptResponse into ResumeAnalysisResult
        analysis_result = self.analysis_formatter_service.format(doc_uuid, prompt_response)
        
        logger.info(
            "Pipeline analyze resume completed successfully",
            extra={
                "document_id": str(doc_uuid),
                "processing_stage": "Analysis Complete"
            }
        )
        
        return analysis_result

    def format_response(self, raw_analysis: str) -> dict:
        """
        [PLACEHOLDER] Structure the LLM analysis response into standard envelope formats.
        
        Planned for Sprint 4: Will delegate to AnalysisFormatterService.
        """
        # TODO: Implement in Sprint 4
        pass
