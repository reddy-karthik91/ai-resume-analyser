from dataclasses import dataclass
from uuid import UUID
from typing import List
from app.schemas.analysis.ats_score import ATSScore
from app.schemas.analysis.analysis_summary import AnalysisSummary
from app.schemas.analysis.skill_analysis import SkillAnalysis
from app.schemas.analysis.recommendation import Recommendation
from app.schemas.analysis.analysis_metadata import AnalysisMetadata
from app.schemas.analysis.analysis_status import AnalysisStatus

@dataclass(frozen=True)
class ResumeAnalysisResult:
    """Immutable aggregate root representing structured resume assessment results."""
    document_id: UUID
    ats_score: ATSScore
    summary: AnalysisSummary
    skill_analysis: SkillAnalysis
    recommendations: List[Recommendation]
    analysis_metadata: AnalysisMetadata
    analysis_status: AnalysisStatus
    analysis_successful: bool
    overall_score: float
