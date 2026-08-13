import random
import time

from openai import APIStatusError, RateLimitError
from config import (
    BASE_DELAY_MS,
    DEFAULT_MAX_TOKENS,
    FALLBACK_MODEL_ID,
    MAX_CONSECUTIVE_529,
    MAX_RETRIES,
    MODEL_ID,
    client,
)
from tools.schema import TOOLS
from utils import log


def call_llm(system: str, messages: list, max_token: int, model: str):
    return client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, *messages],
        tools=TOOLS,
        max_tokens=max_token,
    )


def is_prompt_too_long_error(e: Exception):
    msg = str(e).lower()
    return (
        ("prompt" in msg and "long" in msg)
        or "prompt_is_too_long" in msg
        or "context_length_exceeded" in msg
        or "max_context_window" in msg
        or "contxt_length" in msg
        or "maximum content" in msg
    )


class RecoveryState:
    def __init__(self):
        self.has_escalated = False
        self.current_model = MODEL_ID
        self.consecutive_529 = 0
        self.max_tokens = DEFAULT_MAX_TOKENS
        self.has_attempted_reactive_compact = False
        self.recovery_count = 0


def _is_rate_limit_error(e: Exception):
    if isinstance(e, RateLimitError):
        return True
    msg = str(e).lower()
    name = type(e).__name__.lower()
    return "ratelimit" in name or "429" in msg


def _is_overloaded_error(e: Exception):
    if isinstance(e, APIStatusError) and e.status_code == 529:
        return True
    msg = str(e).lower()
    name = type(e).__name__.lower()
    return "overloaded" in name or "529" in msg


def retry_delay(attempt: int, retry_after=None):
    if retry_after:
        try:
            return float(retry_after)
        except (TypeError, ValueError):
            pass
    base = min(BASE_DELAY_MS * 2**attempt, 32000) / 1000
    return base + random.uniform(0, base * 0.25)


def with_retry(fn, state: RecoveryState):
    for attempt in range(MAX_RETRIES):
        try:
            result = fn()
            return result
        except Exception as e:
            if _is_rate_limit_error(e):
                delay = retry_delay(attempt)
                log.info(
                    f"[Rate limit] Retries {attempt+1}/{MAX_RETRIES}, wait:{delay:.1f}s"
                )
                time.sleep(delay)
                continue
            if _is_overloaded_error(e):
                state.consecutive_529 += 1
                if state.consecutive_529 >= MAX_CONSECUTIVE_529:
                    if FALLBACK_MODEL_ID:
                        state.current_model = FALLBACK_MODEL_ID
                        log.info(f"Replace to backup model: {FALLBACK_MODEL_ID}")
                    else:
                        state.consecutive_529 = 0
                        log.info("Empty backup model, please retry")
            delay = retry_delay(attempt)
            time.sleep(delay)
            continue
    raise RuntimeError(f"excessive max retries ({MAX_RETRIES})")
