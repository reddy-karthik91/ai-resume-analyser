from dataclasses import dataclass

@dataclass(frozen=True)
class TokenUsage:
    """Immutable data transfer object representing completion token telemetry statistics."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
