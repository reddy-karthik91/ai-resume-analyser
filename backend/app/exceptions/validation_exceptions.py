# validation_exceptions.py
# Custom validation-related exceptions for the Flask application.

from .api_exceptions import APIException

class ValidationException(APIException):
    """Exception raised when API request schema validation fails."""
    status_code = 400
    message = "Request validation failed."

    def __init__(self, errors=None, message=None):
        super().__init__(message=message, status_code=400)
        self.errors = errors or []

    def to_dict(self):
        rv = super().to_dict()
        rv['errors'] = self.errors
        return rv
