from secrets import choice
from config import DEFAULT_MAX_TOKENS, MODEL_ID
from llm import call_llm
from prompt import get_system_prompt
from utils import assistant_message_dict


def agent_loop(messages: list):
    max_tokens = DEFAULT_MAX_TOKENS
    model = MODEL_ID
    while True:
        system = get_system_prompt()
        response = call_llm(system, messages, max_tokens, model)
        choice = response.choices[0]
        assistant = choice.message
        messages.append(assistant_message_dict(assistant))
        if not assistant.tool_calls:
          return
        
