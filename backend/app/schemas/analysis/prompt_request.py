from dataclasses import dataclass

@dataclass(frozen=True)
class PromptRequest:
    """Immutable, provider-agnostic data transfer object representing LLM prompt queries."""
    system_prompt: str
    user_prompt: str
    model: str
    temperature: float
    max_output_tokens: int
    top_p: float
    prompt_version: str
