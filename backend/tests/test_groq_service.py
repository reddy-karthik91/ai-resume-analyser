import unittest
from unittest.mock import Mock, patch
from groq import APIError, APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError

class MockAPIError(APIError):
    def __init__(self, message, status_code=500):
        self.status_code = status_code
        self.message = message
        self.body = {"error": {"message": message}}
        super().__init__(
            message=message,
            request=Mock(),
            body=self.body,
            status_code=status_code
        )

from app.schemas.analysis.prompt_request import PromptRequest
from app.schemas.analysis.prompt_response import PromptResponse
from app.schemas.analysis.finish_reason import FinishReason
from app.exceptions.api_exceptions import APIException
from app.exceptions.validation_exceptions import ValidationException
from app.services.groq_service import GroqService

def create_mock_response(text="{\"test\": 1}", model="llama-3.3-70b-versatile", finish_reason="stop", prompt_tokens=10, completion_tokens=20, total_tokens=30, has_content=True):
    response = Mock()
    response.model = model
    
    # Choice mock
    choice = Mock()
    choice.finish_reason = finish_reason
    
    if has_content:
        message = Mock()
        message.content = text
        choice.message = message
    else:
        choice.message = None
        
    response.choices = [choice]
    
    # Usage mock
    usage = Mock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    usage.total_tokens = total_tokens
    response.usage = usage
    
    return response

class TestGroqService(unittest.TestCase):
    """Unit tests for verifying the GroqService execution wrapper using client mocks."""

    def setUp(self):
        self.prompt_request = PromptRequest(
            system_prompt="system",
            user_prompt="user",
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_output_tokens=100,
            top_p=0.9,
            prompt_version="v1"
        )

    def test_successful_generate(self):
        """Assert generate returns populated PromptResponse on success."""
        service = GroqService(api_key="mock-key")
        mock_response = create_mock_response(text="{\"result\": \"success\"}", total_tokens=42)

        with patch("app.services.groq_service.Groq") as mock_client_class:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            response = service.generate(self.prompt_request)

            self.assertIsInstance(response, PromptResponse)
            self.assertEqual(response.content, "{\"result\": \"success\"}")
            self.assertEqual(response.model_used, "llama-3.3-70b-versatile")
            self.assertEqual(response.finish_reason, FinishReason.STOP)
            self.assertIsNotNone(response.token_usage)
            self.assertEqual(response.token_usage.total_tokens, 42)  # type: ignore
            self.assertTrue(response.response_time_ms >= 0)

    def test_empty_key_raises_unauthenticated(self):
        """Assert that missing API key raises APIException wrapper."""
        service = GroqService(api_key=None)
        with self.assertRaises(APIException) as context:
            service.generate(self.prompt_request)
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("API key is missing", context.exception.message)

    def test_response_validation_missing_choices(self):
        """Assert response validation triggers if choice lists are empty."""
        service = GroqService(api_key="mock-key")
        mock_response = Mock()
        mock_response.choices = []

        with patch("app.services.groq_service.Groq") as mock_client_class:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            with self.assertRaises(ValidationException) as context:
                service.generate(self.prompt_request)
            self.assertIn("did not produce any candidate completions", context.exception.message)

    def test_response_validation_empty_content(self):
        """Assert empty choices message payloads raise ValidationExceptions."""
        service = GroqService(api_key="mock-key")
        mock_response = create_mock_response(has_content=False)

        with patch("app.services.groq_service.Groq") as mock_client_class:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            with self.assertRaises(ValidationException) as context:
                service.generate(self.prompt_request)
            self.assertIn("choice message is missing", context.exception.message)

    def test_response_validation_empty_or_whitespace_text(self):
        """Assert empty and whitespace-only text responses raise ValidationExceptions."""
        service = GroqService(api_key="mock-key")
        mock_response_empty = create_mock_response(text="")
        mock_response_whitespace = create_mock_response(text="   ")

        with patch("app.services.groq_service.Groq") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Empty text check
            mock_client.chat.completions.create.return_value = mock_response_empty
            with self.assertRaises(ValidationException) as context:
                service.generate(self.prompt_request)
            self.assertIn("empty text content", context.exception.message)

            # Whitespace text check
            mock_client.chat.completions.create.return_value = mock_response_whitespace
            with self.assertRaises(ValidationException) as context:
                service.generate(self.prompt_request)
            self.assertIn("empty text content", context.exception.message)

    def test_permanent_exceptions_mapping(self):
        """Assert permanent provider exceptions are converted directly without retries."""
        service = GroqService(api_key="mock-key", max_retries=3)

        with patch("app.services.groq_service.Groq") as mock_client_class:
            mock_client = Mock()
            # Authentication Error (401)
            mock_client.chat.completions.create.side_effect = AuthenticationError(
                message="Invalid key",
                response=Mock(),
                body={"error": {"message": "Invalid key"}}
            )
            mock_client_class.return_value = mock_client

            with self.assertRaises(APIException) as context:
                service.generate(self.prompt_request)
            self.assertEqual(context.exception.status_code, 401)
            self.assertIn("authentication failed", context.exception.message.lower())
            self.assertEqual(mock_client.chat.completions.create.call_count, 1)

    def test_transient_exceptions_and_backoff_retries(self):
        """Assert that transient failures are retried and eventually fail mapping correctly."""
        # Using 0 delay in service to run test instantly
        service = GroqService(api_key="mock-key", max_retries=2, retry_delay_seconds=0)

        with patch("app.services.groq_service.Groq") as mock_client_class:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = RateLimitError(
                message="Limit exceeded",
                response=Mock(),
                body={"error": {"message": "Limit exceeded"}}
            )
            mock_client_class.return_value = mock_client

            with self.assertRaises(APIException) as context:
                service.generate(self.prompt_request)
            self.assertEqual(context.exception.status_code, 429)
            # Expecting call count of: 1 initial attempt + 2 retry attempts = 3 total attempts
            self.assertEqual(mock_client.chat.completions.create.call_count, 3)
