from typing import Optional

from app.config import Settings
from app.exceptions.api import APIRequestError
from app.schemas.analysis import AIRecommendations, DeterministicAnalysisResult
from app.services.ai.fallback_recommendations import build_fallback_recommendations
from fastapi import status

from app.services.ai.openai_provider import OpenAIRecommendationProvider


def build_recommendations(
    *,
    settings: Settings,
    analysis: DeterministicAnalysisResult,
    job_title: str,
    company_name: Optional[str],
    job_description: str,
    resume_text: str,
    request_ai: bool,
    ai_consent: bool,
) -> AIRecommendations:
    if not request_ai:
        return AIRecommendations(enabled=False, provider="disabled")

    if not ai_consent:
        raise APIRequestError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="ai_consent_required",
            message="AI recommendations require explicit consent before sending resume content to a provider.",
        )

    if not settings.ai_enabled or not settings.openai_api_key:
        return build_fallback_recommendations(analysis)

    provider = OpenAIRecommendationProvider(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        timeout_seconds=settings.ai_timeout_seconds,
        max_input_chars=settings.ai_max_input_chars,
    )
    try:
        return provider.generate_recommendations(
            job_title=job_title,
            company_name=company_name,
            job_description=job_description,
            resume_text=resume_text,
            analysis=analysis,
        )
    except Exception:
        fallback = build_fallback_recommendations(analysis)
        fallback.notes = (
            (fallback.notes or "")
            + " OpenAI request failed; deterministic fallback recommendations were used."
        ).strip()
        return fallback
