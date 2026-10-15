from app.config import Settings, get_settings
from app.services.ai.openai_provider import create_openai_provider


def test_openai_not_configured_when_key_missing() -> None:
    settings = Settings(ai_enabled=True, openai_api_key=None)
    assert settings.openai_configured is False
    assert create_openai_provider(settings) is None


def test_openai_not_configured_when_key_blank() -> None:
    settings = Settings(ai_enabled=True, openai_api_key="   ")
    assert settings.openai_configured is False
    assert create_openai_provider(settings) is None


def test_openai_configured_when_key_present() -> None:
    settings = Settings(ai_enabled=True, openai_api_key="test-key-local-only")
    assert settings.openai_configured is True
    provider = create_openai_provider(settings)
    assert provider is not None


def test_openai_disabled_when_ai_enabled_false() -> None:
    settings = Settings(ai_enabled=False, openai_api_key="test-key-local-only")
    assert settings.openai_configured is False
    assert create_openai_provider(settings) is None


def test_settings_reads_openai_key_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "env-test-key")
    monkeypatch.setenv("AI_ENABLED", "true")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.openai_configured is True
    get_settings.cache_clear()
