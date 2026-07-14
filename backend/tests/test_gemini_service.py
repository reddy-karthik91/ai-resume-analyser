import unittest
from unittest.mock import Mock, patch
from google.genai.errors import APIError, ClientError, ServerError

class MockAPIError(APIError):
    def __init__(self, message, code=500):
        super().__init__(code, {"message": message})
        self.code = code
        self.message = message

class MockServerError(ServerError):
    def __init__(self, message, code=500):
        super().__init__(code, {"message": message})
        self.code = code
        self.message = message

from app.schemas.analysis.prompt_request import PromptRequest
from app.schemas.analysis.prompt_response import PromptResponse
from app.schemas.analysis.finish_reason import FinishReason
from app.exceptions.api_exceptions import APIException
from app.exceptions.validation_exceptions import ValidationException
from app.services.gemini_service import GeminiService

def create_mock_response(text="{\"test\": 1}", model="gemini-2.5-flash", finish_reason="STOP", prompt_tokens=10, candidate_tokens=20, total_tokens=30, has_content=True):
    response = Mock()
    response.text = text
    response.model = model
    
    # Candidate mock
    candidate = Mock()
    candidate.finish_reason = finish_reason
    
    if has_content:
        part = Mock()
        part.text = text
        content = Mock()
        content.parts = [part]
        candidate.content = content
    else:
        candidate.content = None
        
    response.candidates = [candidate]
    
    # Usage metadata mock
    usage = Mock()
    usage.prompt_token_count = prompt_tokens
    usage.candidates_token_count = candidate_tokens
    usage.total_token_count = total_tokens
    response.usage_metadata = usage
    
    return response

class TestGeminiService(unittest.TestCase):
    """Unit tests for verifying the GeminiService execution wrapper using client mocks."""

    def setUp(self):
        self.prompt_request = PromptRequest(
            system_prompt="system",
            user_prompt="user",
            model="gemini-2.5-flash",
            temperature=0.1,
            max_output_tokens=100,
            top_p=0.9,
            prompt_version="v1"
        )

    def test_successful_generate(self):
        """Assert generate returns populated PromptResponse on success."""
        service = GeminiService(api_key="mock-key")
        mock_response = create_mock_response(text="{\"result\": \"success\"}", total_tokens=42)

        with patch("google.genai.Client") as mock_client_class:
            mock_client = Mock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            response = service.generate(self.prompt_request)

            self.assertIsInstance(response, PromptResponse)
            self.assertEqual(response.content, "{\"result\": \"success\"}")
            self.assertEqual(response.model_used, "gemini-2.5-flash")
            self.assertEqual(response.finish_reason, FinishReason.STOP)
            self.assertIsNotNone(response.token_usage)
            self.assertEqual(response.token_usage.total_tokens, 42)  # type: ignore
            self.assertTrue(response.response_time_ms >= 0)

    def test_empty_key_raises_unauthenticated(self):
        """Assert that missing API key raises APIException wrapper."""
        service = GeminiService(api_key=None)
        with self.assertRaises(APIException) as context:
            service.generate(self.prompt_request)
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("API key is missing", context.exception.message)

    def test_response_validation_missing_candidate(self):
        """Assert response validation triggers if candidate lists are empty."""
        service = GeminiService(api_key="mock-key")
        mock_response = Mock()
        mock_response.candidates = []

        with patch("google.genai.Client") as mock_client_class:
            mock_client = Mock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            with self.assertRaises(ValidationException) as context:
                service.generate(self.prompt_request)
            self.assertIn("yielded no candidate results", context.exception.message)

    def test_response_validation_empty_content(self):
        """Assert empty candidate contents raise ValidationExceptions."""
        service = GeminiService(api_key="mock-key")
        mock_response = create_mock_response(has_content=False, finish_reason="SAFETY")

        with patch("google.genai.Client") as mock_client_class:
            mock_client = Mock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            with self.assertRaises(ValidationException) as context:
                service.generate(self.prompt_request)
            self.assertIn("yielded no content", context.exception.message)

    def test_response_validation_empty_or_whitespace_text(self):
        """Assert empty and whitespace-only text responses raise ValidationExceptions."""
        service = GeminiService(api_key="mock-key")
        mock_response_empty = create_mock_response(text="")
        mock_response_whitespace = create_mock_response(text="   ")

        with patch("google.genai.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Empty text check
            mock_client.models.generate_content.return_value = mock_response_empty
            with self.assertRaises(ValidationException) as context:
                service.generate(self.prompt_request)
            self.assertIn("returned empty text content", context.exception.message)

            # Whitespace text check
            mock_client.models.generate_content.return_value = mock_response_whitespace
            with self.assertRaises(ValidationException) as context:
                service.generate(self.prompt_request)
            self.assertIn("returned empty text content", context.exception.message)

    def test_permanent_exceptions_mapping(self):
        """Assert permanent provider exceptions are converted directly without retries."""
        service = GeminiService(api_key="mock-key", max_retries=3)

        with patch("google.genai.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # 401 Authentication check
            mock_client.models.generate_content.side_effect = MockAPIError("Invalid key", code=403)
            with self.assertRaises(APIException) as context:
                service.generate(self.prompt_request)
            self.assertEqual(context.exception.status_code, 401)
            # Verify side_effect called exactly once (no retries)
            self.assertEqual(mock_client.models.generate_content.call_count, 1)

            # 429 Quota check
            mock_client.models.generate_content.reset_mock()
            mock_client.models.generate_content.side_effect = MockAPIError("Rate limit", code=429)
            with self.assertRaises(APIException) as context:
                service.generate(self.prompt_request)
            self.assertEqual(context.exception.status_code, 429)
            self.assertEqual(mock_client.models.generate_content.call_count, 1)

    def test_transient_retries_and_exponential_backoff(self):
        """Assert transient errors trigger retries up to limit, then wrap exceptions."""
        # 1 retry limit, starting delay 0.01 seconds for fast testing
        service = GeminiService(api_key="mock-key", max_retries=1, retry_delay_seconds=0.01)

        with patch("google.genai.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock transient failure: Timeout code 504 ServerError
            mock_client.models.generate_content.side_effect = MockServerError("Timeout", code=504)
            
            with self.assertRaises(APIException) as context:
                service.generate(self.prompt_request)
                
            self.assertEqual(context.exception.status_code, 504)
            # Verify side_effect called exactly 2 times (1 setup + 1 retry)
            self.assertEqual(mock_client.models.generate_content.call_count, 2)

    def test_request_id_correlation_in_logs(self):
        """Assert that every generate request maps a unique request_id in standard log streams."""
        service = GeminiService(api_key="mock-key")
        mock_response = create_mock_response(text="John Doe content")

        with patch("google.genai.Client") as mock_client_class:
            mock_client = Mock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            with self.assertLogs("app.services.gemini_service", level="INFO") as log_capture:
                service.generate(self.prompt_request)

            # Verify request ID presence in LogRecord attributes
            for record in log_capture.records:
                self.assertTrue(hasattr(record, "request_id"))
                self.assertTrue(len(record.request_id) > 0)
            
            log_messages = "\n".join(log_capture.output)
            self.assertIn("Gemini request initiation", log_messages)
            self.assertIn("Gemini request completed successfully", log_messages)
