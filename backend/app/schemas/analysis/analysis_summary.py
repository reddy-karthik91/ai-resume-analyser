from dataclasses import dataclass
from app.schemas.analysis.professional_level import ProfessionalLevel

@dataclass(frozen=True)
class AnalysisSummary:
    """Immutable data transfer object representing executive parsed resume summaries."""
    summary: str
    overall_feedback: str
    professional_level: ProfessionalLevel
