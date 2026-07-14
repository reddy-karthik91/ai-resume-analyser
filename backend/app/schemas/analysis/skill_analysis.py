from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class SkillAnalysis:
    """Immutable data transfer object representing resume skills categorization."""
    technical_skills: List[str]
    soft_skills: List[str]
    strengths: List[str]
    missing_skills: List[str]
    keyword_matches: List[str]
    keyword_gaps: List[str]
