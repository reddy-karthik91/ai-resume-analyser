from dataclasses import dataclass

@dataclass(frozen=True)
class PageContent:
    """Immutable data transfer object representing the extracted content of a single page."""
    page_number: int  # 1-indexed page number
    text: str
    word_count: int
    character_count: int
    has_text: bool
