from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class DocumentMetadata:
    """Immutable data transfer object representing measurable metadata of the parsed document."""
    page_count: int
    word_count: int
    character_count: int
    parsing_time_ms: int
    has_extractable_text: bool
    language: Optional[str] = None
