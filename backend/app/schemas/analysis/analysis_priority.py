from enum import Enum

class AnalysisPriority(Enum):
    """Enum representing prioritize levels of recommended resume revisions."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
