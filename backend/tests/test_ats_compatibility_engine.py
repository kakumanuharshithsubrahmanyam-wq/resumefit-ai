"""Tests for deterministic ATS compatibility scoring."""

from __future__ import annotations

import fitz

from app.schemas.analysis import MatchStatus, ResumeParseContext
from app.services.ats_compatibility_engine import (
    COMPONENT_WEIGHTS,
    _aggregate_components,
    _ComponentResult,
    compute_ats_compatibility,
)
from app.services.matching_engine import run_deterministic_analysis

JOB = """
Requirements
- Python and FastAPI experience
- Docker and PostgreSQL
Preferred
- React
"""


def test_high_keyword_coverage_scores_higher_than_low() -> None:
    strong = run_deterministic_analysis(
        resume_text=(
            "Skills: Python, FastAPI, Docker, PostgreSQL\n\n"
            "Experience\n• Built REST APIs with FastAPI and Python\n"
            "• Deployed with Docker and PostgreSQL\n\n"
            "Education\nBS Computer Science\n"
            "Contact: jane@example.com | (555) 123-4567"
        ),
        job_description=JOB,
    )
    weak = run_deterministic_analysis(
        resume_text=(
            "General office assistant with Microsoft Word experience.\n"
            "Email: weak@example.com"
        ),
        job_description=JOB,
    )
    assert strong.ats_compatibility is not None
    assert weak.ats_compatibility is not None
    assert strong.ats_compatibility.overall_score is not None
    assert weak.ats_compatibility.overall_score is not None
    assert strong.ats_compatibility.overall_score > weak.ats_compatibility.overall_score


def test_aliases_inherit_coverage_from_analysis() -> None:
    analysis = run_deterministic_analysis(
        resume_text=(
            "Skills\nJavaScript, Node.js\n\nExperience\n• Built web APIs with JS\n"
            "Email: dev@example.com"
        ),
        job_description="Requirements\n- JavaScript experience\n",
    )
    js_finding = next(f for f in analysis.findings if "javascript" in f.label.lower())
    assert js_finding.status == MatchStatus.MATCHED
    assert analysis.ats_compatibility and analysis.ats_compatibility.overall_score is not None


def test_keyword_repetition_penalizes_stuffing() -> None:
    stuffed = "Python " * 80 + "\nEmail: spam@example.com\nExperience\n• one line"
    analysis_stuffed = run_deterministic_analysis(
        resume_text=stuffed,
        job_description=JOB,
    )
    natural = run_deterministic_analysis(
        resume_text=(
            "Skills\nPython, FastAPI\n\nExperience\n• Built APIs with Python and FastAPI\n"
            "Email: good@example.com"
        ),
        job_description=JOB,
    )
    assert analysis_stuffed.ats_compatibility
    assert natural.ats_compatibility
    kw_stuffed = next(
        c for c in analysis_stuffed.ats_compatibility.components if c.id == "job_relevant_keyword_coverage"
    )
    kw_natural = next(
        c for c in natural.ats_compatibility.components if c.id == "job_relevant_keyword_coverage"
    )
    assert kw_stuffed.score is not None and kw_natural.score is not None
    assert kw_natural.score >= kw_stuffed.score
    assert any("stuffing" in w.lower() for w in analysis_stuffed.ats_compatibility.parsing_warnings)


def test_clear_headings_score_better_than_unstructured() -> None:
    structured = (
        "EXPERIENCE\n• Built APIs with Python\n\n"
        "SKILLS\nPython, FastAPI\n\n"
        "EDUCATION\nBS CS\nEmail: a@example.com"
    )
    unstructured = (
        "Built APIs with Python FastAPI Docker PostgreSQL React "
        "without headings or bullets. Email: a@example.com"
    )
    a = run_deterministic_analysis(resume_text=structured, job_description=JOB)
    b = run_deterministic_analysis(resume_text=unstructured, job_description=JOB)
    s_a = next(c for c in a.ats_compatibility.components if c.id == "section_clarity_structure")
    s_b = next(c for c in b.ats_compatibility.components if c.id == "section_clarity_structure")
    assert s_a.score is not None and s_b.score is not None
    assert s_a.score > s_b.score


