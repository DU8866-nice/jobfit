import pytest

from jobfit.config import Settings

ENV_VARS = [
    "ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY",
    "JOBFIT_PROVIDER",
    "JOBFIT_MATCH_EFFORT",
    "JOBFIT_DAILY_ANALYSIS_LIMIT",
    "JOBFIT_CORS_ORIGINS",
    "JOBFIT_CLIENT_IP_HEADER",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_defaults_to_mock_without_a_key():
    assert Settings.from_env().provider == "mock"


def test_uses_claude_when_a_key_is_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    settings = Settings.from_env()
    assert settings.provider == "anthropic"
    assert settings.anthropic_api_key == "sk-test"


def test_uses_deepseek_when_only_its_key_is_set(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds")
    settings = Settings.from_env()
    assert settings.provider == "deepseek"
    assert settings.extract_model is None, "None means the provider's default model"


def test_claude_wins_when_both_keys_are_set_unless_provider_is_explicit(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds")
    assert Settings.from_env().provider == "anthropic"
    monkeypatch.setenv("JOBFIT_PROVIDER", "deepseek")
    assert Settings.from_env().provider == "deepseek"


def test_reads_overrides(monkeypatch):
    monkeypatch.setenv("JOBFIT_MATCH_EFFORT", "HIGH")
    monkeypatch.setenv("JOBFIT_DAILY_ANALYSIS_LIMIT", "5")
    monkeypatch.setenv("JOBFIT_CORS_ORIGINS", "http://localhost:5173, https://example.com")
    monkeypatch.setenv("JOBFIT_CLIENT_IP_HEADER", "Fly-Client-IP")
    settings = Settings.from_env()
    assert settings.client_ip_header == "Fly-Client-IP"
    assert settings.match_effort == "high"
    assert settings.daily_analysis_limit == 5
    assert settings.cors_origins == ("http://localhost:5173", "https://example.com")


@pytest.mark.parametrize(
    "name, value",
    [("JOBFIT_PROVIDER", "openai"), ("JOBFIT_MATCH_EFFORT", "turbo"), ("JOBFIT_DAILY_ANALYSIS_LIMIT", "lots")],
)
def test_rejects_bad_values(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError):
        Settings.from_env()
