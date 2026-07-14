from dataclasses import dataclass
from typing import Optional
from app.schemas.analysis.finish_reason import FinishReason
from app.schemas.analysis.token_usage import TokenUsage

@dataclass(frozen=True)
class PromptResponse:
    """Immutable, provider-agnostic data transfer object representing raw completions."""
    content: str
    model_used: str
    finish_reason: FinishReason
    response_time_ms: int
    token_usage: Optional[TokenUsage] = None
