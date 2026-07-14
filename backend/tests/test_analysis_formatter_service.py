import json
import unittest
from uuid import uuid4
from datetime import datetime

from app.schemas.analysis.prompt_response import PromptResponse
from app.schemas.analysis.finish_reason import FinishReason
from app.schemas.analysis.ats_grade import ATSGrade
from app.schemas.analysis.professional_level import ProfessionalLevel
from app.schemas.analysis.analysis_priority import AnalysisPriority
from app.schemas.analysis.recommendation_category import RecommendationCategory
from app.schemas.analysis.resume_analysis_result import ResumeAnalysisResult
from app.exceptions.validation_exceptions import ValidationException
from app.services.analysis_formatter_service import AnalysisFormatterService

VALID_JSON_CONTENT = """{
  "ats_score": {
    "score": 85,
    "grade": "B+",
    "confidence": 0.95,
    "feedback": "Strong structure with slight keyword gaps."
  },
  "summary": {
    "summary": "Professional summary statement description...",
    "overall_feedback": "Constructive high-level summary overview feedback...",
    "professional_level": "MID_LEVEL"
  },
  "skill_analysis": {
    "technical_skills": ["Angular", "Python", "Flask"],
    "soft_skills": ["Teamwork", "Problem Solving"],
    "strengths": ["Quantified metrics listed in experience sections."],
    "missing_skills": ["Docker", "Kubernetes"],
    "keyword_matches": ["TypeScript", "HTML"],
    "keyword_gaps": ["CI/CD"]
  },
  "recommendations": [
    {
      "title": "Add Quantified Achievements",
      "description": "Quantify outcomes of major projects using percentages or values.",
      "priority": "HIGH",
      "category": "EXPERIENCE"
    }
  ],
  "overall_score": 85.0
}"""

