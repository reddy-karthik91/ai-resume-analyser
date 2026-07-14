# api_exceptions.py
# Custom API-related exceptions for the Flask application.

class APIException(Exception):
    """Base exception class for all custom API errors."""
    status_code = 500
    message = "An unexpected server error occurred."

    def __init__(self, message=None, status_code=None, payload=None):
        if message is not None:
            self.message = message
        super().__init__(self.message)
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['success'] = False
        return rv


class InvalidResumeException(APIException):
    """Exception raised when a resume cannot be read or contains malformed data."""
    status_code = 400
    message = "The uploaded resume is invalid or could not be parsed."


class UnsupportedFileException(APIException):
    """Exception raised when the uploaded file extension or MIME type is not allowed."""
    status_code = 415
    message = "The uploaded file format is unsupported. Only PDF files are allowed."


class AIServiceException(APIException):
    """Exception raised when calls to the AI analysis engine (OpenAI API) fail or timeout."""
    status_code = 503
    message = "The AI analysis service is temporarily unavailable. Please try again later."
