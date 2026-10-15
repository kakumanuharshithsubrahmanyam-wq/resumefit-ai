from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db.models import Base

_engine = None
SessionLocal = None


def _ensure_sqlite_path(url: str) -> None:
    if url.startswith("sqlite:///"):
        relative = url.replace("sqlite:///", "", 1)
        if relative and relative != ":memory:":
            Path(relative).parent.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    global _engine, SessionLocal
    settings = get_settings()
    _ensure_sqlite_path(settings.database_url)
    _engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False}
        if settings.database_url.startswith("sqlite")
        else {},
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    Base.metadata.create_all(bind=_engine)


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
