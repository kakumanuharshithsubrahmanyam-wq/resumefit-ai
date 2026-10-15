from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analysis import AnalysisData
from app.services.matching_engine import run_deterministic_analysis
from app.services.recommendation_service import build_recommendations
from app.config import get_settings

client = TestClient(app)

RESUME = """
Skills: Python, FastAPI, SQL, Docker
Experience
- Built REST APIs with FastAPI and Python for analytics platform
Education
Bachelor of Science in Computer Science
"""

JOB = """
Requirements
- Python and FastAPI
- Docker
- Kubernetes
"""


def test_export_pdf_from_payload() -> None:
    settings = get_settings()
    analysis = run_deterministic_analysis(RESUME, JOB)
    recommendations = build_recommendations(
        settings=settings,
        analysis=analysis,
        job_title="Backend Engineer",
        company_name="Acme",
        job_description=JOB,
        resume_text=RESUME,
        request_ai=False,
        ai_consent=False,
    )
    payload = AnalysisData(
        job_title="Backend Engineer",
        company_name="Acme",
        analysis=analysis,
        recommendations=recommendations,
    )
    response = client.post("/api/v1/analysis/export/pdf", json=payload.model_dump(mode="json"))
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
