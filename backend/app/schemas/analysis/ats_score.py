from dataclasses import dataclass
from app.schemas.analysis.ats_grade import ATSGrade

@dataclass(frozen=True)
class ATSScore:
    """Immutable data transfer object representing quantified ATS compatibility results."""
    score: int
    grade: ATSGrade
    confidence: float
    feedback: str
