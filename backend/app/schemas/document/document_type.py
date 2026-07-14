from enum import Enum

class DocumentType(Enum):
    """Enum representing supported document categories."""
    RESUME = "RESUME"
    JOB_DESCRIPTION = "JOB_DESCRIPTION"
    COVER_LETTER = "COVER_LETTER"
    CERTIFICATE = "CERTIFICATE"
    EXPERIENCE_LETTER = "EXPERIENCE_LETTER"
    UNKNOWN = "UNKNOWN"
