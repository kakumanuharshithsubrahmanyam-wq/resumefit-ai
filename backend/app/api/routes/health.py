from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.schemas.response import APIResponse

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> APIResponse[Dict[str, str]]:
    settings = get_settings()
    db.execute(text("SELECT 1"))
    return APIResponse(
        data={
            "status": "ok",
            "service": settings.app_name,
            "environment": settings.environment,
            "database": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
