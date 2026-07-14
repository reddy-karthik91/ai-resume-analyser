export interface ATSScore {
  score: number;
  grade: string;
  confidence: number;
  feedback: string;
}

export interface AnalysisSummary {
  summary: string;
  overall_feedback: string;
  professional_level: string;
}

export interface SkillAnalysis {
  technical_skills: string[];
  soft_skills: string[];
  strengths: string[];
  missing_skills: string[];
  keyword_matches: string[];
  keyword_gaps: string[];
}

export interface Recommendation {
  title: string;
  description: string;
  priority: string;
  category: string;
}

export interface AnalysisMetadata {
  provider: string;
  model_used: string;
  analysis_duration_ms: number;
  analysis_timestamp: string;
  prompt_version: string;
}

export interface ResumeAnalysisResult {
  document_id: string;
  ats_score: ATSScore;
  summary: AnalysisSummary;
  skill_analysis: SkillAnalysis;
  recommendations: Recommendation[];
  analysis_metadata: AnalysisMetadata;
  analysis_status: string;
  analysis_successful: boolean;
  overall_score: number;
}

export interface AnalysisResponseEnvelope {
  success: boolean;
  message: string;
  data: ResumeAnalysisResult;
  errors: string[] | null;
  timestamp: string;
}
