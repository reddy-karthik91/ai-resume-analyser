import uuid
import unittest
from datetime import datetime, timezone
from dataclasses import asdict, FrozenInstanceError
from app.schemas.analysis import (
    ATSGrade,
    ATSScore,
    ProfessionalLevel,
    AnalysisSummary,
    SkillAnalysis,
    RecommendationCategory,
    AnalysisPriority,
    Recommendation,
    AnalysisStatus,
    FinishReason,
    TokenUsage,
    AnalysisMetadata,
    PromptRequest,
    PromptResponse,
    ResumeAnalysisResult
)

class TestAnalysisDomainModel(unittest.TestCase):
    """Unit tests for validating the Sprint 4 AI Domain Model Layer."""

    def test_enums_creation_and_values(self):
        """Assert enums values and labels are mapped correctly."""
        self.assertEqual(ATSGrade.A_PLUS.value, "A+")
        self.assertEqual(ProfessionalLevel.SENIOR.value, "SENIOR")
        self.assertEqual(RecommendationCategory.TECHNICAL_SKILLS.value, "TECHNICAL_SKILLS")
        self.assertEqual(AnalysisPriority.CRITICAL.value, "CRITICAL")
        self.assertEqual(AnalysisStatus.SUCCESS.value, "SUCCESS")
        self.assertEqual(FinishReason.STOP.value, "STOP")

    def test_frozen_dataclasses_immutability(self):
        """Assert that all domain dataclasses are frozen (immutable)."""
        score = ATSScore(score=85, grade=ATSGrade.B_PLUS, confidence=0.9, feedback="Good")
        with self.assertRaises(FrozenInstanceError):
            score.score = 90  # type: ignore

        usage = TokenUsage(input_tokens=10, output_tokens=5, total_tokens=15)
        with self.assertRaises(FrozenInstanceError):
            usage.total_tokens = 20  # type: ignore

    def test_aggregate_root_construction_and_composition(self):
        """Assert nested aggregate root construction maps DTO fields and optional formats cleanly."""
        doc_id = uuid.uuid4()
        
        ats = ATSScore(score=92, grade=ATSGrade.A, confidence=0.98, feedback="Excellent fit.")
        summary = AnalysisSummary(
            summary="Senior frontend engineer.",
            overall_feedback="Excellent portfolio.",
            professional_level=ProfessionalLevel.SENIOR
        )
        skills = SkillAnalysis(
            technical_skills=["Angular", "TypeScript", "Python"],
            soft_skills=["Leadership", "Communication"],
            strengths=["Architecture design"],
            missing_skills=["Docker"],
            keyword_matches=["Angular", "Python"],
            keyword_gaps=["Docker"]
        )
        rec = Recommendation(
            title="Add Docker details",
            description="Detail Docker deployment experience.",
            priority=AnalysisPriority.MEDIUM,
            category=RecommendationCategory.TECHNICAL_SKILLS
        )
        meta = AnalysisMetadata(
            provider="gemini",
            model_used="gemini-1.5-pro",
            analysis_duration_ms=450,
            analysis_timestamp=datetime.now(timezone.utc),
            prompt_version="v1.2.0"
        )

        result = ResumeAnalysisResult(
            document_id=doc_id,
            ats_score=ats,
            summary=summary,
            skill_analysis=skills,
            recommendations=[rec],
            analysis_metadata=meta,
            analysis_status=AnalysisStatus.SUCCESS,
            analysis_successful=True,
            overall_score=92.0
        )

        # Assert composition
        self.assertEqual(result.document_id, doc_id)
        self.assertEqual(result.ats_score.score, 92)
        self.assertEqual(result.summary.professional_level, ProfessionalLevel.SENIOR)
        self.assertEqual(len(result.skill_analysis.technical_skills), 3)
        self.assertEqual(result.recommendations[0].title, "Add Docker details")
        self.assertEqual(result.analysis_metadata.provider, "gemini")
        self.assertEqual(result.analysis_status, AnalysisStatus.SUCCESS)
        self.assertTrue(result.analysis_successful)
        self.assertEqual(result.overall_score, 92.0)

    def test_prompt_request_and_response_fields(self):
        """Assert PromptRequest and PromptResponse initialization and optional usage."""
        req = PromptRequest(
            system_prompt="Act as an ATS",
            user_prompt="Analyze resume text",
            model="gemini-1.5-flash",
            temperature=0.2,
            max_output_tokens=1024,
            top_p=0.9,
            prompt_version="v1.0"
        )
        self.assertEqual(req.model, "gemini-1.5-flash")
        self.assertEqual(req.temperature, 0.2)

        # PromptResponse with token usage
        usage = TokenUsage(100, 200, 300)
        res_with_usage = PromptResponse(
            content="{}",
            model_used="gemini-1.5-flash",
            finish_reason=FinishReason.STOP,
            token_usage=usage,
            response_time_ms=350
        )
        self.assertIsNotNone(res_with_usage.token_usage)
        self.assertEqual(res_with_usage.token_usage.total_tokens, 300)  # type: ignore

        # PromptResponse without token usage (optional field)
        res_no_usage = PromptResponse(
            content="{}",
            model_used="gemini-1.5-flash",
            finish_reason=FinishReason.STOP,
            token_usage=None,
            response_time_ms=350
        )
        self.assertIsNone(res_no_usage.token_usage)

    def test_asdict_serialization(self):
        """Assert standard dataclasses.asdict() recursively serializes enums and DTO models."""
        doc_id = uuid.uuid4()
        ats = ATSScore(score=70, grade=ATSGrade.C, confidence=0.8, feedback="Okay")
        summary = AnalysisSummary("Summary", "Feedback", ProfessionalLevel.JUNIOR)
        skills = SkillAnalysis([], [], [], [], [], [])
        meta = AnalysisMetadata("openai", "gpt-4o", 100, datetime.now(timezone.utc), "v1")
        
        result = ResumeAnalysisResult(
            document_id=doc_id,
            ats_score=ats,
            summary=summary,
            skill_analysis=skills,
            recommendations=[],
            analysis_metadata=meta,
            analysis_status=AnalysisStatus.PARTIAL,
            analysis_successful=False,
            overall_score=70.0
        )

        serialized = asdict(result)
        
        self.assertEqual(serialized["document_id"], doc_id)
        self.assertEqual(serialized["ats_score"]["score"], 70)
        # asdict retains Enums as objects inside the dict, verified in route serializer mapping
        self.assertEqual(serialized["ats_score"]["grade"], ATSGrade.C)
        self.assertEqual(serialized["summary"]["professional_level"], ProfessionalLevel.JUNIOR)
        self.assertEqual(serialized["recommendations"], [])
        self.assertFalse(serialized["analysis_successful"])
        self.assertEqual(serialized["overall_score"], 70.0)
