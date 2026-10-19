import pytest
from litellm.exceptions import RateLimitError

from risk_pipeline.utils import llm
from risk_pipeline.utils.config import Settings

SETTINGS = Settings(model="test/model", api_key=None, base_url=None)


def _rate_limited(**kwargs):
    raise RateLimitError(message="slow down", llm_provider="test", model="test/model")


class _Msg:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Msg(content)


class _Response:
    def __init__(self, content):
        self.choices = [_Choice(content)]


def _sleeper(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr(llm.time, "sleep", sleeps.append)
    return sleeps


def test_rate_limit_is_retried_then_succeeds(monkeypatch):
    sleeps = _sleeper(monkeypatch)
    responses = iter(
        [
            _rate_limited,
            _rate_limited,
            lambda **kwargs: _Response('{"risks": []}'),
        ]
    )
    monkeypatch.setattr(llm.litellm, "completion", lambda **kwargs: next(responses)())

    assert llm.complete_json([], SETTINGS) == {"risks": []}
    assert sleeps == [
        llm.RATE_LIMIT_BACKOFF_SECONDS,
        llm.RATE_LIMIT_BACKOFF_SECONDS * 2,
    ]


def test_rate_limit_gives_up_after_the_attempt_limit(monkeypatch):
    sleeps = _sleeper(monkeypatch)
    calls = []
    monkeypatch.setattr(
        llm.litellm,
        "completion",
        lambda **kwargs: (calls.append(kwargs), _rate_limited(**kwargs))[1],
    )

    with pytest.raises(RateLimitError):
        llm.complete_json([], SETTINGS)

    assert len(calls) == llm.MAX_RATE_LIMIT_ATTEMPTS
    assert len(sleeps) == llm.MAX_RATE_LIMIT_ATTEMPTS - 1


def test_json_retries_are_independent_of_rate_limit_retries(monkeypatch):
    """A rate-limited first attempt must not consume the JSON retry budget."""
    sleeps = _sleeper(monkeypatch)
    responses = iter(
        [
            _rate_limited,
            lambda **kwargs: _Response("not json"),
            lambda **kwargs: _Response('{"risks": []}'),
        ]
    )
    monkeypatch.setattr(llm.litellm, "completion", lambda **kwargs: next(responses)())

    assert llm.complete_json([], SETTINGS) == {"risks": []}


def test_request_delay_is_slept_before_the_first_call(monkeypatch):
    sleeps = _sleeper(monkeypatch)
    settings = Settings(
        model="test/model", api_key=None, base_url=None, request_delay=3.0
    )
    monkeypatch.setattr(
        llm.litellm, "completion", lambda **kwargs: _Response('{"risks": []}')
    )

    llm.complete_json([], settings)

    assert sleeps[0] == 3.0


def test_no_delay_is_applied_by_default(monkeypatch):
    sleeps = _sleeper(monkeypatch)
    monkeypatch.setattr(
        llm.litellm, "completion", lambda **kwargs: _Response('{"risks": []}')
    )

    llm.complete_json([], SETTINGS)

    assert sleeps == []
