from app.schemas.analysis import MatchStatus, RequirementCategory, RequirementImportance
from app.services.matching_engine import match_requirements, run_deterministic_analysis
from app.services.requirement_extractor import extract_requirements
from app.services.resume_analyzer import analyze_resume
from app.schemas.analysis import ExtractedRequirement, RequirementCategory, StructuredRequirements


JOB_DESCRIPTION = """
Requirements
- 5+ years of Python experience
- Strong FastAPI and PostgreSQL skills
- Experience with Docker and Kubernetes
Preferred
- React and TypeScript exposure
Responsibilities
- Design REST APIs and mentor junior engineers
Education
- Bachelor's degree in Computer Science or related field
"""


RESUME_TEXT = """
Jane Doe
Skills
Python, FastAPI, PostgreSQL, Docker, Git

Experience
- Built REST APIs with FastAPI and Python serving 2M requests/day
- Deployed services with Docker on AWS
- Mentored two junior engineers on code reviews and testing
Education
Bachelor of Science in Computer Science, State University
"""


def test_extracts_structured_requirements_with_sources() -> None:
    requirements = extract_requirements(JOB_DESCRIPTION)
    labels = {item.label.lower() for item in requirements.items}
    assert "python" in labels
    assert "fastapi" in labels
    assert any(item.importance == RequirementImportance.PREFERRED for item in requirements.items)


def test_alias_matching_distinguishes_javascript_and_java() -> None:
    resume = "Skills: JavaScript, React, Node.js. Built frontend dashboards."
    requirements = StructuredRequirements(
        items=[
            ExtractedRequirement(
                id="1",
                label="java",
                category=RequirementCategory.REQUIRED_TECHNICAL,
                importance=RequirementImportance.REQUIRED,
                source_text="Java required",
            ),
            ExtractedRequirement(
                id="2",
                label="javascript",
                category=RequirementCategory.REQUIRED_TECHNICAL,
                importance=RequirementImportance.REQUIRED,
                source_text="JavaScript required",
            ),
        ],
    )
    profile = analyze_resume(resume)
    findings, _ = match_requirements(requirements, resume, profile)
    by_label = {finding.label: finding.status for finding in findings}
    assert by_label["javascript"] == MatchStatus.MATCHED
    assert by_label["java"] == MatchStatus.MISSING


def test_partial_and_missing_findings() -> None:
    result = run_deterministic_analysis(RESUME_TEXT, JOB_DESCRIPTION)
    statuses = {finding.label.lower(): finding.status for finding in result.findings}
    assert statuses.get("python") == MatchStatus.MATCHED
    assert statuses.get("kubernetes") == MatchStatus.MISSING
    assert result.scoring.overall_alignment > 0
    assert "not a prediction" in result.scoring.disclaimer.lower()


def test_scoring_required_and_preferred_coverage() -> None:
    result = run_deterministic_analysis(RESUME_TEXT, JOB_DESCRIPTION)
    assert 0 <= result.scoring.required_skill_coverage <= 100
    assert 0 <= result.scoring.preferred_skill_coverage <= 100
    assert len(result.scoring.category_scores) == len(RequirementCategory)
