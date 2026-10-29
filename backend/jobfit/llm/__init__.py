"""Model providers. `get_client` picks one from the settings."""

from __future__ import annotations

from ..config import Settings
from .base import LLMClient, LLMError


def get_client(settings: Settings) -> LLMClient:
    if settings.provider == "anthropic":
        from .anthropic_client import AnthropicClient

        return AnthropicClient(settings)
    if settings.provider == "deepseek":
        from .deepseek_client import DeepSeekClient

        return DeepSeekClient(settings)
    from .mock_client import MockClient

    return MockClient()


__all__ = ["LLMClient", "LLMError", "get_client"]
