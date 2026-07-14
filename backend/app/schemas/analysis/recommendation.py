from dataclasses import dataclass
from app.schemas.analysis.analysis_priority import AnalysisPriority
from app.schemas.analysis.recommendation_category import RecommendationCategory

@dataclass(frozen=True)
class Recommendation:
    """Immutable data transfer object representing revision guidance."""
    title: str
    description: str
    priority: AnalysisPriority
    category: RecommendationCategory
