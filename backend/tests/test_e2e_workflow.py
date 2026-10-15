"""End-to-end workflow: parse → analyze → PDF → history lifecycle."""

import uuid

import fitz
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

JOB = """
Requirements
- Python and FastAPI experience
- Docker and PostgreSQL
- REST API design
Preferred
- React
Responsibilities
- Build backend services and mentor engineers
Education
- Bachelor's degree in Computer Science
"""


def _make_pdf_bytes() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        "Skills\nPython, FastAPI, PostgreSQL, Docker, Git\n\n"
        "Experience\n- Built REST APIs with FastAPI serving 2M requests/day\n"
        "- Deployed services with Docker\n\n"
        "Education\nBachelor of Science in Computer Science",
        fontsize=11,
    )
    payload = document.tobytes()
    document.close()
    return payload


def test_complete_workflow_parse_analyze_pdf_history() -> None:
    session = str(uuid.uuid4())
    headers = {"X-Analysis-Session-Id": session}
    pdf_bytes = _make_pdf_bytes()

    parse_response = client.post(
        "/api/v1/resumes/parse",
        headers=headers,
        data={
            "job_title": "Backend Engineer",
            "company_name": "Acme",
            "job_description": JOB,
        },
        files={"file": ("candidate.pdf", pdf_bytes, "application/pdf")},
    )
    assert parse_response.status_code == 200
    parsed = parse_response.json()["data"]
    assert parsed["word_count"] > 0
    resume_text = parsed["text"]

    analyze_response = client.post(
        "/api/v1/analysis/run",
        headers=headers,
        json={
            "resume_text": resume_text,
            "job_title": "Backend Engineer",
            "company_name": "Acme",
            "job_description": JOB,
            "request_ai_recommendations": False,
            "ai_consent": False,
            "save_to_history": True,
            "resume_filename": "candidate.pdf",
        },
    )
    assert analyze_response.status_code == 200
    analysis_body = analyze_response.json()["data"]
    scoring = analysis_body["analysis"]["scoring"]
    assert scoring["overall_alignment"] >= 0
    findings = analysis_body["analysis"]["findings"]
    assert any(item["status"] == "matched" for item in findings)
    assert any(item["status"] == "missing" for item in findings)
    record_id = analysis_body["record_id"]
    assert record_id

    pdf_response = client.post(
        "/api/v1/analysis/export/pdf",
        headers=headers,
        json=analysis_body,
    )
    assert pdf_response.status_code == 200
    assert pdf_response.content.startswith(b"%PDF")

    saved_pdf = client.get(
        f"/api/v1/analysis/{record_id}/export/pdf",
        headers=headers,
    )
    assert saved_pdf.status_code == 200
    assert saved_pdf.content.startswith(b"%PDF")

    history_list = client.get("/api/v1/history", headers=headers)
    assert history_list.status_code == 200
    assert len(history_list.json()["data"]) == 1

    reopened = client.get(f"/api/v1/history/{record_id}", headers=headers)
    assert reopened.status_code == 200
    assert reopened.json()["data"]["data"]["job_title"] == "Backend Engineer"

    deleted = client.delete(f"/api/v1/history/{record_id}", headers=headers)
    assert deleted.status_code == 200
    missing = client.get(f"/api/v1/history/{record_id}", headers=headers)
    assert missing.status_code == 404


def test_stored_history_does_not_include_full_resume_text() -> None:
    session = str(uuid.uuid4())
    headers = {"X-Analysis-Session-Id": session}
    resume_text = (
        "Skills: Python, FastAPI, Docker\nExperience\n- Built APIs with Python\n"
        "Education\nBS Computer Science\n"
        + ("Additional experience details. " * 80)
    )
    run = client.post(
        "/api/v1/analysis/run",
        headers=headers,
        json={
            "resume_text": resume_text,
            "job_title": "Engineer",
            "job_description": JOB,
            "save_to_history": True,
        },
    )
    record_id = run.json()["data"]["record_id"]
    stored = client.get(f"/api/v1/history/{record_id}", headers=headers).json()["data"]
    serialized = str(stored)
    assert "resume_text" not in serialized
    # Full resume filler text must not be persisted verbatim in saved history.
    assert serialized.count("Additional experience details.") == 0
