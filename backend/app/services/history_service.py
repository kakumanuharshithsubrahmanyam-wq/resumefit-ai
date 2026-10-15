import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models import AnalysisRecord
from app.exceptions.api import APIRequestError
from app.schemas.analysis import AnalysisData, AnalysisHistoryItem, StoredAnalysisRecord
from fastapi import status


def save_analysis_record(
    db: Session,
    *,
    session_id: str,
    data: AnalysisData,
    resume_filename: Optional[str],
) -> StoredAnalysisRecord:
    payload = data.model_dump(mode="json")
    record = AnalysisRecord(
        session_id=session_id,
        job_title=data.job_title,
        company_name=data.company_name,
        resume_filename=resume_filename,
        result_json=json.dumps(payload),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _to_stored(record)


def list_history(db: Session, session_id: str) -> List[AnalysisHistoryItem]:
    rows = (
        db.query(AnalysisRecord)
        .filter(AnalysisRecord.session_id == session_id)
        .order_by(AnalysisRecord.created_at.desc())
        .all()
    )
    items: List[AnalysisHistoryItem] = []
    for row in rows:
        summary = _summary_from_json(row.result_json)
        items.append(
            AnalysisHistoryItem(
                id=row.id,
                created_at=row.created_at,
                job_title=row.job_title,
                company_name=row.company_name,
                resume_filename=row.resume_filename,
                overall_alignment=summary["overall_alignment"],
                required_skill_coverage=summary["required_skill_coverage"],
            ),
        )
    return items


def get_analysis_record(db: Session, session_id: str, record_id: str) -> StoredAnalysisRecord:
    row = (
        db.query(AnalysisRecord)
        .filter(AnalysisRecord.id == record_id, AnalysisRecord.session_id == session_id)
        .one_or_none()
    )
    if row is None:
        raise APIRequestError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="analysis_not_found",
            message="Analysis record was not found for this browser session.",
        )
    return _to_stored(row)


def delete_analysis_record(db: Session, session_id: str, record_id: str) -> None:
    row = (
        db.query(AnalysisRecord)
        .filter(AnalysisRecord.id == record_id, AnalysisRecord.session_id == session_id)
        .one_or_none()
    )
    if row is None:
        raise APIRequestError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="analysis_not_found",
            message="Analysis record was not found for this browser session.",
        )
    db.delete(row)
    db.commit()


def clear_history(db: Session, session_id: str) -> int:
    deleted = (
        db.query(AnalysisRecord)
        .filter(AnalysisRecord.session_id == session_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return int(deleted)


def _to_stored(row: AnalysisRecord) -> StoredAnalysisRecord:
    data = AnalysisData.model_validate_json(row.result_json)
    return StoredAnalysisRecord(
        id=row.id,
        created_at=row.created_at,
        job_title=row.job_title,
        company_name=row.company_name,
        resume_filename=row.resume_filename,
        data=data,
    )


def _summary_from_json(result_json: str) -> dict:
    payload = json.loads(result_json)
    scoring = payload.get("analysis", {}).get("scoring", {})
    return {
        "overall_alignment": float(scoring.get("overall_alignment", 0.0)),
        "required_skill_coverage": float(scoring.get("required_skill_coverage", 0.0)),
    }
