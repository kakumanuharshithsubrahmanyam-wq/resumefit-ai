import uuid

from fastapi.testclient import TestClient

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


def _session_headers() -> dict:
    return {"X-Analysis-Session-Id": str(uuid.uuid4())}


def test_save_list_get_and_delete_history() -> None:
    headers = _session_headers()

    run_response = client.post(
        "/api/v1/analysis/run",
        headers=headers,
        json={
            "resume_text": RESUME,
            "job_title": "Backend Engineer",
            "company_name": "Acme",
            "job_description": JOB,
            "save_to_history": True,
            "resume_filename": "resume.pdf",
        },
    )
    assert run_response.status_code == 200
    record_id = run_response.json()["data"]["record_id"]
    assert record_id

    list_response = client.get("/api/v1/history", headers=headers)
    assert list_response.status_code == 200
    items = list_response.json()["data"]
    assert len(items) == 1
    assert items[0]["id"] == record_id

    get_response = client.get(f"/api/v1/history/{record_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["data"]["data"]["job_title"] == "Backend Engineer"

    delete_response = client.delete(f"/api/v1/history/{record_id}", headers=headers)
    assert delete_response.status_code == 200

    missing = client.get(f"/api/v1/history/{record_id}", headers=headers)
    assert missing.status_code == 404


def test_history_isolated_by_session() -> None:
    headers_a = _session_headers()
    headers_b = _session_headers()

    created = client.post(
        "/api/v1/analysis/run",
        headers=headers_a,
        json={
            "resume_text": RESUME,
            "job_title": "Engineer",
            "job_description": JOB,
            "save_to_history": True,
        },
    )
    record_id = created.json()["data"]["record_id"]

    forbidden = client.get(f"/api/v1/history/{record_id}", headers=headers_b)
    assert forbidden.status_code == 404


def test_clear_history() -> None:
    headers = _session_headers()
    client.post(
        "/api/v1/analysis/run",
        headers=headers,
        json={
            "resume_text": RESUME,
            "job_title": "Engineer",
            "job_description": JOB,
            "save_to_history": True,
        },
    )
    cleared = client.delete("/api/v1/history", headers=headers)
    assert cleared.status_code == 200
    assert cleared.json()["data"]["deleted_count"] >= 1
