from enum import Enum

class FinishReason(Enum):
    """Enum representing termination status reasons returned from LLM completions."""
    STOP = "STOP"
    MAX_TOKENS = "MAX_TOKENS"
    SAFETY = "SAFETY"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"
