"""Provider-agnostic LLM access via litellm."""

from __future__ import annotations

import json
import logging
import re
import time

import litellm
from litellm.exceptions import RateLimitError

from risk_pipeline.utils.config import Settings

logger = logging.getLogger(__name__)

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)

# Rate-limit handling: retry a throttled call a few times before giving up.
MAX_RATE_LIMIT_ATTEMPTS = 4
RATE_LIMIT_BACKOFF_SECONDS = 20.0


def _extract_json(content: str) -> dict:
    """Parse a JSON object from model output, tolerating code fences."""
    cleaned = _FENCE.sub("", content.strip()).strip()
    return json.loads(cleaned)


def _completion_with_backoff(messages: list[dict], settings: Settings):
    """Call the LLM once, retrying while the provider throttles us.

    A rate-limited call is retried rather than raised, because the caller
    treats an exception as "this page produced nothing" - which would silently
    drop a page and distort recall instead of showing a real failure.
    """
    if settings.request_delay > 0:
        time.sleep(settings.request_delay)

    for attempt in range(1, MAX_RATE_LIMIT_ATTEMPTS + 1):
        try:
            return litellm.completion(
                model=settings.model,
                messages=messages,
                api_base=settings.base_url,
                api_key=settings.api_key,
                temperature=0,
                response_format={"type": "json_object"},
            )
        except RateLimitError:
            if attempt == MAX_RATE_LIMIT_ATTEMPTS:
                logger.error(
                    "Rate limited after %d attempts; giving up", MAX_RATE_LIMIT_ATTEMPTS
                )
                raise
            wait = RATE_LIMIT_BACKOFF_SECONDS * attempt
            logger.warning(
                "Rate limited by %s (attempt %d/%d); retrying in %.0fs",
                settings.model,
                attempt,
                MAX_RATE_LIMIT_ATTEMPTS,
                wait,
            )
            time.sleep(wait)

    raise AssertionError("unreachable")


def complete_json(messages: list[dict], settings: Settings) -> dict:
    """Call the configured LLM and return a parsed JSON object.

    Retries once when the response is not valid JSON.
    """
    for attempt in range(2):
        response = _completion_with_backoff(messages, settings)
        content = response.choices[0].message.content or ""
        try:
            return _extract_json(content)
        except json.JSONDecodeError:
            logger.warning("LLM returned non-JSON output (attempt %d)", attempt + 1)
    raise ValueError("LLM did not return valid JSON after retries")
