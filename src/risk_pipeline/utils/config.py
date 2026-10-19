"""Environment-based LLM settings, provider-agnostic via litellm."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class ConfigurationError(Exception):
    """Raised when required configuration is missing."""


@dataclass(frozen=True)
class Settings:
    model: str
    api_key: str | None
    base_url: str | None
    request_delay: float = 0.0


def load_settings(
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    request_delay: float | None = None,
) -> Settings:
    """Load LLM settings from arguments, falling back to the environment (.env).

    ``model`` is a litellm model string, e.g. ``gemini/gemini-2.5-flash``,
    ``openai/gpt-4o-mini``, or ``openai/<name>`` with a custom ``LLM_BASE_URL``.

    ``request_delay`` is seconds to pause before each LLM call, used to stay
    under provider rate limits; it falls back to ``LLM_REQUEST_DELAY``.
    """
    resolved_model = model or os.getenv("LLM_MODEL")
    if not resolved_model:
        raise ConfigurationError(
            "No LLM model configured. Set LLM_MODEL in .env (or pass --model), "
            "e.g. LLM_MODEL=gemini/gemini-2.5-flash"
        )
    resolved_delay = (
        request_delay
        if request_delay is not None
        else float(os.getenv("LLM_REQUEST_DELAY", "0") or 0)
    )
    return Settings(
        model=resolved_model,
        api_key=api_key or os.getenv("LLM_API_KEY") or None,
        base_url=base_url or os.getenv("LLM_BASE_URL") or None,
        request_delay=resolved_delay,
    )
