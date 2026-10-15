from typing import List

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import AnalysisHistoryItem, StoredAnalysisRecord
from app.schemas.response import APIResponse
from app.services.history_service import (
    clear_history,
    delete_analysis_record,
    get_analysis_record,
    list_history,
)
from app.services.session_context import resolve_session_id

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=APIResponse[List[AnalysisHistoryItem]])
def get_history(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> APIResponse[List[AnalysisHistoryItem]]:
    session_id = resolve_session_id(request, response)
    items = list_history(db, session_id)
    return APIResponse(data=items, meta={"session_id": session_id, "count": len(items)})


@router.get("/{record_id}", response_model=APIResponse[StoredAnalysisRecord])
def get_history_item(
    record_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> APIResponse[StoredAnalysisRecord]:
    session_id = resolve_session_id(request, response)
    record = get_analysis_record(db, session_id, record_id)
    return APIResponse(data=record)


@router.delete("/{record_id}", response_model=APIResponse[dict])
def delete_history_item(
    record_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> APIResponse[dict]:
    session_id = resolve_session_id(request, response)
    delete_analysis_record(db, session_id, record_id)
    return APIResponse(data={"deleted": True, "id": record_id})


@router.delete("", response_model=APIResponse[dict])
def delete_all_history(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> APIResponse[dict]:
    session_id = resolve_session_id(request, response)
    deleted_count = clear_history(db, session_id)
    return APIResponse(data={"deleted_count": deleted_count})