class TestAnalysisFormatterService(unittest.TestCase):
    """Unit tests validating the AnalysisFormatterService parsing and validation policies."""

    def setUp(self):
        self.formatter = AnalysisFormatterService()
        self.document_id = uuid4()
        self.prompt_response = PromptResponse(
            content=VALID_JSON_CONTENT,
            model_used="gemini-2.5-flash",
            finish_reason=FinishReason.STOP,
            response_time_ms=1200
        )

    def test_successful_formatting(self):
        """Assert valid PromptResponse successfully deserializes into ResumeAnalysisResult."""
        result = self.formatter.format(self.document_id, self.prompt_response)
        
        self.assertIsInstance(result, ResumeAnalysisResult)
        self.assertEqual(result.document_id, self.document_id)
        self.assertEqual(result.overall_score, 85.0)
        self.assertTrue(result.analysis_successful)
        
        # Check ats_score
        self.assertEqual(result.ats_score.score, 85)
        self.assertEqual(result.ats_score.grade, ATSGrade.B_PLUS)
        self.assertEqual(result.ats_score.confidence, 0.95)
        self.assertEqual(result.ats_score.feedback, "Strong structure with slight keyword gaps.")
        
        # Check summary
        self.assertEqual(result.summary.professional_level, ProfessionalLevel.MID_LEVEL)
        self.assertEqual(result.summary.summary, "Professional summary statement description...")
        
        # Check skills
        self.assertEqual(result.skill_analysis.technical_skills, ["Angular", "Python", "Flask"])
        
        # Check recommendations
        self.assertEqual(len(result.recommendations), 1)
        self.assertEqual(result.recommendations[0].title, "Add Quantified Achievements")
        self.assertEqual(result.recommendations[0].priority, AnalysisPriority.HIGH)
        self.assertEqual(result.recommendations[0].category, RecommendationCategory.EXPERIENCE)
        
        # Check metadata mapping from PromptResponse
        self.assertEqual(result.analysis_metadata.model_used, "gemini-2.5-flash")
        self.assertEqual(result.analysis_metadata.analysis_duration_ms, 1200)
        self.assertEqual(result.analysis_metadata.provider, "Google Gemini")

    def test_malformed_json_rejection(self):
        """Assert invalid JSON syntax throws a ValidationException."""
        bad_response = PromptResponse(
            content="{invalid json syntax",
            model_used="gemini-2.5-flash",
            finish_reason=FinishReason.STOP,
            response_time_ms=100
        )
        with self.assertRaises(ValidationException) as context:
            self.formatter.format(self.document_id, bad_response)
        self.assertIn("invalid JSON syntax", context.exception.message)

    def test_structural_validation_missing_key(self):
        """Assert JSON missing top level fields is rejected."""
        data = json.loads(VALID_JSON_CONTENT)
        del data["ats_score"]
        
        bad_response = PromptResponse(
            content=json.dumps(data),
            model_used="gemini-2.5-flash",
            finish_reason=FinishReason.STOP,
            response_time_ms=100
        )
        with self.assertRaises(ValidationException) as context:
            self.formatter.format(self.document_id, bad_response)
        self.assertIn("Missing top-level section: 'ats_score'", context.exception.errors[0])

    def test_structural_validation_incorrect_type(self):
        """Assert fields matching wrong primitive types are rejected."""
        data = json.loads(VALID_JSON_CONTENT)
        data["overall_score"] = "eighty-five"  # string instead of float/int
        
        bad_response = PromptResponse(
            content=json.dumps(data),
            model_used="gemini-2.5-flash",
            finish_reason=FinishReason.STOP,
            response_time_ms=100
        )
        with self.assertRaises(ValidationException) as context:
            self.formatter.format(self.document_id, bad_response)
        self.assertIn("overall_score' must be a number", context.exception.errors[0])

    def test_business_validation_score_out_of_range(self):
        """Assert score parameter range boundaries are strictly checked."""
        data = json.loads(VALID_JSON_CONTENT)
        data["ats_score"]["score"] = 105  # > 100
        
        bad_response = PromptResponse(
            content=json.dumps(data),
            model_used="gemini-2.5-flash",
            finish_reason=FinishReason.STOP,
            response_time_ms=100
        )
        with self.assertRaises(ValidationException) as context:
            self.formatter.format(self.document_id, bad_response)
        self.assertIn("ats_score.score' has invalid range", context.exception.errors[0])

    def test_business_validation_confidence_out_of_range(self):
        """Assert confidence parameter range boundaries are checked."""
        data = json.loads(VALID_JSON_CONTENT)
        data["ats_score"]["confidence"] = 1.2  # > 1.0
        
        bad_response = PromptResponse(
            content=json.dumps(data),
            model_used="gemini-2.5-flash",
            finish_reason=FinishReason.STOP,
            response_time_ms=100
        )
        with self.assertRaises(ValidationException) as context:
            self.formatter.format(self.document_id, bad_response)
        self.assertIn("ats_score.confidence' has invalid range", context.exception.errors[0])

    def test_business_validation_empty_recommendations(self):
        """Assert empty recommendations array fails business validation."""
        data = json.loads(VALID_JSON_CONTENT)
        data["recommendations"] = []
        
        bad_response = PromptResponse(
            content=json.dumps(data),
            model_used="gemini-2.5-flash",
            finish_reason=FinishReason.STOP,
            response_time_ms=100
        )
        with self.assertRaises(ValidationException) as context:
            self.formatter.format(self.document_id, bad_response)
        self.assertIn("Recommendations list cannot be empty", context.exception.errors[0])

    def test_business_validation_empty_title_in_recs(self):
        """Assert empty/whitespace titles inside recommendations trigger validation failure."""
        data = json.loads(VALID_JSON_CONTENT)
        data["recommendations"][0]["title"] = "   "
        
        bad_response = PromptResponse(
            content=json.dumps(data),
            model_used="gemini-2.5-flash",
            finish_reason=FinishReason.STOP,
            response_time_ms=100
        )
        with self.assertRaises(ValidationException) as context:
            self.formatter.format(self.document_id, bad_response)
        self.assertIn("title' in recommendation 0 cannot be empty or whitespace", context.exception.errors[0])

    def test_business_validation_invalid_enum_grade(self):
        """Assert invalid qualitative grade strings raise validation failure."""
        data = json.loads(VALID_JSON_CONTENT)
        data["ats_score"]["grade"] = "Z+"  # invalid enum
        
        bad_response = PromptResponse(
            content=json.dumps(data),
            model_used="gemini-2.5-flash",
            finish_reason=FinishReason.STOP,
            response_time_ms=100
        )
        with self.assertRaises(ValidationException) as context:
            self.formatter.format(self.document_id, bad_response)
        self.assertIn("grade' enum value", context.exception.errors[0])

    def test_validation_failure_logging_attributes_and_privacy(self):
        """Assert that validation failures log operational attributes but do NOT print PII or content text."""
        bad_content = "{invalid json content"
        bad_response = PromptResponse(
            content=bad_content,
            model_used="gemini-2.5-flash",
            finish_reason=FinishReason.STOP,
            response_time_ms=100
        )
        
        with self.assertLogs("app.services.analysis_formatter_service", level="ERROR") as log_capture:
            try:
                self.formatter.format(self.document_id, bad_response)
            except ValidationException:
                pass
                
        # Check logs structure and ensure privacy compliance
        for record in log_capture.records:
            self.assertEqual(record.levelname, "ERROR")
            self.assertTrue(hasattr(record, "document_id"))
            self.assertEqual(record.document_id, str(self.document_id))
            self.assertTrue(hasattr(record, "validation_error"))
            self.assertTrue(hasattr(record, "response_length"))
            self.assertEqual(record.response_length, len(bad_content))
            self.assertEqual(record.status, "failed")
            
            # Ensure the raw JSON string or prompt is not present in record variables or message
            self.assertNotIn(bad_content, record.message)
