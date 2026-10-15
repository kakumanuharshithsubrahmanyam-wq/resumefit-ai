from typing import Optional

from sqlalchemy.orm import Session

from app.config import Settings
from app.schemas.analysis import AnalysisData, AnalysisRequest
from app.services.history_service import save_analysis_record
from app.services.matching_engine import run_deterministic_analysis
from app.services.recommendation_service import build_recommendations


def run_analysis(
    request: AnalysisRequest,
    settings: Settings,
    *,
    db: Optional[Session] = None,
    session_id: Optional[str] = None,
) -> AnalysisData:
    analysis = run_deterministic_analysis(
        resume_text=request.resume_text.strip(),
        job_description=request.job_description.strip(),
        parse_context=request.resume_parse_context,
    )
    recommendations = build_recommendations(
        settings=settings,
        analysis=analysis,
        job_title=request.job_title.strip(),
        company_name=request.company_name.strip() if request.company_name else None,
        job_description=request.job_description.strip(),
        resume_text=request.resume_text.strip(),
        request_ai=request.request_ai_recommendations,
        ai_consent=request.ai_consent,
    )
    result = AnalysisData(
        job_title=request.job_title.strip(),
        company_name=request.company_name.strip() if request.company_name else None,
        analysis=analysis,
        recommendations=recommendations,
    )

    if request.save_to_history:
        if db is None or not session_id:
            raise ValueError("Database session is required when save_to_history is enabled.")
        stored = save_analysis_record(
            db,
            session_id=session_id,
            data=result,
            resume_filename=request.resume_filename,
        )
        result.record_id = stored.id

    return result
