from typing import List

from app.schemas.analysis import (
    AIRecommendations,
    DeterministicAnalysisResult,
    GroundedRecommendation,
    LearningPlanStep,
    MatchStatus,
)


def build_fallback_recommendations(analysis: DeterministicAnalysisResult) -> AIRecommendations:
    missing = [f for f in analysis.findings if f.status == MatchStatus.MISSING]
    partial = [f for f in analysis.findings if f.status == MatchStatus.PARTIAL]

    gap_explanations: List[str] = []
    for finding in missing[:5]:
        gap_explanations.append(
            f"The job description calls out \"{finding.label}\", but the resume text does not provide clear evidence.",
        )

    skill_improvements: List[GroundedRecommendation] = []
    for finding in (missing + partial)[:6]:
        grounded = "gap" if finding.status == MatchStatus.MISSING else "partial_match"
        skill_improvements.append(
            GroundedRecommendation(
                title=f"Strengthen evidence for {finding.label}",
                rationale=(
                    "This requirement appears in the job description. Add verifiable examples only if you truly have them."
                ),
                grounded_in=grounded,
                related_requirements=[finding.label],
            ),
        )

    learning_topics = [finding.label for finding in missing[:5]]
    project_ideas = [
        f"Build a small portfolio project that demonstrates {finding.label} in a realistic workflow."
        for finding in missing[:3]
    ]

    resume_bullets = [
        (
            "Suggested bullet (only if accurate): Quantify an accomplishment that demonstrates "
            f"{finding.label} (metrics, scope, or outcome)."
        )
        for finding in partial[:4]
    ]

    learning_plan = [
        LearningPlanStep(
            title="Close highest-priority gaps",
            focus=", ".join(finding.label for finding in missing[:3]) or "Core role requirements",
            estimated_effort="2–4 weeks",
            actions=[
                "Review the missing requirements listed in the deterministic findings.",
                "Study fundamentals and implement one focused practice exercise per gap.",
            ],
        ),
        LearningPlanStep(
            title="Improve resume evidence",
            focus="Translate existing work into requirement-aligned bullets",
            estimated_effort="1 week",
            actions=[
                "Rewrite experience bullets to mirror the job description language where truthful.",
                "Keep claims tied to projects, responsibilities, or certifications already on the resume.",
            ],
        ),
    ]

    return AIRecommendations(
        enabled=True,
        provider="deterministic_fallback",
        gap_explanations=gap_explanations,
        skill_improvements=skill_improvements,
        learning_topics=learning_topics,
        project_ideas=project_ideas,
        resume_bullet_suggestions=resume_bullets,
        learning_plan=learning_plan,
        notes="Generated without an external LLM using deterministic gap analysis.",
    )
