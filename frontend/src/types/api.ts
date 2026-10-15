export type ErrorDetail = {
  code: string
  message: string
  details?: Record<string, unknown> | null
}

export type APIErrorBody = {
  error: ErrorDetail
}

export type APIResponse<T> = {
  success: boolean
  data: T
  meta?: Record<string, unknown> | null
}

export type HealthData = {
  status: string
  service: string
  timestamp: string
}

export type ResumeFormat = 'pdf' | 'docx'

export type ResumeParseData = {
  filename: string
  format: ResumeFormat
  size_bytes: number
  page_count?: number | null
  character_count: number
  word_count: number
  text: string
}

export type ResumeParseMeta = {
  job_title: string
  company_name?: string | null
  job_description_length: number
}

export type JobDetails = {
  jobTitle: string
  companyName: string
  jobDescription: string
}

export type RequirementCategory =
  | 'required_technical_skills'
  | 'preferred_skills'
  | 'tools_frameworks'
  | 'experience_responsibilities'
  | 'education_certifications'
  | 'domain_soft_skills'

export type MatchStatus =
  | 'matched'
  | 'partially_demonstrated'
  | 'missing'
  | 'uncertain'

export type RequirementFinding = {
  requirement_id: string
  label: string
  category: RequirementCategory
  importance: 'required' | 'preferred' | 'nice_to_have'
  status: MatchStatus
  score_contribution: number
  evidence: string[]
  notes?: string | null
}

export type CategoryScore = {
  category: RequirementCategory
  score: number
  matched: number
  partial: number
  missing: number
  uncertain: number
  total: number
}

export type ScoringBreakdown = {
  overall_alignment: number
  required_skill_coverage: number
  preferred_skill_coverage: number
  category_scores: CategoryScore[]
  methodology: string
  disclaimer: string
}

export type ATSComponentScore = {
  id: string
  label: string
  nominal_weight: number
  effective_weight: number
  score: number | null
  available: boolean
  explanation: string
}

export type ATSRecommendedFix = {
  title: string
  rationale: string
  impact: 'high' | 'medium' | 'low'
}

export type ATSCompatibilityResult = {
  status: 'available' | 'unavailable' | 'insufficient_data'
  overall_score: number | null
  label: string
  disclaimer: string
  methodology: string
  components: ATSComponentScore[]
  positive_signals: string[]
  improvement_opportunities: string[]
  missing_keywords: string[]
  structural_warnings: string[]
  parsing_warnings: string[]
  recommended_fixes: ATSRecommendedFix[]
}

export type ResumeParseContext = {
  format?: ResumeFormat | null
  word_count?: number | null
  character_count?: number | null
  page_count?: number | null
}

export type ResumeProfile = {
  explicit_skills: string[]
  demonstrated_skills: string[]
  achievements: string[]
  responsibilities: string[]
  education: string[]
  certifications: string[]
}

export type AnalysisResult = {
  job_title: string
  company_name?: string | null
  record_id?: string | null
  analysis: {
    findings: RequirementFinding[]
    scoring: ScoringBreakdown
    resume_profile: ResumeProfile
    ats_compatibility?: ATSCompatibilityResult | null
  }
  recommendations: {
    enabled: boolean
    provider: 'openai' | 'deterministic_fallback' | 'disabled'
    gap_explanations: string[]
    skill_improvements: Array<{
      title: string
      rationale: string
      grounded_in: 'gap' | 'partial_match' | 'existing_evidence'
      related_requirements: string[]
    }>
    learning_topics: string[]
    project_ideas: string[]
    resume_bullet_suggestions: string[]
    learning_plan: Array<{
      title: string
      focus: string
      estimated_effort: string
      actions: string[]
    }>
    notes?: string | null
  }
}

export type RunAnalysisPayload = JobDetails & {
  resumeText: string
  requestAiRecommendations: boolean
  aiConsent: boolean
  saveToHistory: boolean
  resumeFilename?: string | null
  resumeParseContext?: ResumeParseContext | null
}

export type AnalysisHistoryItem = {
  id: string
  created_at: string
  job_title: string
  company_name?: string | null
  resume_filename?: string | null
  overall_alignment: number
  required_skill_coverage: number
  ats_compatibility_score?: number | null
}

export type StoredAnalysisRecord = {
  id: string
  created_at: string
  job_title: string
  company_name?: string | null
  resume_filename?: string | null
  data: AnalysisResult
}
