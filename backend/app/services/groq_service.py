import time
import uuid
import logging
from typing import Optional
from groq import Groq
from groq import APIError, APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError

from app.schemas.analysis.prompt_request import PromptRequest
from app.schemas.analysis.prompt_response import PromptResponse
from app.schemas.analysis.finish_reason import FinishReason
from app.schemas.analysis.token_usage import TokenUsage
from app.exceptions.api_exceptions import APIException
from app.exceptions.validation_exceptions import ValidationException

logger = logging.getLogger(__name__)

class GroqService:
    """Service responsible for communicating with Groq API using the official groq SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay_seconds: Optional[int] = None
    ):
        """Initializes GroqService with configuration settings."""
        self.api_key = api_key
        self.default_model = default_model or "llama-3.3-70b-versatile"
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else 60
        self.max_retries = max_retries if max_retries is not None else 2
        self.retry_delay_seconds = retry_delay_seconds if retry_delay_seconds is not None else 2

        import importlib.metadata
        try:
            sdk_version = importlib.metadata.version("groq")
        except Exception:
            sdk_version = "unknown"

        logger.info(
            "Groq configuration loaded:\n"
            f"api_key_present={self.api_key is not None}\n"
            f"configured_model={self.default_model}\n"
            f"sdk_version={sdk_version}\n"
            f"timeout={self.timeout_seconds}\n"
            f"max_retries={self.max_retries}"
        )

    def generate(self, request: PromptRequest) -> PromptResponse:
        """
        Executes model generation using Groq Chat Completions endpoint.
        
        Args:
            request: Standardized PromptRequest containing system and user prompts.
            
        Returns:
            A populated PromptResponse DTO.
        """
        request_id = str(uuid.uuid4())
        client = self._configure_client()

        logger.info(
            "Groq request initiation",
            extra={
                "request_id": request_id,
                "model": request.model or self.default_model,
                "prompt_version": request.prompt_version,
                "status": "initiated"
            }
        )

        raw_response, duration_ms, retry_count = self._execute_request(client, request, request_id)
        self._validate_response(raw_response, request_id)

        token_usage = self._extract_usage(raw_response)
        finish_reason = self._extract_finish_reason(raw_response)

        choice = raw_response.choices[0]
        content_text = choice.message.content

        logger.info(
            "Groq request completed successfully",
            extra={
                "request_id": request_id,
                "model": raw_response.model,
                "response_time_ms": duration_ms,
                "retry_count": retry_count,
                "finish_reason": finish_reason.name,
                "status": "success"
            }
        )

        return PromptResponse(
            content=content_text,
            model_used=raw_response.model,
            finish_reason=finish_reason,
            token_usage=token_usage,
            response_time_ms=duration_ms
        )

    def _configure_client(self) -> Groq:
        """Configures and returns a new Groq client instance."""
        if not self.api_key:
            raise APIException(
                message="Groq API key is missing. Configure GROQ_API_KEY environment variable.",
                status_code=401
            )
        try:
            return Groq(
                api_key=self.api_key,
                timeout=float(self.timeout_seconds)
            )
        except Exception as e:
            raise APIException(
                message=f"Failed to initialize Groq Client: {str(e)}",
                status_code=500
            )

    def _execute_request(self, client: Groq, request: PromptRequest, request_id: str):
        """Sends generation command to completions.create endpoint implementing backoffs."""
        attempt = 0
        max_retries = self.max_retries
        delay = self.retry_delay_seconds

        while True:
            try:
                start_time = time.perf_counter()
                
                response = client.chat.completions.create(
                    model=request.model or self.default_model,
                    messages=[
                        {"role": "system", "content": request.system_prompt},
                        {"role": "user", "content": request.user_prompt}
                    ],
                    temperature=request.temperature,
                    max_tokens=request.max_output_tokens,
                    response_format={"type": "json_object"}
                )
                
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                return response, duration_ms, attempt

            except (RateLimitError, APIConnectionError, APITimeoutError, APIError) as e:
                status_code = getattr(e, "status_code", 500)
                # Retry on rate limits or connection/timeout issues
                is_transient = isinstance(e, (RateLimitError, APIConnectionError, APITimeoutError)) or status_code in (503, 504, 408)
                
                if is_transient:
                    attempt += 1
                    if attempt > max_retries:
                        self._handle_errors(e, request_id)
                    
                    logger.warning(
                        "Groq API transient failure. Retrying...",
                        extra={
                            "request_id": request_id,
                            "attempt": attempt,
                            "error_type": type(e).__name__,
                            "error_msg": str(e),
                            "delay_seconds": delay
                        }
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    self._handle_errors(e, request_id)

            except Exception as e:
                self._handle_errors(e, request_id)

    def _validate_response(self, response, request_id: str):
        """Validates that Groq returned a valid completion message."""
        if not response:
            raise ValidationException(
                errors=["Groq returned an empty response object."],
                message="LLM generation returned an empty result."
            )
            
        if not hasattr(response, "choices") or not response.choices:
            raise ValidationException(
                errors=["Response contains no choices."],
                message="LLM generation did not produce any candidate completions."
            )
            
        choice = response.choices[0]
        if not hasattr(choice, "message") or not choice.message:
            raise ValidationException(
                errors=["Choice contains no message payload."],
                message="LLM generation choice message is missing."
            )
            
        content = getattr(choice.message, "content", None)
        if content is None or not str(content).strip():
            raise ValidationException(
                errors=["Message content is empty or null."],
                message="LLM generation produced empty text content."
            )

    def _extract_usage(self, response) -> Optional[TokenUsage]:
        """Extracts token usage metadata from raw Groq response."""
        if not hasattr(response, "usage") or not response.usage:
            return None
        usage = response.usage
        return TokenUsage(
            input_tokens=getattr(usage, "prompt_tokens", 0),
            output_tokens=getattr(usage, "completion_tokens", 0),
            total_tokens=getattr(usage, "total_tokens", 0)
        )

    def _extract_finish_reason(self, response) -> FinishReason:
        """Extracts and normalizes finish reasons."""
        if not hasattr(response, "choices") or not response.choices:
            return FinishReason.UNKNOWN
            
        choice = response.choices[0]
        raw_reason = getattr(choice, "finish_reason", "UNKNOWN")
        if not raw_reason:
            return FinishReason.UNKNOWN
            
        reason_str = str(raw_reason).upper()
        if "STOP" in reason_str:
            return FinishReason.STOP
        elif "LENGTH" in reason_str:
            return FinishReason.MAX_TOKENS
        elif "CONTENT_FILTER" in reason_str:
            return FinishReason.SAFETY
        else:
            return FinishReason.UNKNOWN

    def _handle_errors(self, error: Exception, request_id: str):
        """Translates Groq SDK errors into standard APIException envelopes."""
        status_code = getattr(error, "status_code", 500)
        message = getattr(error, "message", str(error))
        body = getattr(error, "body", "N/A")

        # Verbose Logging
        log_message = (
            "\n------------------------------------------------------------\n"
            "Groq SDK Exception\n"
            f"Exception Type: {type(error).__name__}\n"
            f"HTTP Status: {status_code}\n"
            f"Groq Error Message: {message}\n"
            f"Groq Error Body: {body}\n"
            f"Configured Model: {self.default_model}\n"
            f"Request ID: {request_id}\n"
            "------------------------------------------------------------"
        )
        logger.error(log_message, exc_info=True)

        if isinstance(error, AuthenticationError) or status_code in (401, 403):
            raise APIException(
                message=f"Groq API authentication failed: {message}",
                status_code=401
            )
        elif isinstance(error, RateLimitError) or status_code == 429:
            raise APIException(
                message="Groq API rate limit or quota exceeded.",
                status_code=429
            )
        elif status_code == 404:
            raise APIException(
                message=f"Groq model '{self.default_model}' is no longer supported or unavailable: {message}",
                status_code=400
            )
        elif status_code in (504, 408) or isinstance(error, APITimeoutError):
            raise APIException(
                message="Groq API request timed out.",
                status_code=504
            )
        elif isinstance(error, APIError):
            raise APIException(
                message=f"Groq API error: {message}",
                status_code=502
            )
        else:
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
