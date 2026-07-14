# Output Schema

Your output MUST be a single, valid JSON object matching the following structure:

```json
{
  "ats_score": {
    "score": 85,
    "grade": "B+", // Must be one of: A+, A, B+, B, C, D, F
    "confidence": 0.95,
    "feedback": "Strong structure with slight keyword gaps."
  },
  "summary": {
    "summary": "Professional summary statement description...",
    "overall_feedback": "Constructive high-level summary overview feedback...",
    "professional_level": "MID_LEVEL" // Must be one of: ENTRY_LEVEL, JUNIOR, MID_LEVEL, SENIOR, LEAD, ARCHITECT
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
      "priority": "HIGH", // Must be one of: LOW, MEDIUM, HIGH, CRITICAL
      "category": "EXPERIENCE" // Must be one of: SUMMARY, FORMATTING, TECHNICAL_SKILLS, SOFT_SKILLS, PROJECTS, EXPERIENCE, EDUCATION, CERTIFICATIONS, KEYWORDS, GENERAL
    }
  ],
  "overall_score": 85.0
}
```

Do not wrap the JSON output in markdown blocks or include any introductory/concluding text. Return ONLY the raw JSON string.
