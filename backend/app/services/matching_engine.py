from typing import Dict, List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.data.skill_lexicon import ALL_CANONICAL_SKILLS, canonicalize_skill, expand_skill_variants
from app.schemas.analysis import (
    CategoryScore,
    DeterministicAnalysisResult,
    ExtractedRequirement,
    MatchStatus,
    RequirementCategory,
    RequirementFinding,
    RequirementImportance,
    ResumeProfile,
    ScoringBreakdown,
    StructuredRequirements,
)
from app.services.requirement_extractor import extract_requirements
from app.services.resume_analyzer import analyze_resume
from app.services.text_utils import find_skill_mentions, split_sentences

STATUS_POINTS = {
    MatchStatus.MATCHED: 1.0,
    MatchStatus.PARTIAL: 0.55,
    MatchStatus.UNCERTAIN: 0.25,
    MatchStatus.MISSING: 0.0,
}

CATEGORY_WEIGHTS: Dict[RequirementCategory, float] = {
    RequirementCategory.REQUIRED_TECHNICAL: 0.35,
    RequirementCategory.TOOLS_FRAMEWORKS: 0.15,
    RequirementCategory.EXPERIENCE: 0.20,
    RequirementCategory.PREFERRED: 0.10,
    RequirementCategory.EDUCATION: 0.10,
    RequirementCategory.DOMAIN_SOFT: 0.10,
}

SCORE_METHODOLOGY = (
    "Weighted deterministic score: category weights "
    "(required technical 35%, tools 15%, experience 20%, preferred 10%, education 10%, domain/soft 10%). "
    "Each requirement contributes matched=1.0, partial=0.55, uncertain=0.25, missing=0.0, "
    "multiplied by importance (required×1.0, preferred×0.7, nice-to-have×0.5)."
)

SCORE_DISCLAIMER = (
    "This score measures textual alignment between your resume and the supplied job description. "
    "It is not a prediction of interview success or hiring probability."
)


def _importance_weight(importance: RequirementImportance) -> float:
    if importance == RequirementImportance.REQUIRED:
        return 1.0
    if importance == RequirementImportance.PREFERRED:
        return 0.7
    return 0.5


def _best_similarity(requirement_text: str, resume_text: str) -> float:
    sentences = split_sentences(resume_text)
    if not sentences:
        return 0.0
    corpus = [requirement_text, *sentences]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
    try:
        matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        return 0.0
    req_vec = matrix[0:1]
    resume_vecs = matrix[1:]
    if resume_vecs.shape[0] == 0:
        return 0.0
    similarities = cosine_similarity(req_vec, resume_vecs)[0]
    return float(max(similarities))


def _match_skill_requirement(label: str, resume_text: str, profile: ResumeProfile) -> Tuple[MatchStatus, List[str], Optional[str]]:
    canonical = canonicalize_skill(label)
    if canonical in ALL_CANONICAL_SKILLS or label.lower() in ALL_CANONICAL_SKILLS:
        skill = canonical if canonical in ALL_CANONICAL_SKILLS else label.lower()
        variants = list(expand_skill_variants(skill))
        mentions = find_skill_mentions(resume_text, variants)
        if mentions:
            if skill in profile.explicit_skills:
                return MatchStatus.MATCHED, [snippet for _, snippet in mentions[:3]], "Explicitly listed on resume."
            if skill in profile.demonstrated_skills:
                return MatchStatus.MATCHED, [snippet for _, snippet in mentions[:3]], "Demonstrated in experience/projects."
            return MatchStatus.PARTIAL, [snippet for _, snippet in mentions[:2]], "Mentioned without strong section context."
        return MatchStatus.MISSING, [], "No direct mention found in resume text."

    similarity = _best_similarity(label, resume_text)
    if similarity >= 0.28:
        evidence_sentence = max(
            split_sentences(resume_text),
            key=lambda sentence: _best_similarity(label, sentence),
            default="",
        )
        return MatchStatus.PARTIAL, [evidence_sentence] if evidence_sentence else [], "Semantic overlap with role language."
    if similarity >= 0.14:
        evidence_sentence = max(
            split_sentences(resume_text),
            key=lambda sentence: _best_similarity(label, sentence),
            default="",
        )
        return MatchStatus.UNCERTAIN, [evidence_sentence] if evidence_sentence else [], "Limited evidence; manual review recommended."
    return MatchStatus.MISSING, [], "Insufficient evidence in resume text."


