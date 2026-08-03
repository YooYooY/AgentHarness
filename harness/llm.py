from config import client
from tools.schema import TOOLS


def call_llm(system: str, messages: list, max_token: int, model: str):
    return client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, *messages],
        tools=TOOLS,
        max_tokens=max_token
    )
