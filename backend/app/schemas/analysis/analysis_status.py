from enum import Enum

class AnalysisStatus(Enum):
    """Enum representing operational states of asynchronous analysis pipelines."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    PROCESSING = "PROCESSING"
