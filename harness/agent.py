import json
from config import CONTEXT_LIMIT, DEFAULT_MAX_TOKENS, MODEL_ID, TODO_REMINDER_ROUNDS
from tools.handlers import todo_update_reminder
from memory import consolidate_memories, extract_memories, load_memories
from history import (
    compact_history,
    estimate_size,
    micro_compact,
    reactive_compact,
    repair_message_chain,
    snip_compact,
    tool_result_budget,
)
from hooks import trigger_hooks
from tools.executor import exectue_tool
from llm import RecoveryState, call_llm, is_prompt_too_long_error, with_retry
from prompt import get_system_prompt
from utils import assistant_message_dict, log, message_text

rounds_since_todo = 0


def agent_loop(messages: list):
    state = RecoveryState()

    global rounds_since_todo
    max_tokens = DEFAULT_MAX_TOKENS
    model = MODEL_ID
    # Continue until the model returns a response without tool calls.
    while True:
        system = get_system_prompt()

        memories_content = load_memories(messages)
        if memories_content:
            system += "\n\n" + memories_content
            log.magenta(f"[🔖 Load memories]", memories_content)

        todo_remainder = todo_update_reminder(rounds_since_todo, TODO_REMINDER_ROUNDS)
        if todo_remainder:
            system+="\n\n"+todo_remainder
            log.info("💡 [TODO Reminder]: {rounds_since_todo} consecutive rounds not update.")

        pre_compress = [
            {"role": m.get("role", ""), "content": message_text(m)}
            for m in messages
            if isinstance(m, dict)
        ]

        messages[:] = tool_result_budget(messages)
        messages[:] = snip_compact(messages)
        messages[:] = micro_compact(messages)

        if estimate_size(messages) > CONTEXT_LIMIT:
            messages[:] = compact_history(messages)

        messages[:] = repair_message_chain(messages)

        try:
            # response = call_llm(system, messages, max_tokens, model)
            response = with_retry(
                lambda max_tokens=max_tokens, model=state.current_model: call_llm(
                    system, messages, max_tokens, model
                ),
                state
            )
        except Exception as e:
            if is_prompt_too_long_error(e):
                messages[:] = reactive_compact(messages)
                continue

        choice = response.choices[0]
        assistant = choice.message
        messages.append(assistant_message_dict(assistant))
        rounds_since_todo += 1
        if not assistant.tool_calls:
            extract_memories(pre_compress)
            consolidate_memories()
            force = trigger_hooks("Stop", messages)
            if force:
                messages.append({"role": "user", "content": force})
                continue
            return
        for tool_call in assistant.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments or "{}")

            if name == "compact":
                messages[:] = compact_history(messages)
                break

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
