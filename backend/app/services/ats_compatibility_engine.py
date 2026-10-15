"""Deterministic Estimated ATS Compatibility scoring (0–100)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from app.data.skill_lexicon import canonicalize_skill, expand_skill_variants
from app.schemas.analysis import (
    ATSCompatibilityResult,
    ATSComponentScore,
    ATSRecommendedFix,
    DeterministicAnalysisResult,
    MatchStatus,
    RequirementFinding,
    RequirementImportance,
    ResumeParseContext,
)
from app.services.text_utils import split_sentences

COMPONENT_WEIGHTS: Dict[str, float] = {
    "job_relevant_keyword_coverage": 0.35,
    "section_clarity_structure": 0.20,
    "machine_readable_parsing": 0.20,
    "contact_essential_details": 0.10,
    "readability_formatting": 0.15,
}

COMPONENT_LABELS: Dict[str, str] = {
    "job_relevant_keyword_coverage": "Job-relevant keyword coverage",
    "section_clarity_structure": "Resume section clarity & structure",
    "machine_readable_parsing": "Machine-readable text & parsing quality",
    "contact_essential_details": "Contact & essential details",
    "readability_formatting": "Readability & formatting signals",
}

ATS_METHODOLOGY = (
    "Weighted estimate from extracted text only (not visual layout): "
    "keyword coverage 35%, section structure 20%, parsing quality 20%, "
    "contact details 10%, readability 15%. "
    "Unavailable components are excluded and remaining weights are renormalized."
)

ATS_DISCLAIMER = (
    "Estimated ATS Compatibility reflects how well this resume's extracted text "
    "communicates job-relevant qualifications and parse-friendly structure. "
    "It is not an official ATS score—employers use different parsers and ranking rules."
)

SECTION_HEADING_PATTERNS = (
    r"^(?:experience|work experience|professional experience|employment)\b",
    r"^(?:education|academic background)\b",
    r"^(?:skills|technical skills|core competencies|technologies)\b",
    r"^(?:summary|professional summary|profile|objective)\b",
    r"^(?:projects|certifications|licenses)\b",
)

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)",
)
LINKEDIN_RE = re.compile(r"\blinkedin\.com/\S+", re.IGNORECASE)
BULLET_LINE_RE = re.compile(r"^\s*(?:[•\-\*●▪]|\d+\.)\s+\S")
HEADING_LINE_RE = re.compile(
    r"^(?:[A-Z][A-Za-z0-9 &/\-]{2,40}):?\s*$|^(?:EXPERIENCE|EDUCATION|SKILLS|SUMMARY|PROJECTS|CERTIFICATIONS)\s*$",
    re.MULTILINE,
)


@dataclass
class _ComponentResult:
    key: str
    score: Optional[float]
    available: bool
    explanation: str


def _importance_weight(importance: RequirementImportance) -> float:
    if importance == RequirementImportance.REQUIRED:
        return 1.0
    if importance == RequirementImportance.PREFERRED:
        return 0.65
    return 0.45


def _status_points(status: MatchStatus) -> float:
    return {
        MatchStatus.MATCHED: 1.0,
        MatchStatus.PARTIAL: 0.55,
        MatchStatus.UNCERTAIN: 0.25,
        MatchStatus.MISSING: 0.0,
    }[status]


def _keyword_stuffing_penalty(resume_text: str, findings: Sequence[RequirementFinding]) -> Tuple[float, List[str]]:
    """Reduce keyword component when the same terms repeat without distinct evidence."""
    warnings: List[str] = []
    penalty = 0.0
    lower = resume_text.lower()
    for finding in findings:
        if finding.status not in {MatchStatus.MATCHED, MatchStatus.PARTIAL}:
            continue
        canonical = canonicalize_skill(finding.label)
        variants = expand_skill_variants(canonical) if canonical else [finding.label.lower()]
        total_hits = sum(lower.count(v) for v in variants if len(v) > 2)
        if total_hits <= 6:
            continue
        sentences = split_sentences(resume_text)
        sentence_hits = sum(
            1 for sentence in sentences if any(v in sentence.lower() for v in variants if len(v) > 2)
        )
        if total_hits > 8 and sentence_hits <= 2:
            penalty += 8.0
            warnings.append(
                f'"{finding.label}" appears many times in close repetition—ATS parsers may treat this as keyword stuffing.',
            )
    return min(penalty, 20.0), warnings


def _score_keyword_coverage(
    findings: Sequence[RequirementFinding],
    resume_text: str,
) -> _ComponentResult:
    if not findings:
        return _ComponentResult(
            "job_relevant_keyword_coverage",
            None,
            False,
            "No job requirements were extracted to compare against the resume.",
        )
    weighted_sum = 0.0
    weight_total = 0.0
    for finding in findings:
        w = _importance_weight(finding.importance)
        weighted_sum += w * _status_points(finding.status)
        weight_total += w
    base = (weighted_sum / weight_total * 100.0) if weight_total else 0.0
    penalty, _ = _keyword_stuffing_penalty(resume_text, findings)
    score = max(0.0, min(100.0, base - penalty))
    return _ComponentResult(
        "job_relevant_keyword_coverage",
        round(score, 1),
        True,
        "Coverage of extracted job requirements (required terms weighted higher), with alias-aware matching from analysis.",
    )


def _score_section_structure(resume_text: str) -> _ComponentResult:
    if len(resume_text.strip()) < 40:
        return _ComponentResult(
            "section_clarity_structure",
            None,
            False,
            "Not enough text to assess section structure.",
        )
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    if not lines:
        return _ComponentResult("section_clarity_structure", None, False, "No readable lines found.")

    heading_hits = 0
    for line in lines:
        normalized = line.lower().rstrip(":")
        if any(re.match(pattern, normalized) for pattern in SECTION_HEADING_PATTERNS):
            heading_hits += 1
        elif HEADING_LINE_RE.match(line):
            heading_hits += 1

    bullet_lines = sum(1 for line in lines if BULLET_LINE_RE.match(line))
    bullet_ratio = bullet_lines / len(lines)

    heading_score = min(100.0, heading_hits / 3.0 * 100.0)
    bullet_score = min(100.0, bullet_ratio / 0.35 * 100.0) if bullet_ratio else 20.0
    score = round(0.55 * heading_score + 0.45 * bullet_score, 1)
    return _ComponentResult(
        "section_clarity_structure",
        score,
        True,
        "Recognizable section headings and bullet-like entries in extracted text (layout/fonts not inspected).",
    )


def _score_parsing_quality(
    resume_text: str,
    parse_context: Optional[ResumeParseContext],
) -> _ComponentResult:
    text = resume_text.strip()
    if len(text) < 40:
        return _ComponentResult(
            "machine_readable_parsing",
            None,
            False,
            "Insufficient extracted text to judge parsing quality.",
        )

    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)
    if parse_context and parse_context.word_count is not None:
        word_count = parse_context.word_count

    char_count = len(text)
    if parse_context and parse_context.character_count is not None:
        char_count = parse_context.character_count

    alnum = sum(1 for c in text if c.isalnum() or c.isspace())
    alnum_ratio = alnum / max(len(text), 1)

    density_score = 100.0
    page_count = parse_context.page_count if parse_context else None
    if page_count and page_count > 0:
        wpp = word_count / page_count
        if wpp < 25:
            density_score = max(25.0, wpp / 25.0 * 100.0)
        elif wpp > 800:
            density_score = 70.0

    avg_word_len = char_count / max(word_count, 1)
    word_len_score = 100.0
    if avg_word_len > 12:
        word_len_score = 60.0
    elif avg_word_len < 3:
        word_len_score = 50.0

    alnum_score = min(100.0, alnum_ratio / 0.85 * 100.0)
    score = round(0.45 * density_score + 0.35 * alnum_score + 0.20 * word_len_score, 1)
    return _ComponentResult(
        "machine_readable_parsing",
        score,
        True,
        "Heuristics on extracted text density and character quality; optional upload metadata improves page-density checks.",
    )


def _score_contact_essentials(resume_text: str) -> _ComponentResult:
    has_email = bool(EMAIL_RE.search(resume_text))
    has_phone = bool(PHONE_RE.search(resume_text))
    has_linkedin = bool(LINKEDIN_RE.search(resume_text))

    score = 0.0
    if has_email:
        score += 55.0
    if has_phone:
        score += 35.0
    if has_linkedin:
        score += 10.0
    score = min(100.0, score)

    return _ComponentResult(
        "contact_essential_details",
        round(score, 1),
        True,
        "Detects common contact fields in text; optional fields (photo, social links) are not required.",
    )


def _score_readability(resume_text: str) -> _ComponentResult:
    sentences = split_sentences(resume_text)
    if not sentences:
        return _ComponentResult("readability_formatting", None, False, "No sentences detected.")

    lengths = [len(s.split()) for s in sentences]
    avg_len = sum(lengths) / len(lengths)
    if avg_len <= 8:
        len_score = 70.0
    elif avg_len <= 28:
        len_score = 100.0 - abs(avg_len - 18) * 2.5
    else:
        len_score = max(35.0, 100.0 - (avg_len - 28) * 3)

    lines = [line for line in resume_text.splitlines() if line.strip()]
    long_lines = sum(1 for line in lines if len(line) > 180 and not BULLET_LINE_RE.match(line))
    long_line_penalty = min(30.0, long_lines * 6.0)

    caps_lines = sum(
        1
        for line in lines
        if len(line) > 20 and sum(1 for c in line if c.isalpha() and c.isupper()) / max(sum(1 for c in line if c.isalpha()), 1) > 0.8
    )
    caps_penalty = min(20.0, caps_lines * 5.0)

    score = max(0.0, min(100.0, len_score - long_line_penalty - caps_penalty))
    return _ComponentResult(
        "readability_formatting",
        round(score, 1),
        True,
        "Sentence length, dense paragraphs, and ALL-CAPS blocks in extracted text (not font size or margins).",
    )


def _aggregate_components(components: Sequence[_ComponentResult]) -> Tuple[Optional[float], List[ATSComponentScore]]:
    available: List[Tuple[str, float, float]] = []
    breakdown: List[ATSComponentScore] = []

    for comp in components:
        nominal = COMPONENT_WEIGHTS[comp.key]
        if comp.available and comp.score is not None:
            available.append((comp.key, nominal, comp.score))
            breakdown.append(
                ATSComponentScore(
                    id=comp.key,
                    label=COMPONENT_LABELS[comp.key],
                    nominal_weight=nominal,
                    effective_weight=nominal,
                    score=comp.score,
                    available=True,
                    explanation=comp.explanation,
                ),
            )
        else:
            breakdown.append(
                ATSComponentScore(
                    id=comp.key,
                    label=COMPONENT_LABELS[comp.key],
                    nominal_weight=nominal,
                    effective_weight=0.0,
                    score=None,
                    available=False,
                    explanation=comp.explanation,
                ),
            )

    if not available:
        return None, breakdown

    total_nominal = sum(nominal for _, nominal, _ in available)
    for item in breakdown:
        if item.available and item.score is not None:
            item.effective_weight = round(item.nominal_weight / total_nominal, 4)

    overall = sum(
        item.effective_weight * item.score
        for item in breakdown
        if item.available and item.score is not None
    )
    return round(overall, 1), breakdown


def _missing_keywords(findings: Sequence[RequirementFinding]) -> List[str]:
    missing: List[str] = []
    for finding in findings:
        if finding.status != MatchStatus.MISSING:
            continue
        if finding.importance == RequirementImportance.REQUIRED:
            missing.append(f"{finding.label} — not found in resume text")
        elif finding.importance == RequirementImportance.PREFERRED:
            missing.append(f"{finding.label} — preferred term not found in resume text")
    return missing[:12]


def _positive_signals(
    components: Sequence[_ComponentResult],
    findings: Sequence[RequirementFinding],
    resume_text: str,
) -> List[str]:
    signals: List[str] = []
    matched_required = sum(
        1
        for f in findings
        if f.importance == RequirementImportance.REQUIRED and f.status == MatchStatus.MATCHED
    )
    if matched_required:
        signals.append(f"{matched_required} required job terms appear with supporting resume text.")
    structure = next((c for c in components if c.key == "section_clarity_structure"), None)
    if structure and structure.score is not None and structure.score >= 70:
        signals.append("Section headings and bullet-style entries are easy to detect in extracted text.")
    if EMAIL_RE.search(resume_text):
        signals.append("A recognizable email address appears in the resume text.")
    parsing = next((c for c in components if c.key == "machine_readable_parsing"), None)
    if parsing and parsing.score is not None and parsing.score >= 75:
        signals.append("Extracted text looks machine-readable with healthy character density.")
    return signals[:6]


def _build_fixes(
    missing_keywords: List[str],
    structural_warnings: List[str],
    parsing_warnings: List[str],
    stuffing_warnings: List[str],
    components: Sequence[_ComponentResult],
) -> List[ATSRecommendedFix]:
    fixes: List[ATSRecommendedFix] = []
    for label in missing_keywords[:4]:
        term = label.split(" — ")[0]
        fixes.append(
            ATSRecommendedFix(
                title=f"Address job term: {term}",
                rationale=(
                    f"{label}. Add truthful evidence (projects, tools used, outcomes)—only include skills you can substantiate."
                ),
                impact="high",
            ),
        )
    for warning in structural_warnings:
        fixes.append(
            ATSRecommendedFix(
                title="Improve resume structure",
                rationale=warning,
                impact="high" if "heading" in warning.lower() else "medium",
            ),
        )
    for warning in parsing_warnings + stuffing_warnings:
        fixes.append(
            ATSRecommendedFix(
                title="Improve parse-friendly formatting",
                rationale=warning,
                impact="medium",
            ),
        )
    contact = next((c for c in components if c.key == "contact_essential_details"), None)
    if contact and contact.score is not None and contact.score < 60:
        fixes.append(
            ATSRecommendedFix(
                title="Add clear contact details",
                rationale="Include a professional email and phone number near the top in plain text.",
                impact="medium",
            ),
        )
    impact_order = {"high": 0, "medium": 1, "low": 2}
    fixes.sort(key=lambda item: impact_order.get(item.impact, 3))
    return fixes[:8]


def compute_ats_compatibility(
    *,
    resume_text: str,
    analysis: DeterministicAnalysisResult,
    parse_context: Optional[ResumeParseContext] = None,
) -> ATSCompatibilityResult:
    text = resume_text.strip()
    findings = analysis.findings

    if len(text) < 40:
        return ATSCompatibilityResult(
            status="insufficient_data",
            overall_score=None,
            label="Estimated ATS Compatibility",
            disclaimer=ATS_DISCLAIMER,
            methodology=ATS_METHODOLOGY,
            components=[],
            positive_signals=[],
            improvement_opportunities=["Provide a resume with more extractable text to estimate ATS compatibility."],
            missing_keywords=[],
            structural_warnings=[],
            parsing_warnings=[],
            recommended_fixes=[],
        )

    stuffing_penalty, stuffing_warnings = _keyword_stuffing_penalty(text, findings)
    raw_components = [
        _score_keyword_coverage(findings, text),
        _score_section_structure(text),
        _score_parsing_quality(text, parse_context),
        _score_contact_essentials(text),
        _score_readability(text),
    ]

    overall, component_models = _aggregate_components(raw_components)
    if overall is None:
        return ATSCompatibilityResult(
            status="unavailable",
            overall_score=None,
            label="Estimated ATS Compatibility",
            disclaimer=ATS_DISCLAIMER,
            methodology=ATS_METHODOLOGY,
            components=component_models,
            positive_signals=[],
            improvement_opportunities=["Unable to compute a reliable ATS compatibility estimate from available data."],
            missing_keywords=_missing_keywords(findings),
            structural_warnings=[],
            parsing_warnings=[],
            recommended_fixes=[],
        )

    structural_warnings: List[str] = []
    structure = raw_components[1]
    if structure.score is not None and structure.score < 55:
        structural_warnings.append(
            "Add clear section headings (Experience, Skills, Education) and bullet points for responsibilities.",
        )

    parsing_warnings: List[str] = []
    parsing = raw_components[2]
    if parse_context and parse_context.page_count and parse_context.word_count:
        wpp = parse_context.word_count / max(parse_context.page_count, 1)
        if wpp < 25:
            parsing_warnings.append(
                "Low words-per-page in extracted text may indicate scanning or poor text extraction.",
            )
    if parsing.score is not None and parsing.score < 50:
        parsing_warnings.append(
            "Extracted text quality is weak—verify the source file is text-based PDF/DOCX, not an image scan.",
        )

    missing_kw = _missing_keywords(findings)
    opportunities: List[str] = []
    if missing_kw:
        opportunities.append(
            "Several job-description terms are missing from the resume text—add evidence where you genuinely have the experience.",
        )
    if stuffing_penalty > 0:
        opportunities.append("Reduce repeated keyword lists; emphasize distinct achievements instead.")
    if structural_warnings:
        opportunities.extend(structural_warnings)
    if parsing_warnings:
        opportunities.extend(parsing_warnings)

    fixes = _build_fixes(missing_kw, structural_warnings, parsing_warnings, stuffing_warnings, raw_components)

    return ATSCompatibilityResult(
        status="available",
        overall_score=overall,
        label="Estimated ATS Compatibility",
        disclaimer=ATS_DISCLAIMER,
        methodology=ATS_METHODOLOGY,
        components=component_models,
        positive_signals=_positive_signals(raw_components, findings, text),
        improvement_opportunities=opportunities[:8],
        missing_keywords=missing_kw,
        structural_warnings=structural_warnings,
        parsing_warnings=parsing_warnings + stuffing_warnings,
        recommended_fixes=fixes,
    )
