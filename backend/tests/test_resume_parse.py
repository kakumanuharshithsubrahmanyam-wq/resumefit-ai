from io import BytesIO

import fitz
from docx import Document
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

client = TestClient(app)

JOB_FORM = {
    "job_title": "Backend Engineer",
    "company_name": "Acme Corp",
    "job_description": "We need Python, FastAPI, and SQL experience for platform work.",
}


def _post_parse(filename: str, content: bytes, content_type: str):
    return client.post(
        "/api/v1/resumes/parse",
        data=JOB_FORM,
        files={"file": (filename, BytesIO(content), content_type)},
    )


def test_parse_valid_pdf(sample_pdf_bytes: bytes) -> None:
    response = _post_parse("resume.pdf", sample_pdf_bytes, "application/pdf")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["format"] == "pdf"
    assert body["data"]["word_count"] > 0
    assert "FastAPI" in body["data"]["text"]
    assert body["meta"]["job_title"] == JOB_FORM["job_title"]


def test_parse_valid_docx(sample_docx_bytes: bytes) -> None:
    response = _post_parse(
        "resume.docx",
        sample_docx_bytes,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["format"] == "docx"
    assert "Jane Developer" in body["data"]["text"]


def test_rejects_unsupported_file_type() -> None:
    response = _post_parse("notes.txt", b"plain text resume content", "text/plain")
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_file_type"


def test_rejects_invalid_pdf_content() -> None:
    response = _post_parse("resume.pdf", b"not-a-pdf", "application/pdf")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_file_content"


def test_rejects_empty_file() -> None:
    response = _post_parse("resume.pdf", b"", "application/pdf")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "empty_file"


def test_rejects_file_over_size_limit(sample_pdf_bytes: bytes, monkeypatch) -> None:
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "32")
    get_settings.cache_clear()
    response = _post_parse("resume.pdf", sample_pdf_bytes, "application/pdf")
    get_settings.cache_clear()
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"


def test_scanned_pdf_returns_helpful_error(scanned_pdf_bytes: bytes) -> None:
    response = _post_parse("scan.pdf", scanned_pdf_bytes, "application/pdf")
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "scanned_pdf"
    assert "OCR" in body["error"]["message"]


def test_encrypted_pdf_is_rejected(sample_pdf_bytes: bytes) -> None:
    document = fitz.open(stream=sample_pdf_bytes, filetype="pdf")
    encrypted = document.tobytes(
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="owner-secret",
        user_pw="user-secret",
    )
    document.close()

    response = _post_parse("locked.pdf", encrypted, "application/pdf")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "encrypted_document"


def test_corrupted_docx_returns_parse_error() -> None:
    response = _post_parse(
        "broken.docx",
        b"PK\x03\x04corrupted",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "parse_error"