def _score_requirements(findings: List[RequirementFinding]) -> ScoringBreakdown:
    category_totals: Dict[RequirementCategory, Dict[str, float]] = {}
    category_counts: Dict[RequirementCategory, Dict[str, int]] = {}

    required_points = 0.0
    required_total = 0.0
    preferred_points = 0.0
    preferred_total = 0.0

    weighted_sum = 0.0
    weight_sum = 0.0

    for finding in findings:
        cat = finding.category
        category_totals.setdefault(cat, {"points": 0.0, "weight": 0.0})
        category_counts.setdefault(
            cat,
            {"matched": 0, "partial": 0, "missing": 0, "uncertain": 0, "total": 0},
        )
        importance_w = _importance_weight(finding.importance)
        category_w = CATEGORY_WEIGHTS.get(cat, 0.05)
        combined_weight = importance_w * category_w
        points = STATUS_POINTS[finding.status] * importance_w

        category_totals[cat]["points"] += points
        category_totals[cat]["weight"] += importance_w
        category_counts[cat]["total"] += 1
        if finding.status == MatchStatus.MATCHED:
            category_counts[cat]["matched"] += 1
        elif finding.status == MatchStatus.PARTIAL:
            category_counts[cat]["partial"] += 1
        elif finding.status == MatchStatus.UNCERTAIN:
            category_counts[cat]["uncertain"] += 1
        else:
            category_counts[cat]["missing"] += 1

        weighted_sum += STATUS_POINTS[finding.status] * combined_weight
        weight_sum += combined_weight

        if finding.importance == RequirementImportance.REQUIRED:
            required_points += STATUS_POINTS[finding.status]
            required_total += 1.0
        elif finding.importance == RequirementImportance.PREFERRED:
            preferred_points += STATUS_POINTS[finding.status]
            preferred_total += 1.0

    category_scores: List[CategoryScore] = []
    for category in RequirementCategory:
        totals = category_totals.get(category, {"points": 0.0, "weight": 0.0})
        counts = category_counts.get(
            category,
            {"matched": 0, "partial": 0, "missing": 0, "uncertain": 0, "total": 0},
        )
        score = 0.0
        if totals["weight"] > 0:
            score = (totals["points"] / totals["weight"]) * 100.0
        category_scores.append(
            CategoryScore(
                category=category,
                score=round(score, 1),
                matched=counts["matched"],
                partial=counts["partial"],
                missing=counts["missing"],
                uncertain=counts["uncertain"],
                total=counts["total"],
            ),
        )

    overall = (weighted_sum / weight_sum * 100.0) if weight_sum else 0.0
    required_cov = (required_points / required_total * 100.0) if required_total else 0.0
    preferred_cov = (preferred_points / preferred_total * 100.0) if preferred_total else 0.0

    return ScoringBreakdown(
        overall_alignment=round(overall, 1),
        required_skill_coverage=round(required_cov, 1),
        preferred_skill_coverage=round(preferred_cov, 1),
        category_scores=category_scores,
        methodology=SCORE_METHODOLOGY,
        disclaimer=SCORE_DISCLAIMER,
    )


def match_requirements(
    requirements: StructuredRequirements,
    resume_text: str,
    profile: ResumeProfile,
) -> Tuple[List[RequirementFinding], ScoringBreakdown]:
    findings: List[RequirementFinding] = []
    for req in requirements.items:
        status, evidence, notes = _match_skill_requirement(req.label, resume_text, profile)
        findings.append(
            RequirementFinding(
                requirement_id=req.id,
                label=req.label,
                category=req.category,
                importance=req.importance,
                status=status,
                score_contribution=STATUS_POINTS[status],
                evidence=evidence,
                notes=notes,
            ),
        )
    scoring = _score_requirements(findings)
    return findings, scoring


def run_deterministic_analysis(
    resume_text: str,
    job_description: str,
) -> DeterministicAnalysisResult:
    requirements = extract_requirements(job_description)
    profile = analyze_resume(resume_text)
    findings, scoring = match_requirements(requirements, resume_text, profile)
    return DeterministicAnalysisResult(
        requirements=requirements,
        resume_profile=profile,
        findings=findings,
        scoring=scoring,
    )
