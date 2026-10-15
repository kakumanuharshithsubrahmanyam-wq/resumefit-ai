from typing import Optional, Protocol

from app.schemas.analysis import AIRecommendations, DeterministicAnalysisResult


class LLMProvider(Protocol):
    def generate_recommendations(
        self,
        *,
        job_title: str,
        company_name: Optional[str],
        job_description: str,
        resume_text: str,
        analysis: DeterministicAnalysisResult,
    ) -> AIRecommendations:
        ...
