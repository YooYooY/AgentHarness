import json
from config import DEFAULT_MAX_TOKENS, MODEL_ID
from hooks import trigger_hooks
from tools.executor import exectue_tool
from llm import call_llm
from prompt import get_system_prompt
from utils import assistant_message_dict, log


def agent_loop(messages: list):
    max_tokens = DEFAULT_MAX_TOKENS
    model = MODEL_ID
    # Continue until the model returns a response without tool calls.
    while True:
        system = get_system_prompt()
        response = call_llm(system, messages, max_tokens, model)
        choice = response.choices[0]
        assistant = choice.message
        messages.append(assistant_message_dict(assistant))
        if not assistant.tool_calls:
            force = trigger_hooks("Stop", messages)
            if force:
                messages.append({"role": "user", "content": force})
                continue
            return
        for tool_call in assistant.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments or "{}")

            blocked = trigger_hooks("PreToolUse", name, args)
            if blocked:
                log.warn(f"\n⛔ str{blocked}")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(blocked),
                    }
                )
                continue

            output = exectue_tool(name, args)
            trigger_hooks("PostToolUse", name, args, output)
            messages.append(
                {"role": "tool", "tool_call_id": tool_call.id, "content": output}
            )
