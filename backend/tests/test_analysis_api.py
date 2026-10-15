from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

client = TestClient(app)

RESUME = """
Skills: Python, FastAPI, SQL, Docker
Experience
- Built REST APIs with FastAPI and Python for analytics platform
- Containerized workloads using Docker
Education
Bachelor of Science in Computer Science
"""

JOB = """
Requirements
- Python and FastAPI
- Docker
- Kubernetes
Preferred
- React
"""


def test_analysis_endpoint_success_without_ai() -> None:
    response = client.post(
        "/api/v1/analysis/run",
        json={
            "resume_text": RESUME,
            "job_title": "Backend Engineer",
            "company_name": "Acme",
            "job_description": JOB,
            "request_ai_recommendations": False,
            "ai_consent": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["analysis"]["scoring"]["overall_alignment"] >= 0
    ats = body["data"]["analysis"]["ats_compatibility"]
    assert ats["status"] == "available"
    assert ats["overall_score"] is not None
    assert body["data"]["recommendations"]["provider"] == "disabled"


def test_analysis_requires_resume_text() -> None:
    response = client.post(
        "/api/v1/analysis/run",
        json={
            "resume_text": "too short",
            "job_title": "Engineer",
            "job_description": JOB,
        },
    )
    assert response.status_code == 422


def test_ai_consent_required_when_requesting_ai() -> None:
    response = client.post(
        "/api/v1/analysis/run",
        json={
            "resume_text": RESUME,
            "job_title": "Backend Engineer",
            "job_description": JOB,
            "request_ai_recommendations": True,
            "ai_consent": False,
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "ai_consent_required"


@patch("app.services.ai.openai_provider.OpenAIRecommendationProvider.generate_recommendations")
def test_ai_failure_falls_back_deterministically(mock_generate) -> None:
    mock_generate.side_effect = RuntimeError("rate limit")

    get_settings.cache_clear()
    with patch.dict(
        "os.environ",
        {
            "OPENAI_API_KEY": "test-key",
            "AI_ENABLED": "true",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        response = client.post(
            "/api/v1/analysis/run",
            json={
                "resume_text": RESUME,
                "job_title": "Backend Engineer",
                "job_description": JOB,
                "request_ai_recommendations": True,
                "ai_consent": True,
            },
        )
    get_settings.cache_clear()

    assert response.status_code == 200
    rec = response.json()["data"]["recommendations"]
    assert rec["provider"] == "deterministic_fallback"
    assert rec["gap_explanations"]
