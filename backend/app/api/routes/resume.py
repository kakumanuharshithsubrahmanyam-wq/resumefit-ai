from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, status

from app.config import get_settings
from app.exceptions.api import APIRequestError
from app.schemas.response import APIResponse
from app.schemas.resume import ResumeParseData, ResumeParseMeta
from app.services.resume_parser import parse_resume_bytes

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/parse", response_model=APIResponse[ResumeParseData])
async def parse_resume_upload(
    file: UploadFile = File(...),
    job_title: str = Form(..., min_length=1, max_length=200),
    job_description: str = Form(..., min_length=1, max_length=20000),
    company_name: Optional[str] = Form(default=None, max_length=200),
) -> APIResponse[ResumeParseData]:
    if file.filename is None or not file.filename.strip():
        raise APIRequestError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="missing_filename",
            message="The upload must include a filename.",
        )

    settings = get_settings()
    raw = await file.read(settings.max_upload_bytes + 1)
    if len(raw) > settings.max_upload_bytes:
        raise APIRequestError(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code="file_too_large",
            message="The uploaded file exceeds the maximum allowed size.",
            details={
                "max_bytes": settings.max_upload_bytes,
                "size_bytes": len(raw),
            },
        )

    parsed = parse_resume_bytes(
        raw,
        filename=file.filename,
        content_type=file.content_type,
        max_bytes=settings.max_upload_bytes,
    )

    data = ResumeParseData(**parsed)
    meta = ResumeParseMeta(
        job_title=job_title.strip(),
        company_name=company_name.strip() if company_name else None,
        job_description_length=len(job_description.strip()),
    )
    return APIResponse(data=data, meta=meta.model_dump())
