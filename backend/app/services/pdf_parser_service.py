import os
import time
import logging
import uuid
import fitz  # PyMuPDF
from typing import List
from datetime import datetime
from app.schemas.document import (
    DocumentType,
    DocumentFileInfo,
    DocumentMetadata,
    PageContent,
    ParsedDocument
)
from app.exceptions.api_exceptions import InvalidResumeException

logger = logging.getLogger(__name__)

class PdfParserService:
    """Service responsible for opening PDF files and extracting structured textual contents using PyMuPDF."""

    def parse(self, file_path: str, file_info: DocumentFileInfo) -> ParsedDocument:
        """
        Parses a PDF file and constructs a ParsedDocument domain model.
        
        Args:
            file_path: Absolute path to the PDF on disk.
            file_info: Pre-resolved DocumentFileInfo containing upload details.
            
        Returns:
            A populated ParsedDocument aggregate root DTO.
        """
        start_time = time.perf_counter()
        doc_id = uuid.UUID(file_info.stored_filename.split("_")[0])

        doc = self._open_document(file_path, doc_id)
        
        pages: List[PageContent] = []
        full_text_list: List[str] = []
        total_word_count = 0
        total_character_count = 0
        has_extractable_text = False

        try:
            for page_num in range(len(doc)):
                # Sequence process pages
                raw_page_text = self._extract_page_text(doc, page_num)
                normalized_text = self._normalize_text(raw_page_text)
                
                page_content = self._build_page_content(page_num + 1, normalized_text)
                
                pages.append(page_content)
                if page_content.has_text:
                    full_text_list.append(page_content.text)
                    has_extractable_text = True

                total_word_count += page_content.word_count
                total_character_count += page_content.character_count
        finally:
            doc.close()

        elapsed_time_ms = int((time.perf_counter() - start_time) * 1000)
        full_text = "\n\n".join(full_text_list)

        # Build Metadata DTO
        metadata = self._build_metadata(
            page_count=len(pages),
            word_count=total_word_count,
            character_count=total_character_count,
            elapsed_time_ms=elapsed_time_ms,
            has_extractable_text=has_extractable_text
        )

        # Build root aggregate ParsedDocument
        parsed_doc = self._build_parsed_document(
            doc_id=doc_id,
            file_info=file_info,
            metadata=metadata,
            pages=pages,
            full_text=full_text,
            parsing_successful=True
        )

        # Structured operational log
        logger.info(
            "PDF parsed successfully",
            extra={
                "document_id": str(doc_id),
                "original_filename": file_info.original_filename,
                "stored_filename": file_info.stored_filename,
                "file_size": file_info.file_size,
                "page_count": len(pages),
                "word_count": total_word_count,
                "character_count": total_character_count,
                "parsing_duration_ms": elapsed_time_ms,
                "success": True
            }
        )

        return parsed_doc

    def _open_document(self, file_path: str, doc_id: uuid.UUID) -> fitz.Document:
        """Opens the PDF using PyMuPDF and validates read access."""
        if not os.path.exists(file_path):
            self._log_and_raise_error(
                doc_id,
                file_path,
                "FileNotFoundError",
                "The target PDF file was not found on disk.",
                "Opening document file"
            )

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            self._log_and_raise_error(
                doc_id,
                file_path,
                type(e).__name__,
                "The uploaded file is corrupted or is not a valid PDF document.",
                "Opening document file",
                str(e)
            )

        if doc.is_encrypted:
            doc.close()
            self._log_and_raise_error(
                doc_id,
                file_path,
                "EncryptedFileError",
                "The uploaded PDF file is password protected and cannot be read.",
                "Opening document file"
            )

        return doc

    def _extract_page_text(self, doc: fitz.Document, page_num: int) -> str:
        """Extracts text of a page using PyMuPDF."""
        page = doc[page_num]
        return page.get_text()

    def _build_page_content(self, page_number: int, normalized_text: str) -> PageContent:
        """Calculates page statistics and returns a PageContent DTO."""
        word_count = len(normalized_text.split()) if normalized_text else 0
        character_count = len(normalized_text) if normalized_text else 0
        has_text = character_count > 0

        return PageContent(
            page_number=page_number,
            text=normalized_text,
            word_count=word_count,
            character_count=character_count,
            has_text=has_text
        )

    def _normalize_text(self, text: str) -> str:
        """Normalizes spacing, carriage returns, and collapses excessive linebreaks."""
        if not text:
            return ""
        
        # Standardize carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # Strip trailing whitespace on each line
        lines = [line.rstrip() for line in text.split("\n")]
        
        # Collapse multiple empty lines, keeping single blank separation
        cleaned_lines = []
        consecutive_blanks = 0
        
        for line in lines:
            if not line:
                consecutive_blanks += 1
                if consecutive_blanks <= 1:
                    cleaned_lines.append("")
            else:
                consecutive_blanks = 0
                cleaned_lines.append(line)
                
        return "\n".join(cleaned_lines).strip()

    def _build_metadata(self, page_count: int, word_count: int, character_count: int, elapsed_time_ms: int, has_extractable_text: bool) -> DocumentMetadata:
        """Constructs the DocumentMetadata DTO."""
        return DocumentMetadata(
            page_count=page_count,
            word_count=word_count,
            character_count=character_count,
            parsing_time_ms=elapsed_time_ms,
            has_extractable_text=has_extractable_text,
            language=None
        )

    def _build_parsed_document(self, doc_id: uuid.UUID, file_info: DocumentFileInfo, metadata: DocumentMetadata, pages: List[PageContent], full_text: str, parsing_successful: bool) -> ParsedDocument:
        """Constructs the aggregate root ParsedDocument DTO."""
        return ParsedDocument(
            document_id=doc_id,
            document_type=DocumentType.RESUME,
            file=file_info,
            metadata=metadata,
            pages=pages,
            text=full_text,
            parsing_successful=parsing_successful
        )

    def _log_and_raise_error(self, doc_id: uuid.UUID, file_path: str, exception_type: str, message: str, stage: str, details: str = None) -> None:
        """Logs structured parsing error metadata and raises InvalidResumeException."""
        logger.error(
            "PDF parsing failed",
            extra={
                "document_id": str(doc_id) if doc_id else None,
                "stored_filename": os.path.basename(file_path),
                "exception_type": exception_type,
                "failure_reason": message,
                "processing_stage": stage,
                "details": details,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "success": False
            }
        )
        raise InvalidResumeException(message)
