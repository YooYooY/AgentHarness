import json
from config import DEFAULT_MAX_TOKENS, MODEL_ID
from history import micro_compact, snip_compact, tool_result_budget
from hooks import trigger_hooks
from tools.executor import exectue_tool
from llm import call_llm
from prompt import get_system_prompt
from utils import assistant_message_dict, log

rounds_since_todo = 0


def agent_loop(messages: list):
    global rounds_since_todo
    max_tokens = DEFAULT_MAX_TOKENS
    model = MODEL_ID
    # Continue until the model returns a response without tool calls.
    while True:
        system = get_system_prompt()
        messages[:] = tool_result_budget(messages)
        messages[:] = snip_compact(messages)
        messages[:] = micro_compact(messages)
        if rounds_since_todo >= 5 and messages:
            messages.append(
                {"role": "user", "content": "<remider>Update your todos.</remider>"}
            )
            log.info("💡 REMIDER: Update your todos.")
            rounds_since_todo = 0
        response = call_llm(system, messages, max_tokens, model)
        choice = response.choices[0]
        assistant = choice.message
        messages.append(assistant_message_dict(assistant))
        rounds_since_todo += 1
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
            if name == "todo_write":
                rounds_since_todo = 0
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
