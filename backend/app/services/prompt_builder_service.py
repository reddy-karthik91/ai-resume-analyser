import os
import logging
from typing import Optional
from app.schemas.document import ParsedDocument
from app.schemas.analysis.prompt_request import PromptRequest
from app.exceptions.validation_exceptions import ValidationException

logger = logging.getLogger(__name__)

class PromptBuilderService:
    """Service responsible for constructing structured and provider-independent PromptRequest objects."""

    def __init__(
        self,
        templates_dir: Optional[str] = None,
        default_model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        prompt_version: Optional[str] = None
    ):
        """
        Initializes PromptBuilderService and loads markdown templates in memory.
        
        Args:
            templates_dir: Path to directory containing prompt templates markdown files.
            default_model: Name of the default LLM model.
            temperature: Configurable generation temperature.
            top_p: Configurable top_p value.
            max_output_tokens: Maximum number of tokens for output responses.
            prompt_version: Version identifier for prompts.
        """
        # Resolve templates directory
        if not templates_dir:
            templates_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "prompts"
            )
        self.templates_dir = templates_dir

        # Load and cache template contents in memory
        self.templates = {}
        self._load_templates()

        # Configurable defaults
        self.default_model = default_model or "gemini-1.5-pro"
        self.temperature = temperature if temperature is not None else 0.1
        self.top_p = top_p if top_p is not None else 0.95
        self.max_output_tokens = max_output_tokens if max_output_tokens is not None else 4096
        self.prompt_version = prompt_version or "v1.0.0"

    def _load_templates(self):
        """Loads and caches prompt markdown files in memory. Raises ValidationException on failure."""
        required_files = {
            "system": "system_prompt.md",
            "instructions": "analysis_instructions.md",
            "schema": "output_schema.md",
            "scoring": "scoring_rules.md",
            "recommendation": "recommendation_rules.md"
        }
        
        for key, filename in required_files.items():
            filepath = os.path.join(self.templates_dir, filename)
            if not os.path.exists(filepath):
                raise ValidationException(
                    errors=[f"Template file '{filename}' not found in directory: {self.templates_dir}"],
                    message=f"Missing prompt template asset: {filename}"
                )
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.templates[key] = f.read()
            except Exception as e:
                raise ValidationException(
                    errors=[str(e)],
                    message=f"Failed to read prompt template asset: {filename}"
                )

    def build_prompt(self, parsed_document: ParsedDocument) -> PromptRequest:
        """
        Builds a structured PromptRequest from a parsed document.
        
        Args:
            parsed_document: The parsed resume document domain model.
            
        Returns:
            A populated PromptRequest object.
        """
        if parsed_document is None:
            raise ValidationException(
                errors=["parsed_document parameter cannot be None."],
                message="Invalid parsed document."
            )
            
        if not parsed_document.text or not parsed_document.text.strip():
            raise ValidationException(
                errors=["Resume text is empty or non-extractable."],
                message="Resume contains no extractable text content."
            )

        # Merge system prompt templates
        system_prompt = (
            f"{self.templates['system']}\n\n"
            f"{self.templates['instructions']}\n\n"
            f"{self.templates['scoring']}\n\n"
            f"{self.templates['recommendation']}\n\n"
            f"{self.templates['schema']}"
        )

        # Build candidate resume user prompt segment
        user_prompt = (
            "Candidate Resume\n"
            "----------------\n"
            f"{parsed_document.text}\n"
            "----------------\n"
            "End Resume\n"
        )

        # Map current Flask application configurations if executing under Flask context
        model = self.default_model
        temp = self.temperature
        top_p = self.top_p
        max_tokens = self.max_output_tokens
        version = self.prompt_version

        try:
            from flask import current_app
            if current_app:
                model = current_app.config.get("DEFAULT_LLM_MODEL", model)
                temp = current_app.config.get("LLM_TEMPERATURE", temp)
                top_p = current_app.config.get("LLM_TOP_P", top_p)
                max_tokens = current_app.config.get("LLM_MAX_OUTPUT_TOKENS", max_tokens)
                version = current_app.config.get("LLM_PROMPT_VERSION", version)
        except RuntimeError:
            pass

        # Construct request DTO
        request = PromptRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=temp,
            max_output_tokens=max_tokens,
            top_p=top_p,
            prompt_version=version
        )

        # Log construct metrics (safe of PII/Content)
        logger.info(
            "PromptRequest constructed successfully.",
            extra={
                "document_id": str(parsed_document.document_id),
                "page_count": parsed_document.metadata.page_count,
                "word_count": parsed_document.metadata.word_count,
                "prompt_version": version,
                "model": model,
                "system_prompt_size_chars": len(system_prompt),
                "user_prompt_size_chars": len(user_prompt)
            }
        )

        return request
