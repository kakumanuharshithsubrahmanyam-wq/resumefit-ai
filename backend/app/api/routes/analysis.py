from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.exceptions.api import APIRequestError
from app.schemas.analysis import AnalysisData, AnalysisRequest
from app.schemas.response import APIResponse
from app.services.analysis_pipeline import run_analysis
from app.services.history_service import get_analysis_record
from app.services.report_pdf import generate_analysis_pdf, generate_pdf_from_analysis_data
from app.services.session_context import resolve_session_id
from fastapi import status

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/run", response_model=APIResponse[AnalysisData])
def run_resume_analysis(
    payload: AnalysisRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> APIResponse[AnalysisData]:
    settings = get_settings()
    session_id = resolve_session_id(request, response)
    try:
        result = run_analysis(
            payload,
            settings,
            db=db if payload.save_to_history else None,
            session_id=session_id if payload.save_to_history else None,
        )
    except ValueError as exc:
        raise APIRequestError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="history_unavailable",
            message=str(exc),
        ) from exc
    return APIResponse(data=result, meta={"session_id": session_id})


@router.post("/export/pdf")
def export_analysis_pdf(payload: AnalysisData) -> StreamingResponse:
    pdf_bytes = generate_pdf_from_analysis_data(payload)
    filename = "resumefit-analysis-report.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{record_id}/export/pdf")
def export_saved_analysis_pdf(
    record_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    session_id = resolve_session_id(request, response)
    record = get_analysis_record(db, session_id, record_id)
    pdf_bytes = generate_analysis_pdf(record)
    filename = f"resumefit-analysis-{record_id}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