def test_low_words_per_page_lowers_parsing_component() -> None:
    sparse_ctx = ResumeParseContext(format="pdf", word_count=30, character_count=200, page_count=3)
    dense_ctx = ResumeParseContext(format="pdf", word_count=600, character_count=4000, page_count=2)
    text = (
        "EXPERIENCE\n• Built APIs with Python and FastAPI\n"
        "Email: user@example.com\nEDUCATION\nBS Computer Science"
    )
    sparse = run_deterministic_analysis(text, JOB, parse_context=sparse_ctx)
    dense = run_deterministic_analysis(text, JOB, parse_context=dense_ctx)
    p_sparse = next(c for c in sparse.ats_compatibility.components if c.id == "machine_readable_parsing")
    p_dense = next(c for c in dense.ats_compatibility.components if c.id == "machine_readable_parsing")
    assert p_sparse.score is not None and p_dense.score is not None
    assert p_dense.score > p_sparse.score


def test_missing_phone_does_not_zero_contact_score() -> None:
    text = "Skills\nPython\nExperience\n• Built APIs\nEmail: only@example.com\n"
    analysis = run_deterministic_analysis(text, JOB)
    contact = next(c for c in analysis.ats_compatibility.components if c.id == "contact_essential_details")
    assert contact.score is not None
    assert contact.score >= 50.0


def test_weight_renormalization_when_keyword_unavailable() -> None:
    components = [
        _ComponentResult("job_relevant_keyword_coverage", None, False, "n/a"),
        _ComponentResult("section_clarity_structure", 80.0, True, "ok"),
        _ComponentResult("machine_readable_parsing", 70.0, True, "ok"),
        _ComponentResult("contact_essential_details", 60.0, True, "ok"),
        _ComponentResult("readability_formatting", 75.0, True, "ok"),
    ]
    overall, breakdown = _aggregate_components(components)
    assert overall is not None
    unavailable = next(c for c in breakdown if c.id == "job_relevant_keyword_coverage")
    assert unavailable.effective_weight == 0.0
    active = [c for c in breakdown if c.available]
    assert abs(sum(c.effective_weight for c in active) - 1.0) < 0.01


def test_insufficient_data_for_tiny_resume() -> None:
    analysis = run_deterministic_analysis("short text that is still forty chars long!!", JOB)
    assert analysis.ats_compatibility.status == "available"


def test_insufficient_data_status_when_below_min() -> None:
    from app.schemas.analysis import DeterministicAnalysisResult, StructuredRequirements
    from app.services.resume_analyzer import analyze_resume

    profile = analyze_resume("x" * 39)
    base = DeterministicAnalysisResult(
        requirements=StructuredRequirements(items=[]),
        resume_profile=profile,
        findings=[],
        scoring=run_deterministic_analysis("x" * 80, JOB).scoring,
    )
    result = compute_ats_compatibility(resume_text="x" * 39, analysis=base)
    assert result.status == "insufficient_data"
    assert result.overall_score is None


def test_scores_within_bounds_and_deterministic() -> None:
    resume = (
        "EXPERIENCE\n• Python FastAPI Docker PostgreSQL\n"
        "Email: test@example.com | 555-010-0200\nEDUCATION\nBS CS"
    )
    first = run_deterministic_analysis(resume, JOB)
    second = run_deterministic_analysis(resume, JOB)
    assert first.ats_compatibility.overall_score == second.ats_compatibility.overall_score
    assert 0 <= first.ats_compatibility.overall_score <= 100


def test_missing_keywords_distinguish_not_found() -> None:
    analysis = run_deterministic_analysis(
        "Skills\nPython\nEmail: a@example.com\nExperience\n• Built APIs\n",
        JOB,
    )
    missing = analysis.ats_compatibility.missing_keywords
    assert any("not found in resume text" in item for item in missing)


def test_analysis_api_includes_ats_field() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/analysis/run",
        json={
            "resume_text": "Skills\nPython, FastAPI, Docker\nEmail: dev@example.com\n"
            "Experience\n• Built APIs with Python\n",
            "job_title": "Engineer",
            "job_description": JOB,
            "request_ai_recommendations": False,
            "ai_consent": False,
        },
    )
    assert response.status_code == 200
    ats = response.json()["data"]["analysis"]["ats_compatibility"]
    assert ats["status"] == "available"
    assert ats["overall_score"] is not None
    assert len(ats["components"]) == len(COMPONENT_WEIGHTS)


def test_history_summary_tolerates_missing_ats() -> None:
    from app.services.history_service import _summary_from_json

    legacy = '{"analysis": {"scoring": {"overall_alignment": 72.5, "required_skill_coverage": 80.0}}}'
    summary = _summary_from_json(legacy)
    assert summary["overall_alignment"] == 72.5
    assert summary["ats_compatibility_score"] is None
