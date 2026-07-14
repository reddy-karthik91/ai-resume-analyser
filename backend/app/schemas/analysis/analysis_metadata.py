from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class AnalysisMetadata:
    """Immutable DTO mapping telemetry execution context for an AI processing cycle."""
    provider: str
    model_used: str
    analysis_duration_ms: int
    analysis_timestamp: datetime
    prompt_version: str
