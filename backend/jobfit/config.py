"""Settings read from environment variables.

Everything has a sensible default so the app runs with no configuration.
The provider is picked in this order:

1. JOBFIT_PROVIDER if set ("anthropic", "deepseek" or "mock")
2. "anthropic" if ANTHROPIC_API_KEY is set
3. "deepseek" if DEEPSEEK_API_KEY is set
4. "mock" (offline keyword matching, no API key needed)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROVIDERS = {"anthropic", "deepseek", "mock"}
EFFORT_LEVELS = {"low", "medium", "high", "xhigh", "max"}


def _str_env(name: str) -> str | None:
    return os.getenv(name, "").strip() or None


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _effort_env(name: str, default: str) -> str:
    value = os.getenv(name, "").strip().lower() or default
    if value not in EFFORT_LEVELS:
        raise ValueError(f"{name} must be one of {sorted(EFFORT_LEVELS)}, got {value!r}")
    return value


@dataclass(frozen=True)
class Settings:
    provider: str = "mock"
    anthropic_api_key: str | None = None
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    # Model names. None means "use the provider's default" (see each client).
    extract_model: str | None = None
    match_model: str | None = None
    # Claude only: how much the model thinks before answering.
    extract_effort: str = "low"
    match_effort: str = "medium"
    max_upload_bytes: int = 2_000_000
    max_text_chars: int = 30_000
    # Two cost guards: analyses per visitor per hour, and analyses for the whole site per day.
    rate_limit_per_hour: int = 10
    daily_analysis_limit: int = 200
    cors_origins: tuple[str, ...] = ()
    static_dir: Path | None = None
    # Header that carries the visitor's real IP when the app runs behind a hosting proxy
    # (Fly.io sets Fly-Client-IP). Only set this when that proxy always overwrites the header,
    # otherwise visitors could fake it to dodge the rate limit.
    client_ip_header: str | None = None

    @classmethod
    def from_env(cls) -> Settings:
        anthropic_key = _str_env("ANTHROPIC_API_KEY")
        deepseek_key = _str_env("DEEPSEEK_API_KEY")

        provider = (_str_env("JOBFIT_PROVIDER") or "").lower()
        if not provider:
            provider = "anthropic" if anthropic_key else "deepseek" if deepseek_key else "mock"
        if provider not in PROVIDERS:
            raise ValueError(f"JOBFIT_PROVIDER must be one of {sorted(PROVIDERS)}, got {provider!r}")

        origins = tuple(o.strip() for o in os.getenv("JOBFIT_CORS_ORIGINS", "").split(",") if o.strip())
        static = _str_env("JOBFIT_STATIC_DIR")

        return cls(
            provider=provider,
            anthropic_api_key=anthropic_key,
            deepseek_api_key=deepseek_key,
            deepseek_base_url=_str_env("DEEPSEEK_BASE_URL") or cls.deepseek_base_url,
            extract_model=_str_env("JOBFIT_EXTRACT_MODEL"),
            match_model=_str_env("JOBFIT_MATCH_MODEL"),
            extract_effort=_effort_env("JOBFIT_EXTRACT_EFFORT", cls.extract_effort),
            match_effort=_effort_env("JOBFIT_MATCH_EFFORT", cls.match_effort),
            max_upload_bytes=_int_env("JOBFIT_MAX_UPLOAD_BYTES", cls.max_upload_bytes),
            max_text_chars=_int_env("JOBFIT_MAX_TEXT_CHARS", cls.max_text_chars),
            rate_limit_per_hour=_int_env("JOBFIT_RATE_LIMIT_PER_HOUR", cls.rate_limit_per_hour),
            daily_analysis_limit=_int_env("JOBFIT_DAILY_ANALYSIS_LIMIT", cls.daily_analysis_limit),
            cors_origins=origins,
            static_dir=Path(static) if static else None,
            client_ip_header=_str_env("JOBFIT_CLIENT_IP_HEADER"),
        )
