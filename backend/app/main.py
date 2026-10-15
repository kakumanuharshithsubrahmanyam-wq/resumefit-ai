from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.db.session import init_db
from app.exceptions import register_exception_handlers
from app.logging_config import configure_logging
from app.middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Analysis-Session-Id"],
    )
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.rate_limit_requests_per_minute,
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    return app


app = create_app()
