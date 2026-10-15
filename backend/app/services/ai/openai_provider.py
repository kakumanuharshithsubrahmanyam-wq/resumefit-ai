import json
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.config import Settings
from app.schemas.analysis import (
    AIRecommendations,
    DeterministicAnalysisResult,
    GroundedRecommendation,
    LearningPlanStep,
)


class _LLMRecommendationPayload(BaseModel):
    gap_explanations: List[str] = Field(default_factory=list)
    skill_improvements: List[GroundedRecommendation] = Field(default_factory=list)
    learning_topics: List[str] = Field(default_factory=list)
    project_ideas: List[str] = Field(default_factory=list)
    resume_bullet_suggestions: List[str] = Field(default_factory=list)
    learning_plan: List[LearningPlanStep] = Field(default_factory=list)
    notes: Optional[str] = None


class OpenAIRecommendationProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_input_chars: int,
    ) -> None:
        if not api_key.strip():
            raise ValueError("OpenAI API key must not be empty.")
        self._api_key = api_key.strip()
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_input_chars = max_input_chars

    def generate_recommendations(
        self,
        *,
        job_title: str,
        company_name: Optional[str],
        job_description: str,
        resume_text: str,
        analysis: DeterministicAnalysisResult,
    ) -> AIRecommendations:
        trimmed_resume = resume_text[: self.max_input_chars]
        trimmed_job = job_description[: self.max_input_chars]
        findings_summary = [
            {
                "label": finding.label,
                "status": finding.status.value,
                "importance": finding.importance.value,
                "evidence": finding.evidence[:2],
            }
            for finding in analysis.findings[:25]
        ]

        system_prompt = (
            "You are a career coach assistant. Use ONLY facts present in the resume text and "
            "deterministic findings. Never invent skills, employers, certifications, metrics, or "
            "experience. Mark suggestions as hypothetical when evidence is missing. Return JSON only."
        )
        user_prompt = {
            "job_title": job_title,
            "company_name": company_name,
            "job_description_excerpt": trimmed_job,
            "resume_excerpt": trimmed_resume,
            "deterministic_findings": findings_summary,
            "deterministic_scores": analysis.scoring.model_dump(),
            "output_schema": {
                "gap_explanations": ["string"],
                "skill_improvements": [
                    {
                        "title": "string",
                        "rationale": "string",
                        "grounded_in": "gap|partial_match|existing_evidence",
                        "related_requirements": ["string"],
                    },
                ],
                "learning_topics": ["string"],
                "project_ideas": ["string"],
                "resume_bullet_suggestions": [
                    "string starting with 'Suggested bullet (only if accurate):'"
                ],
                "learning_plan": [
                    {
                        "title": "string",
                        "focus": "string",
                        "estimated_effort": "string",
                        "actions": ["string"],
                    },
                ],
                "notes": "string",
            },
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            body = response.json()

        content = body["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        validated = _LLMRecommendationPayload.model_validate(parsed)
        return AIRecommendations(
            enabled=True,
            provider="openai",
            gap_explanations=validated.gap_explanations,
            skill_improvements=validated.skill_improvements,
            learning_topics=validated.learning_topics,
            project_ideas=validated.project_ideas,
            resume_bullet_suggestions=validated.resume_bullet_suggestions,
            learning_plan=validated.learning_plan,
            notes=validated.notes,
        )


def create_openai_provider(settings: Settings) -> Optional[OpenAIRecommendationProvider]:
    """Return a provider instance only when OpenAI is fully configured."""
    if not settings.openai_configured or not settings.openai_api_key:
        return None
    return OpenAIRecommendationProvider(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        timeout_seconds=settings.ai_timeout_seconds,
        max_input_chars=settings.ai_max_input_chars,
    )
