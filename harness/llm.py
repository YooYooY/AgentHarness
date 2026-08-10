from config import client
from tools.schema import TOOLS


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
