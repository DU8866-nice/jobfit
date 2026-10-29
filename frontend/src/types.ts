// Mirrors backend/jobfit/schemas.py (AnalysisResult and friends).

export type Language = "en" | "zh";
export type Importance = "must_have" | "nice_to_have";
export type Category = "skill" | "experience" | "education" | "certification" | "other";
export type MatchStatus = "met" | "partial" | "missing";
export type WorkRightsStatus = "not_mentioned" | "required" | "preferred";
export type ReportNote = "not_assessed" | "evidence_not_found";

export interface RequirementReport {
  id: string;
  text: string;
  importance: Importance;
  category: Category;
  keywords: string[];
  status: MatchStatus;
  evidence: string[];
  explanation: string;
  note: ReportNote | null;
}

export interface WorkRightsReport {
  status: WorkRightsStatus;
  detail: string;
  quote: string;
  quote_verified: boolean;
}

export interface ScoreBreakdown {
  overall: number;
  must_have: number | null;
  nice_to_have: number | null;
  counts: { met: number; partial: number; missing: number };
}

export interface Suggestion {
  requirement_ids: string[];
  original: string;
  rewrite: string;
  rationale: string;
}

export interface GroundingStats {
  evidence_cited: number;
  evidence_removed: number;
  suggestions_proposed: number;
  suggestions_removed: number;
  requirements_downgraded: number;
}

export interface AnalysisResult {
  job_title: string;
  company: string;
  provider: string;
  language: Language;
  work_rights: WorkRightsReport;
  score: ScoreBreakdown;
  requirements: RequirementReport[];
  missing_keywords: string[];
  suggestions: Suggestion[];
  summary: string;
  grounding: GroundingStats;
}

export interface ApiErrorBody {
  code: string;
  message: string;
}
