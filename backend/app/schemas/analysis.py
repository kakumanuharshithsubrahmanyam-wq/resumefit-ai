from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class RequirementCategory(str, Enum):
    REQUIRED_TECHNICAL = "required_technical_skills"
    PREFERRED = "preferred_skills"
    TOOLS_FRAMEWORKS = "tools_frameworks"
    EXPERIENCE = "experience_responsibilities"
    EDUCATION = "education_certifications"
    DOMAIN_SOFT = "domain_soft_skills"


class RequirementImportance(str, Enum):
    REQUIRED = "required"
    PREFERRED = "preferred"
    NICE_TO_HAVE = "nice_to_have"


class MatchStatus(str, Enum):
    MATCHED = "matched"
    PARTIAL = "partially_demonstrated"
    MISSING = "missing"
    UNCERTAIN = "uncertain"


class ExtractedRequirement(BaseModel):
    id: str
    label: str
    category: RequirementCategory
    importance: RequirementImportance
    source_text: str


class ResumeSkillEvidence(BaseModel):
    skill: str
    mention_type: Literal["explicit", "demonstrated"]
    evidence: str


class ResumeProfile(BaseModel):
    explicit_skills: List[str]
    demonstrated_skills: List[str]
    achievements: List[str]
    responsibilities: List[str]
    education: List[str]
    certifications: List[str]
    skill_evidence: List[ResumeSkillEvidence]


class RequirementFinding(BaseModel):
    requirement_id: str
    label: str
    category: RequirementCategory
    importance: RequirementImportance
    status: MatchStatus
    score_contribution: float = Field(..., ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class CategoryScore(BaseModel):
    category: RequirementCategory
    score: float = Field(..., ge=0.0, le=100.0)
    matched: int
    partial: int
    missing: int
    uncertain: int
    total: int


class ScoringBreakdown(BaseModel):
    overall_alignment: float = Field(..., ge=0.0, le=100.0)
    required_skill_coverage: float = Field(..., ge=0.0, le=100.0)
    preferred_skill_coverage: float = Field(..., ge=0.0, le=100.0)
    category_scores: List[CategoryScore]
    methodology: str
    disclaimer: str


class ResumeParseContext(BaseModel):
    """Optional upload metadata to improve ATS parsing-quality estimates."""

    format: Optional[Literal["pdf", "docx"]] = None
    word_count: Optional[int] = Field(default=None, ge=0)
    character_count: Optional[int] = Field(default=None, ge=0)
    page_count: Optional[int] = Field(default=None, ge=0)


class ATSComponentScore(BaseModel):
    id: str
    label: str
    nominal_weight: float = Field(..., ge=0.0, le=1.0)
    effective_weight: float = Field(..., ge=0.0, le=1.0)
    score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    available: bool
    explanation: str


class ATSRecommendedFix(BaseModel):
    title: str
    rationale: str
    impact: Literal["high", "medium", "low"]


class ATSCompatibilityResult(BaseModel):
    status: Literal["available", "unavailable", "insufficient_data"]
    overall_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    label: str = "Estimated ATS Compatibility"
    disclaimer: str
    methodology: str
    components: List[ATSComponentScore] = Field(default_factory=list)
    positive_signals: List[str] = Field(default_factory=list)
    improvement_opportunities: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    structural_warnings: List[str] = Field(default_factory=list)
    parsing_warnings: List[str] = Field(default_factory=list)
    recommended_fixes: List[ATSRecommendedFix] = Field(default_factory=list)


class StructuredRequirements(BaseModel):
    items: List[ExtractedRequirement]


class DeterministicAnalysisResult(BaseModel):
    requirements: StructuredRequirements
    resume_profile: ResumeProfile
    findings: List[RequirementFinding]
    scoring: ScoringBreakdown
    ats_compatibility: Optional[ATSCompatibilityResult] = None


class LearningPlanStep(BaseModel):
    title: str
    focus: str
    estimated_effort: str
    actions: List[str]


class GroundedRecommendation(BaseModel):
    title: str
    rationale: str
    grounded_in: Literal["gap", "partial_match", "existing_evidence"]
    related_requirements: List[str] = Field(default_factory=list)


class AIRecommendations(BaseModel):
    enabled: bool
    provider: Literal["openai", "deterministic_fallback", "disabled"]
    gap_explanations: List[str] = Field(default_factory=list)
    skill_improvements: List[GroundedRecommendation] = Field(default_factory=list)
    learning_topics: List[str] = Field(default_factory=list)
    project_ideas: List[str] = Field(default_factory=list)
    resume_bullet_suggestions: List[str] = Field(default_factory=list)
    learning_plan: List[LearningPlanStep] = Field(default_factory=list)
    notes: Optional[str] = None


class AnalysisRequest(BaseModel):
    resume_text: str = Field(..., min_length=40, max_length=50000)
    job_title: str = Field(..., min_length=1, max_length=200)
    job_description: str = Field(..., min_length=20, max_length=20000)
    company_name: Optional[str] = Field(default=None, max_length=200)
    request_ai_recommendations: bool = False
    ai_consent: bool = False
    save_to_history: bool = False
    resume_filename: Optional[str] = Field(default=None, max_length=255)
    resume_parse_context: Optional[ResumeParseContext] = None


class AnalysisData(BaseModel):
    job_title: str
    company_name: Optional[str] = None
    analysis: DeterministicAnalysisResult
    recommendations: AIRecommendations
    record_id: Optional[str] = None


class AnalysisHistoryItem(BaseModel):
    id: str
    created_at: datetime
    job_title: str
    company_name: Optional[str] = None
    resume_filename: Optional[str] = None
    overall_alignment: float = Field(..., ge=0.0, le=100.0)
    required_skill_coverage: float = Field(..., ge=0.0, le=100.0)
    ats_compatibility_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)


class StoredAnalysisRecord(BaseModel):
    id: str
    created_at: datetime
    job_title: str
    company_name: Optional[str] = None
    resume_filename: Optional[str] = None
    data: AnalysisData
