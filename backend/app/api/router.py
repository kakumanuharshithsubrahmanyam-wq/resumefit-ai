from fastapi import APIRouter

from app.api.routes import analysis, health, history, resume

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(resume.router)
api_router.include_router(analysis.router)
api_router.include_router(history.router)
