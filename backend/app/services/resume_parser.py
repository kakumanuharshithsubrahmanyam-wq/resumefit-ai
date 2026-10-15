import re
from io import BytesIO
from typing import List, Literal, Optional, Tuple

import fitz
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.text.paragraph import Paragraph
from fastapi import status

from app.exceptions.api import APIRequestError

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
PDF_MIME_TYPES = {"application/pdf", "application/x-pdf"}
DOCX_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
}

MIN_EXTRACTABLE_CHARS = 40


def _normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def detect_format(filename: str, content_type: Optional[str]) -> Literal["pdf", "docx"]:
    lower_name = filename.lower()
    if lower_name.endswith(".pdf"):
        return "pdf"
    if lower_name.endswith(".docx"):
        return "docx"

    if content_type in PDF_MIME_TYPES:
        return "pdf"
    if content_type in DOCX_MIME_TYPES and lower_name.endswith(".docx"):
        return "docx"

    raise APIRequestError(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        code="unsupported_file_type",
        message="Only PDF and DOCX resume files are supported.",
        details={"allowed_extensions": sorted(ALLOWED_EXTENSIONS)},
    )


def validate_upload_size(size_bytes: int, max_bytes: int) -> None:
    if size_bytes <= 0:
        raise APIRequestError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="empty_file",
            message="The uploaded file is empty.",
        )
    if size_bytes > max_bytes:
        raise APIRequestError(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code="file_too_large",
            message="The uploaded file exceeds the maximum allowed size.",
            details={"max_bytes": max_bytes, "size_bytes": size_bytes},
        )


def _validate_magic_bytes(data: bytes, fmt: Literal["pdf", "docx"]) -> None:
    if fmt == "pdf" and not data.startswith(b"%PDF"):
        raise APIRequestError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="invalid_file_content",
            message="The file does not appear to be a valid PDF document.",
        )
    if fmt == "docx" and not data.startswith(b"PK"):
        raise APIRequestError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="invalid_file_content",
            message="The file does not appear to be a valid DOCX document.",
        )


def _paragraph_text(paragraph: Paragraph) -> str:
    parts = [run.text for run in paragraph.runs if run.text]
    return "".join(parts).strip()


def _is_heading(paragraph: Paragraph) -> bool:
    style = paragraph.style
    if style is None:
        return False
    if style.type == WD_STYLE_TYPE.PARAGRAPH and style.name:
        name = style.name.lower()
        if name.startswith("heading"):
            return True
        if name in {"title", "subtitle"}:
            return True
    return False


def _is_list_item(paragraph: Paragraph) -> bool:
    style = paragraph.style
    if style and style.name:
        name = style.name.lower()
        if "list" in name or "bullet" in name:
            return True
    p_pr = paragraph._p.pPr  # noqa: SLF001 — paragraph properties for list detection
    if p_pr is not None and p_pr.numPr is not None:
        return True
    return False


def parse_docx_bytes(data: bytes) -> Tuple[str, Optional[int]]:
    try:
        document = Document(BytesIO(data))
    except Exception as exc:  # noqa: BLE001 — surface as client-facing parse error
        raise APIRequestError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="parse_error",
            message="Unable to read the DOCX file. It may be corrupted or unsupported.",
        ) from exc

    lines: List[str] = []
    for paragraph in document.paragraphs:
        text = _paragraph_text(paragraph)
        if not text:
            continue
        if _is_heading(paragraph):
            lines.append(f"\n{text}\n")
        elif _is_list_item(paragraph):
            lines.append(f"• {text}")
        else:
            lines.append(text)

    normalized = _normalize_whitespace("\n".join(lines))
    if len(normalized) < MIN_EXTRACTABLE_CHARS:
        raise APIRequestError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="no_extractable_text",
            message="No readable resume text was found in this document.",
        )
    return normalized, None


def parse_pdf_bytes(data: bytes) -> Tuple[str, Optional[int]]:
    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:  # noqa: BLE001
        raise APIRequestError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="parse_error",
            message="Unable to read the PDF file. It may be corrupted or malformed.",
        ) from exc

    try:
        if document.needs_pass or document.is_encrypted:
            raise APIRequestError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="encrypted_document",
                message="Password-protected PDFs are not supported.",
            )

        page_count = document.page_count
        chunks: List[str] = []
        for page in document:
            blocks = page.get_text("blocks")
            page_lines: List[str] = []
            for block in blocks:
                if len(block) < 5:
                    continue
                text = str(block[4]).strip()
                if text:
                    page_lines.append(text)
            if page_lines:
                chunks.append("\n".join(page_lines))

        normalized = _normalize_whitespace("\n\n".join(chunks))
        if len(normalized) < MIN_EXTRACTABLE_CHARS:
            raise APIRequestError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="scanned_pdf",
                message=(
                    "This PDF appears to be scanned or image-based. "
                    "OCR is not supported yet—please upload a text-based PDF or DOCX."
                ),
                details={"page_count": page_count},
            )
        return normalized, page_count
    finally:
        document.close()


def parse_resume_bytes(
    data: bytes,
    *,
    filename: str,
    content_type: Optional[str],
    max_bytes: int,
) -> dict:
    validate_upload_size(len(data), max_bytes)
    fmt = detect_format(filename, content_type)
    _validate_magic_bytes(data, fmt)

    if fmt == "pdf":
        text, page_count = parse_pdf_bytes(data)
    else:
        text, page_count = parse_docx_bytes(data)

    return {
        "filename": filename,
        "format": fmt,
        "size_bytes": len(data),
        "page_count": page_count,
        "character_count": len(text),
        "word_count": _count_words(text),
        "text": text,
    }
