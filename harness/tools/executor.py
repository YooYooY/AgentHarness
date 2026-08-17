import inspect
import json
from hooks import trigger_hooks
from tools.handlers import TOOL_HANDLERS
from utils import log, with_loading
from prompt import SUB_SYSTEM
from config import client, MODEL_ID, DEFAULT_MAX_TOKENS
from tools.schema import BASE_TOOLS
from utils import assistant_message_dict, extract_text


def execute_tool(name: str, args: dict) -> str:
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return f"Unknown tool {name}"

    try:
        sig = inspect.signature(handler)
        # only pass args the handler actually accepts, so harness-control
        # kwargs (e.g. run_in_background) never leak into the handler
        valid = {k: v for k, v in args.items() if k in sig.parameters}
        bound = sig.bind(**valid)
    except TypeError as e:
        return log.error(f"Invalid arguments: {e}")

    return handler(**bound.arguments)


@with_loading("👾 spawn Subagent...")
def run_spawn_subagent(description: str):
    log.info("] 👾 SubAgent start")
    messages = [{"role": "user", "content": description}]
    for _ in range(30):
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "system", "content": SUB_SYSTEM}, *messages],
            tools=BASE_TOOLS,
            max_tokens=DEFAULT_MAX_TOKENS,
        )
        assistant = response.choices[0].message
        messages.append(assistant_message_dict(assistant))
        if not assistant.tool_calls:
            break
        for tool_call in assistant.tool_calls:
            name = tool_call.function.name
            args_str = tool_call.function.arguments
            args = json.loads(args_str or "{}")
            blocked = trigger_hooks("PreToolUse", name, args)
            if blocked:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(blocked),
                    }
                )
                continue
            output = (
                execute_tool(name, args)
                if name in TOOL_HANDLERS
                else f"UNKNOW TOOL: {name}"
            )
            trigger_hooks("PostToolUse", name, args, output)
            log.info(f"[👾 SubAgent] {name}: {str(output)[:100]}")
            messages.append(
                {"role": "tool", "tool_call_id": tool_call.id, "content": output}
            )
    result = extract_text(messages[-1].get("content"))
    if not result:
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                result = extract_text(msg.get("content"))
                if result:
                    break;
    log.info("] 👾 SubAgent Finished Task")
    return result


TOOL_HANDLERS["spawn_subagent"] = run_spawn_subagent
