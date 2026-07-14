from enum import Enum

class RecommendationCategory(Enum):
    """Enum representing specific candidate areas of improvement categories."""
    SUMMARY = "SUMMARY"
    FORMATTING = "FORMATTING"
    TECHNICAL_SKILLS = "TECHNICAL_SKILLS"
    SOFT_SKILLS = "SOFT_SKILLS"
    PROJECTS = "PROJECTS"
    EXPERIENCE = "EXPERIENCE"
    EDUCATION = "EDUCATION"
    CERTIFICATIONS = "CERTIFICATIONS"
    KEYWORDS = "KEYWORDS"
    GENERAL = "GENERAL"
