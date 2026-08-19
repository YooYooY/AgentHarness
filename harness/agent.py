import json
from config import (
    CONTEXT_LIMIT,
    CONTINUATION_PROMPT,
    DEFAULT_MAX_TOKENS,
    ESCALATE_MAX_TOKENS,
    MAX_RECOVERY_RETRIES,
    TODO_REMINDER_ROUNDS,
)
from background import (
    collect_background_results,
    should_run_background,
    start_background_task,
)
from cron import consume_cron_queue
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
from tools.executor import execute_tool
from llm import RecoveryState, call_llm, is_prompt_too_long_error, with_retry
from prompt import get_system_prompt
from utils import assistant_message_dict, log, message_text

rounds_since_todo = 0


def agent_loop(messages: list):
    state = RecoveryState()

    global rounds_since_todo

    while True:

        # consume cron job
        fired = consume_cron_queue()
        for job in fired:
            messages.append(
                {
                    "role": "user",
                    "content": f"[Cron Job Execute]: {job.prompt}",
                }
            )
            log.info(f"[⏰ inject cron schedule] {job.prompt}")

        bg_notification = collect_background_results()
        if bg_notification:
            messages.append({"role": "user", "content": "\n\n".join(bg_notification)})
            log.green(f"[Inject]: {len(bg_notification)} background result in messages")

        system = get_system_prompt()

        memories_content = load_memories(messages)
        if memories_content:
            system += "\n\n" + memories_content
            log.magenta(f"[🔖 Load memories]", memories_content)

        todo_remainder = todo_update_reminder(rounds_since_todo, TODO_REMINDER_ROUNDS)
        if todo_remainder:
            system += "\n\n" + todo_remainder
            log.info(
                f"💡 [TODO Reminder]: {rounds_since_todo} consecutive rounds not update."
            )

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
                lambda: call_llm(
                    system, messages, state.max_tokens, state.current_model
                ),
                state,
            )
        except Exception as e:
            if is_prompt_too_long_error(e):
                if not state.has_attempted_reactive_compact:
                    messages[:] = reactive_compact(messages)
                    state.has_attempted_reactive_compact = True
                    continue
                log.error("[Already try reactive compact, still too long]")
                messages.append(
                    {
                        "role": "assistant",
                        "content": "Error, can't continue due to prompt too long",
                    }
                )
                return
            name = type(e).__name__
            log.error(f"[can't recovery] {name} {str(e)[:100]}")
            messages.append(
                {"role": "assistant", "content": f"[Error] {name}:{str(e)[:100]}"}
            )
            return

        choice = response.choices[0]

        if choice.finish_reason == "length":
            if not state.has_escalated:
                state.max_tokens = ESCALATE_MAX_TOKENS
                state.has_escalated = True
                log.info(
                    f"[max_token] {DEFAULT_MAX_TOKENS} escalate to {ESCALATE_MAX_TOKENS}"
                )
                continue
            messages.append(assistant_message_dict(choice.message))
            if choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": "[output truncated; tool execution failed.]",
                        }
                    )
                continue
            if state.recovery_count < MAX_RECOVERY_RETRIES:
                messages.append({"role": "user", "content": CONTINUATION_PROMPT})
                state.recovery_count += 1
                log.info(f"Pick up {state.recovery_count}/{MAX_RECOVERY_RETRIES}")
                continue
            log.info("reach Recovery retries limit")
            return

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

            if should_run_background(name, args):
                bg_id = start_background_task(tool_call.id, name, args)
                output = (
                    f"background task {bg_id} started in background.\n"
                    f"command: {args.get('command', '')}\n"
                    f"result will be delivered via task notification when completed"
                )
            else:
                output = execute_tool(name, args)
            trigger_hooks("PostToolUse", name, args, output)
            messages.append(
                {"role": "tool", "tool_call_id": tool_call.id, "content": output}
            )
