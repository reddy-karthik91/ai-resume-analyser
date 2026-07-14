import time
import uuid
import logging
from typing import Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError, ServerError

from app.schemas.analysis.prompt_request import PromptRequest
from app.schemas.analysis.prompt_response import PromptResponse
from app.schemas.analysis.finish_reason import FinishReason
from app.schemas.analysis.token_usage import TokenUsage
from app.exceptions.api_exceptions import APIException
from app.exceptions.validation_exceptions import ValidationException

logger = logging.getLogger(__name__)

class GeminiService:
    """Service responsible for communicating with Google Gemini API using the unified google-genai SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay_seconds: Optional[int] = None
    ):
        """
        Initializes GeminiService with configured values.
        
        Args:
            api_key: The Google Gemini API Key.
            default_model: Target model name (e.g. gemini-2.5-flash).
            timeout_seconds: Request timeout in seconds.
            max_retries: Number of retry attempts for transient errors.
            retry_delay_seconds: Starting backoff delay in seconds.
        """
        self.api_key = api_key
        self.default_model = default_model or "gemini-2.0-flash"
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else 60
        self.max_retries = max_retries if max_retries is not None else 2
        self.retry_delay_seconds = retry_delay_seconds if retry_delay_seconds is not None else 2

        import importlib.metadata
        try:
            sdk_version = importlib.metadata.version("google-genai")
        except Exception:
            sdk_version = "unknown"

        logger.info(
            "Gemini configuration loaded:\n"
            f"api_key_present={self.api_key is not None}\n"
            f"configured_model={self.default_model}\n"
            f"sdk_version={sdk_version}\n"
            f"timeout={self.timeout_seconds}\n"
            f"max_retries={self.max_retries}"
        )

    def generate(self, request: PromptRequest) -> PromptResponse:
        """
        Executes models generation using Google Gemini API.
        
        Args:
            request: Standardized PromptRequest containing system and user prompts.
            
        Returns:
            A populated PromptResponse DTO.
        """
        request_id = str(uuid.uuid4())
        
        # Configure client dynamically per request to ensure correct timeout setting
        client = self._configure_client()
        
        logger.info(
            "Gemini request initiation",
            extra={
                "request_id": request_id,
                "model": request.model,
                "prompt_version": request.prompt_version,
                "status": "initiated"
            }
        )
        
        # Execute models request with retries
        raw_response, duration_ms, retry_count = self._execute_request(client, request, request_id)
        
        # Validate response content
        self._validate_response(raw_response, request_id)
        
        # Parse usage metadata and finish reasons
        token_usage = self._extract_usage(raw_response)
        finish_reason = self._extract_finish_reason(raw_response)
        
        # Log successful completion (safe of PII/Content)
        logger.info(
            "Gemini request completed successfully",
            extra={
                "request_id": request_id,
                "model": raw_response.model if hasattr(raw_response, "model") else request.model,
                "response_time_ms": duration_ms,
                "retry_count": retry_count,
                "finish_reason": finish_reason.name,
                "status": "success"
            }
        )
        
        return PromptResponse(
            content=raw_response.text,
            model_used=raw_response.model if hasattr(raw_response, "model") else request.model,
            finish_reason=finish_reason,
            token_usage=token_usage,
            response_time_ms=duration_ms
        )

    def _configure_client(self) -> genai.Client:
        """Configures and returns a new Google GenAI client instance."""
        if not self.api_key:
            raise APIException(
                message="Google Gemini API key is missing. Configure GEMINI_API_KEY environment variable.",
                status_code=401
            )
            
        # HttpOptions expects timeout in milliseconds
        timeout_ms = self.timeout_seconds * 1000
        
        try:
            return genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(timeout=timeout_ms)
            )
        except Exception as e:
            raise APIException(
                message=f"Failed to initialize Google GenAI Client: {str(e)}",
                status_code=500
            )

    def _execute_request(self, client: genai.Client, request: PromptRequest, request_id: str):
        """Sends generating commands to client.models.generate_content implementing backoffs."""
        attempt = 0
        max_retries = self.max_retries
        delay = self.retry_delay_seconds

        while True:
            try:
                start_time = time.perf_counter()
                
                # Request generation
                response = client.models.generate_content(
                    model=request.model or self.default_model,
                    contents=request.user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=request.system_prompt,
                        temperature=request.temperature,
                        top_p=request.top_p,
                        max_output_tokens=request.max_output_tokens,
                        response_mime_type="application/json"
                    )
                )
                
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                return response, duration_ms, attempt

            except (ServerError, APIError) as e:
                code = getattr(e, "code", 500)
                is_transient = isinstance(e, ServerError) or code in (503, 504, 408)
                
                if is_transient:
                    attempt += 1
                    if attempt > max_retries:
                        self._handle_errors(e, request_id)
                    
                    logger.warning(
                        "Gemini API transient failure. Retrying...",
                        extra={
                            "request_id": request_id,
                            "attempt": attempt,
                            "error_type": type(e).__name__,
                            "error_msg": str(e),
                            "delay_seconds": delay
                        }
                    )
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    self._handle_errors(e, request_id)

            except Exception as e:
                # Permanent failure or unexpected SDK exception, raise immediately
                self._handle_errors(e, request_id)

    def _validate_response(self, response, request_id: str):
        """Validates that Gemini returned a valid candidate containing non-empty text."""
        if not response:
            raise ValidationException(
                errors=["Gemini returned an empty response object."],
                message="LLM generation returned an empty result."
            )
            
        if not hasattr(response, "candidates") or not response.candidates:
            raise ValidationException(
                errors=["Response contains no candidates."],
                message="LLM generation yielded no candidate results."
            )
            
        candidate = response.candidates[0]
        # Validate text parts are present
        if not hasattr(candidate, "content") or not candidate.content or not hasattr(candidate.content, "parts") or not candidate.content.parts:
            reason = getattr(candidate, "finish_reason", "UNKNOWN")
            raise ValidationException(
                errors=[f"Response candidate contains no text parts. Finish reason: {reason}"],
                message="LLM generation yielded no content."
            )
            
        # Get response text
        try:
            text = response.text
        except Exception as e:
            raise ValidationException(
                errors=[f"Failed to retrieve response text: {str(e)}"],
                message="LLM generation text extraction failed."
            )
            
        if not text or not text.strip():
            raise ValidationException(
                errors=["Generated response text is empty or whitespace-only."],
                message="LLM generation returned empty text content."
            )

    def _extract_usage(self, response) -> Optional[TokenUsage]:
        """Extracts prompt, candidate, and total token usage counts."""
        if not hasattr(response, "usage_metadata") or not response.usage_metadata:
            return None
        
        meta = response.usage_metadata
        try:
            return TokenUsage(
                input_tokens=meta.prompt_token_count,
                output_tokens=meta.candidates_token_count,
                total_tokens=meta.total_token_count
            )
        except AttributeError:
            return None

    def _extract_finish_reason(self, response) -> FinishReason:
        """Normalizes provider finish reason to system FinishReason enum."""
        if not hasattr(response, "candidates") or not response.candidates:
            return FinishReason.UNKNOWN
            
        candidate = response.candidates[0]
        raw_reason = getattr(candidate, "finish_reason", "UNKNOWN")
        if not raw_reason:
            return FinishReason.UNKNOWN
            
        reason_str = str(raw_reason).upper()
        if "STOP" in reason_str:
            return FinishReason.STOP
        elif "MAX_TOKENS" in reason_str:
            return FinishReason.MAX_TOKENS
        elif "SAFETY" in reason_str or "RECITATION" in reason_str:
            return FinishReason.SAFETY
        elif "ERROR" in reason_str:
            return FinishReason.ERROR
        else:
            return FinishReason.UNKNOWN

    def _handle_errors(self, error: Exception, request_id: str):
        """Translates SDK and connection errors into standard APIException envelopes."""
        # Extract attributes individually
        status_code = getattr(error, "status_code", None)
        if status_code is None:
            status_code = getattr(error, "code", 500) if isinstance(error, APIError) else 500

        message = getattr(error, "message", str(error)) if isinstance(error, APIError) else str(error)
        reason = getattr(error, "reason", "N/A")
        response_attr = getattr(error, "response", "N/A")
        details = getattr(error, "details", "N/A")
        body = getattr(error, "body", "N/A")
        errors_attr = getattr(error, "errors", "N/A")

        # Format and log the complete SDK exception details
        log_message = (
            "\n------------------------------------------------------------\n"
            "Gemini SDK Exception\n"
            f"Exception Type: {type(error).__name__}\n"
            f"HTTP Status: {status_code}\n"
            f"Google Error Code: {status_code}\n"
            f"Google Error Message: {message}\n"
            f"Google Error Details: {details}\n"
            f"Google Error Reason: {reason}\n"
            f"Google Error Response: {response_attr}\n"
            f"Google Error Body: {body}\n"
            f"Google Error Errors: {errors_attr}\n"
            f"Configured Model: {self.default_model}\n"
            f"Request ID: {request_id}\n"
            "------------------------------------------------------------"
        )
        
        logger.error(log_message, exc_info=True)

        if isinstance(error, APIError):
            err_msg_lower = message.lower()
            
            # Check for model support / availability issues
            is_model_error = (
                "not found" in err_msg_lower or 
                "not available" in err_msg_lower or
                "obsolete" in err_msg_lower or
                "deprecated" in err_msg_lower or
                "unavailable" in err_msg_lower or
                status_code == 404
            )
            if is_model_error:
                raise APIException(
                    message=f"Google Gemini model '{self.default_model}' is no longer supported or unavailable: {message}",
                    status_code=400
                )
                
            if status_code in (401, 403):
                raise APIException(
                    message=f"Google Gemini API authentication failed: {message}",
                    status_code=401
                )
            elif status_code == 429:
                raise APIException(
                    message="Google Gemini API rate limit or quota exceeded.",
                    status_code=429
                )
            elif status_code == 400:
                raise ValidationException(
                    errors=[message],
                    message="Google Gemini API parameter validation failed."
                )
            elif status_code in (504, 408):
                raise APIException(
                    message="Google Gemini API request timed out.",
                    status_code=504
                )
            else:
                raise APIException(
                    message=f"Google Gemini API error: {message}",
                    status_code=502
                )
        else:
            # Verify generic HTTP client / sockets timeouts
            err_str = str(error).lower()
            if "timeout" in err_str or "timed out" in err_str:
                raise APIException(
                    message="LLM provider connection timed out.",
                    status_code=504
                )
            raise APIException(
                message=f"Unexpected LLM generation failure: {str(error)}",
                status_code=500
            )
