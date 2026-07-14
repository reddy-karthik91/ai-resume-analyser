import json
import logging
import math
from uuid import UUID
from datetime import datetime
from typing import Optional, List

from app.schemas.analysis.ats_grade import ATSGrade
from app.schemas.analysis.ats_score import ATSScore
from app.schemas.analysis.professional_level import ProfessionalLevel
from app.schemas.analysis.analysis_summary import AnalysisSummary
from app.schemas.analysis.skill_analysis import SkillAnalysis
from app.schemas.analysis.recommendation_category import RecommendationCategory
from app.schemas.analysis.analysis_priority import AnalysisPriority
from app.schemas.analysis.recommendation import Recommendation
from app.schemas.analysis.analysis_status import AnalysisStatus
from app.schemas.analysis.analysis_metadata import AnalysisMetadata
from app.schemas.analysis.prompt_response import PromptResponse
from app.schemas.analysis.resume_analysis_result import ResumeAnalysisResult
from app.exceptions.validation_exceptions import ValidationException

logger = logging.getLogger(__name__)

class AnalysisFormatterService:
    """Service responsible for parsing and validating PromptResponse and formatting it to ResumeAnalysisResult DTO."""

    def format(self, document_id: UUID, response: PromptResponse) -> ResumeAnalysisResult:
        """
        Formats raw model prompt response into a strongly-typed, validated ResumeAnalysisResult aggregate.
        
        Args:
            document_id: UUID of the related document.
            response: Intermediate PromptResponse returned by GeminiService.
            
        Returns:
            A parsed, structured, and validated ResumeAnalysisResult.
        """
        request_id = None
        
        logger.info(
            "Analysis format initiation",
            extra={
                "request_id": request_id,
                "document_id": str(document_id),
                "status": "initiated"
            }
        )
        
        # 1. Parse JSON
        parsed_data = self._parse_json(response.content, document_id, request_id)
        
        # 2. Structural validation checks
        self._validate_structure(parsed_data, document_id, request_id)
        
        # 3. Business rule validation checks
        self._validate_business_rules(parsed_data, document_id, request_id)
        
        # 4. Construct Nested DTO structures
        ats_data = parsed_data["ats_score"]
        ats_score = ATSScore(
            score=int(ats_data["score"]),
            grade=ATSGrade(ats_data["grade"]),
            confidence=float(ats_data["confidence"]),
            feedback=ats_data["feedback"]
        )
        
        sum_data = parsed_data["summary"]
        summary = AnalysisSummary(
            summary=sum_data["summary"],
            overall_feedback=sum_data["overall_feedback"],
            professional_level=ProfessionalLevel(sum_data["professional_level"])
        )
        
        skills_data = parsed_data["skill_analysis"]
        skill_analysis = SkillAnalysis(
            technical_skills=skills_data["technical_skills"],
            soft_skills=skills_data["soft_skills"],
            strengths=skills_data["strengths"],
            missing_skills=skills_data["missing_skills"],
            keyword_matches=skills_data["keyword_matches"],
            keyword_gaps=skills_data["keyword_gaps"]
        )
        
        recs_list = []
        for r in parsed_data["recommendations"]:
            recs_list.append(
                Recommendation(
                    title=r["title"],
                    description=r["description"],
                    priority=AnalysisPriority(r["priority"]),
                    category=RecommendationCategory(r["category"])
                )
            )
            
        # Build metadata directly from PromptResponse telemetry
        metadata = AnalysisMetadata(
            provider="Google Gemini",
            model_used=response.model_used,
            analysis_duration_ms=response.response_time_ms,
            analysis_timestamp=datetime.utcnow(),
            prompt_version="v1.0.0"
        )
        
        logger.info(
            "Analysis format completed successfully",
            extra={
                "request_id": request_id,
                "document_id": str(document_id),
                "recommendation_count": len(recs_list),
                "analysis_duration": response.response_time_ms,
                "model": response.model_used,
                "status": "success"
            }
        )
        
        return ResumeAnalysisResult(
            document_id=document_id,
            ats_score=ats_score,
            summary=summary,
            skill_analysis=skill_analysis,
            recommendations=recs_list,
            analysis_metadata=metadata,
            analysis_status=AnalysisStatus.SUCCESS,
            analysis_successful=True,
            overall_score=float(parsed_data["overall_score"])
        )

    def _parse_json(self, content: str, document_id: UUID, request_id: Optional[str]) -> dict:
        """Parses response string text into a JSON object dict, failing fast if parsing fails."""
        if not content or not content.strip():
            msg = "AI prompt response content is empty."
            self._log_validation_failure(document_id, msg, 0, request_id)
            raise ValidationException(
                errors=[msg],
                message="Formatting failed: empty content returned from model."
            )
            
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            msg = f"JSON decoding failed: {str(e)}"
            self._log_validation_failure(document_id, msg, len(content), request_id)
            raise ValidationException(
                errors=[msg],
                message="Formatting failed: invalid JSON syntax returned from model."
            )

    def _validate_structure(self, data: dict, document_id: UUID, request_id: Optional[str]):
        """Stage 1 Structural Validation: Checks fields exist and are of appropriate types."""
        # Top-level checks
        required_keys = ["ats_score", "summary", "skill_analysis", "recommendations", "overall_score"]
        for key in required_keys:
            if key not in data:
                msg = f"Missing top-level section: '{key}'."
                self._log_validation_failure(document_id, msg, 0, request_id)
                raise ValidationException(errors=[msg], message="JSON structure validation failed.")

        # ats_score structure
        ats = data["ats_score"]
        if not isinstance(ats, dict):
            msg = "Section 'ats_score' must be an object."
            self._log_validation_failure(document_id, msg, 0, request_id)
            raise ValidationException(errors=[msg], message="JSON structure validation failed.")
            
        for f in ["score", "grade", "confidence", "feedback"]:
            if f not in ats:
                msg = f"Missing required field in 'ats_score': '{f}'."
                self._log_validation_failure(document_id, msg, 0, request_id)
                raise ValidationException(errors=[msg], message="JSON structure validation failed.")
        
        # summary structure
        summary = data["summary"]
        if not isinstance(summary, dict):
            msg = "Section 'summary' must be an object."
            self._log_validation_failure(document_id, msg, 0, request_id)
            raise ValidationException(errors=[msg], message="JSON structure validation failed.")
            
        for f in ["summary", "overall_feedback", "professional_level"]:
            if f not in summary:
                msg = f"Missing required field in 'summary': '{f}'."
                self._log_validation_failure(document_id, msg, 0, request_id)
                raise ValidationException(errors=[msg], message="JSON structure validation failed.")

        # skill_analysis structure
        skills = data["skill_analysis"]
        if not isinstance(skills, dict):
            msg = "Section 'skill_analysis' must be an object."
            self._log_validation_failure(document_id, msg, 0, request_id)
            raise ValidationException(errors=[msg], message="JSON structure validation failed.")
            
        skill_fields = ["technical_skills", "soft_skills", "strengths", "missing_skills", "keyword_matches", "keyword_gaps"]
        for f in skill_fields:
            if f not in skills:
                msg = f"Missing required field in 'skill_analysis': '{f}'."
                self._log_validation_failure(document_id, msg, 0, request_id)
                raise ValidationException(errors=[msg], message="JSON structure validation failed.")
            if not isinstance(skills[f], list):
                msg = f"Field 'skill_analysis.{f}' must be a list."
                self._log_validation_failure(document_id, msg, 0, request_id)
                raise ValidationException(errors=[msg], message="JSON structure validation failed.")

        # recommendations structure
        recs = data["recommendations"]
        if not isinstance(recs, list):
            msg = "Section 'recommendations' must be a list."
            self._log_validation_failure(document_id, msg, 0, request_id)
            raise ValidationException(errors=[msg], message="JSON structure validation failed.")
            
        for i, r in enumerate(recs):
            if not isinstance(r, dict):
                msg = f"Recommendation at index {i} must be an object."
                self._log_validation_failure(document_id, msg, 0, request_id)
                raise ValidationException(errors=[msg], message="JSON structure validation failed.")
            for f in ["title", "description", "priority", "category"]:
                if f not in r:
                    msg = f"Missing required field in recommendation {i}: '{f}'."
                    self._log_validation_failure(document_id, msg, 0, request_id)
                    raise ValidationException(errors=[msg], message="JSON structure validation failed.")

        # overall_score structure check
        if not isinstance(data["overall_score"], (int, float)):
            msg = "Field 'overall_score' must be a number."
            self._log_validation_failure(document_id, msg, 0, request_id)
            raise ValidationException(errors=[msg], message="JSON structure validation failed.")

    def _validate_business_rules(self, data: dict, document_id: UUID, request_id: Optional[str]):
        """Stage 2 Business Rules Validation: Checks ranges, enums, and non-emptiness constraints."""
        # 1. overall_score boundaries
        oscore = data["overall_score"]
        if not isinstance(oscore, (int, float)) or not math.isfinite(oscore) or not (0.0 <= oscore <= 100.0):
            msg = f"Field 'overall_score' has invalid range: {oscore}."
            self._log_validation_failure(document_id, msg, 0, request_id)
            raise ValidationException(errors=[msg], message="Business rule validation failed.")

        # 2. ats_score boundaries
        ats = data["ats_score"]
        score = ats["score"]
        if not isinstance(score, (int, float)) or not math.isfinite(score) or not (0.0 <= score <= 100.0) or isinstance(score, bool):
            msg = f"Field 'ats_score.score' has invalid range or type: {score}."
            self._log_validation_failure(document_id, msg, 0, request_id)
            raise ValidationException(errors=[msg], message="Business rule validation failed.")

        confidence = ats["confidence"]
        if not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not (0.0 <= confidence <= 1.0) or isinstance(confidence, bool):
            msg = f"Field 'ats_score.confidence' has invalid range or type: {confidence}."
            self._log_validation_failure(document_id, msg, 0, request_id)
            raise ValidationException(errors=[msg], message="Business rule validation failed.")

        feedback = ats["feedback"]
        if not isinstance(feedback, str) or not feedback.strip():
            msg = "Field 'ats_score.feedback' cannot be empty or whitespace-only."
            self._log_validation_failure(document_id, msg, 0, request_id)
            raise ValidationException(errors=[msg], message="Business rule validation failed.")

        raw_grade = ats["grade"]
        try:
            ATSGrade(raw_grade)
        except ValueError:
            msg = f"Invalid 'ats_score.grade' enum value: '{raw_grade}'."
            self._log_validation_failure(document_id, msg, 0, request_id)
            raise ValidationException(errors=[msg], message="Business rule validation failed.")

        # 3. summary boundaries
        summary = data["summary"]
        prof_lvl = summary["professional_level"]
        try:
            ProfessionalLevel(prof_lvl)
        except ValueError:
            msg = f"Invalid 'summary.professional_level' enum value: '{prof_lvl}'."
            self._log_validation_failure(document_id, msg, 0, request_id)
            raise ValidationException(errors=[msg], message="Business rule validation failed.")

        for f in ["summary", "overall_feedback"]:
            if not isinstance(summary[f], str) or not summary[f].strip():
                msg = f"Field 'summary.{f}' cannot be empty or whitespace-only."
                self._log_validation_failure(document_id, msg, 0, request_id)
                raise ValidationException(errors=[msg], message="Business rule validation failed.")

        # 4. skill_analysis boundaries
        skills = data["skill_analysis"]
        for f in ["technical_skills", "soft_skills", "strengths", "missing_skills", "keyword_matches", "keyword_gaps"]:
            for i, val in enumerate(skills[f]):
                if not isinstance(val, str) or not val.strip():
                    msg = f"List element in 'skill_analysis.{f}' at index {i} cannot be empty or whitespace-only."
                    self._log_validation_failure(document_id, msg, 0, request_id)
                    raise ValidationException(errors=[msg], message="Business rule validation failed.")

        # 5. recommendations boundaries
        recs = data["recommendations"]
        if len(recs) == 0:
            msg = "Recommendations list cannot be empty."
            self._log_validation_failure(document_id, msg, 0, request_id)
            raise ValidationException(errors=[msg], message="Business rule validation failed.")

        for i, r in enumerate(recs):
            for f in ["title", "description"]:
                val = r[f]
                if not isinstance(val, str) or not val.strip():
                    msg = f"Field '{f}' in recommendation {i} cannot be empty or whitespace-only."
                    self._log_validation_failure(document_id, msg, 0, request_id)
                    raise ValidationException(errors=[msg], message="Business rule validation failed.")
            
            raw_priority = r["priority"]
            try:
                AnalysisPriority(raw_priority)
            except ValueError:
                msg = f"Invalid priority enum '{raw_priority}' in recommendation {i}."
                self._log_validation_failure(document_id, msg, 0, request_id)
                raise ValidationException(errors=[msg], message="Business rule validation failed.")

            raw_cat = r["category"]
            try:
                RecommendationCategory(raw_cat)
            except ValueError:
                msg = f"Invalid category enum '{raw_cat}' in recommendation {i}."
                self._log_validation_failure(document_id, msg, 0, request_id)
                raise ValidationException(errors=[msg], message="Business rule validation failed.")

    def _log_validation_failure(self, document_id: UUID, error_msg: str, response_length: int, request_id: Optional[str]):
        """Logs validation failures safely, ensuring no candidate PII is exposed."""
        logger.error(
            "Validation failed during AI response formatting.",
            extra={
                "request_id": request_id,
                "document_id": str(document_id),
                "validation_error": error_msg,
                "response_length": response_length,
                "status": "failed"
            }
        )
