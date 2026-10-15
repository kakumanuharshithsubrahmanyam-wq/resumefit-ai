from app.services.ai.fallback_recommendations import build_fallback_recommendations
from app.services.matching_engine import run_deterministic_analysis


def test_fallback_recommendations_do_not_require_api_key() -> None:
    resume = """
    Skills: Python
    Experience
    - Built internal tools with Python
    """
    job = """
    Requirements
    - Python
    - Kubernetes
    - React
    """
    analysis = run_deterministic_analysis(resume, job)
    rec = build_fallback_recommendations(analysis)
    assert rec.provider == "deterministic_fallback"
    assert any("kubernetes" in item.lower() for item in rec.learning_topics)
    assert all("Suggested bullet" in bullet or "Suggested bullet" in bullet for bullet in rec.resume_bullet_suggestions) or rec.resume_bullet_suggestions == []
