"""Observe exponential-backoff log output when the LLM API returns 429 / 529.

Injects synthetic RateLimitError (429) and APIStatusError (529) into
llm.client.chat.completions.create, runs them through llm.with_retry
(the same code path used by the agent loop), captures the logger output,
and measures the real wall-clock delays to verify exponential backoff.
"""
import io
import os
import sys
import time
from types import SimpleNamespace

HARNESS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "harness")
sys.path.insert(0, os.path.abspath(HARNESS))
os.chdir(os.path.abspath(HARNESS))  # so config.load_dotenv() picks up harness/.env

from openai import APIStatusError, RateLimitError  # noqa: E402
from rich.console import Console  # noqa: E402

import llm  # noqa: E402
from utils import log  # noqa: E402


class FakeResponse:
    """Minimal httpx-like response for constructing openai exceptions."""

    def __init__(self, status_code):
        self.status_code = status_code
        self.request = SimpleNamespace()
        self.headers = {}


class FakeMessage:
    content = "ok"
    role = "assistant"
    tool_calls = []
    refusal = None


class FakeChoice:
    def __init__(self):
        self.message = FakeMessage()


class FakeCompletion:
    def __init__(self):
        self.choices = [FakeChoice()]


def run_scenario(name, error_factory, n_errors, state, restore_model):
    """Patch create() to fail n_errors times, then succeed. Returns (logs, gaps)."""
    buffer = io.StringIO()
    log.console = Console(file=buffer, force_terminal=False, width=120)

    calls = []

    def fake_create(**kwargs):
        calls.append(time.monotonic())
        if len(calls) <= n_errors:
            raise error_factory()
        return FakeCompletion()

    original = llm.client.chat.completions.create
    llm.client.chat.completions.create = fake_create
    start = time.monotonic()
    try:
        result = llm.with_retry(
            lambda: llm.client.chat.completions.create(
                model=state.current_model,
                messages=[{"role": "user", "content": "hi"}],
                tools=[],
                max_tokens=16,
            ),
            state,
        )
    finally:
        llm.client.chat.completions.create = original
        log.console = Console(force_terminal=False, width=120)

    gaps = [round(b - a, 3) for a, b in zip(calls, calls[1:])]
    elapsed = round(time.monotonic() - start, 3)
    return buffer.getvalue(), gaps, elapsed, result


def main():
    print("=" * 78)
    print("config: MAX_RETRIES=%s BASE_DELAY_MS=%s MAX_CONSECUTIVE_529=%s"
          % (llm.MAX_RETRIES, llm.BASE_DELAY_MS, llm.MAX_CONSECUTIVE_529))
    print("MODEL_ID=%s FALLBACK_MODEL_ID=%s" % (llm.MODEL_ID, llm.FALLBACK_MODEL_ID))
    print("expected backoff bases (s):",
          [round(min(llm.BASE_DELAY_MS * 2**i, 32000) / 1000, 2)
           for i in range(5)])
    print("=" * 78)

    # ---- Scenario A: 429 RateLimitError -------------------------------------
    state = llm.RecoveryState()
    logs, gaps, elapsed, _ = run_scenario(
        "429", lambda: RateLimitError(
            "rate limit exceeded", response=FakeResponse(429), body=None
        ), 4, state, None)
    print("\n### Scenario A: 429 (RateLimitError) x4 then success ###")
    print("-- captured log output --")
    print(logs)
    print("-- measured wall-clock gaps between attempts (s): %s" % gaps)
    print("-- total elapsed: %.3fs; current_model=%s; consecutive_529=%s"
          % (elapsed, state.current_model, state.consecutive_529))

    # ---- Scenario B: 529 overloaded ------------------------------------------
    state = llm.RecoveryState()
    logs, gaps, elapsed, _ = run_scenario(
        "529", lambda: APIStatusError(
            "overloaded", response=FakeResponse(529), body=None
        ), 4, state, None)
    print("\n### Scenario B: 529 (APIStatusError) x4 then success ###")
    print("-- captured log output --")
    print(logs)
    print("-- measured wall-clock gaps between attempts (s): %s" % gaps)
    print("-- total elapsed: %.3fs; current_model=%s; consecutive_529=%s"
          % (elapsed, state.current_model, state.consecutive_529))


if __name__ == "__main__":
    main()
