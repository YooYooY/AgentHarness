import json
import time
from config import (
    DEFAULT_MAX_TOKENS,
    KEEP_RECENT,
    MAX_BYTES,
    MAX_MESSAGE_LENGTH,
    MODEL_ID,
    PERSIST_THRESHOLD,
    TEXT_ENCODING,
    TOOL_RESULT_DIR,
    TRANSCRIPTS_DIR,
    client,
)
from utils import log, with_loading


def persist_large_output(tool_call_id: str, output: str):
    if len(output) < PERSIST_THRESHOLD:
        return output

    TOOL_RESULT_DIR.mkdir(parents=True, exist_ok=True)

    path = TOOL_RESULT_DIR / f"{tool_call_id}.txt"

    if not path.exists():
        path.write_text(output, encoding=TEXT_ENCODING)
    return f"<persisted_output>\n full output path: {path} \npreview: \n {output[:PERSIST_THRESHOLD]}</persisted_output>"


def tool_result_budget(messages: list, max_bytes: int = MAX_BYTES):
    indices = [
        index for index, message in enumerate(messages) if message.get("role") == "tool"
    ]
    if not indices:
        return messages

    total = sum(len(str(messages[index].get("content", ""))) for index in indices)
    if total < max_bytes:
        return messages

    ranked = sorted(
        indices,
        key=lambda index: len(str(messages[index].get("content", ""))),
        reverse=True,
    )
    if not ranked:
        return messages

    for index in ranked:
        if total <= max_bytes:
            break
        msg = messages[index]
        content = str(msg.get("content", ""))
        if len(content) <= PERSIST_THRESHOLD:
            continue
        tool_id = msg.get("tool_call_id", "unknow")
        msg["content"] = persist_large_output(tool_id, content)
        total = sum(len(str(messages[index].get("content", ""))) for index in indices)

    log.magenta("[🍔 HISTORY] Tool_result_budget")
    return messages


def repair_message_chain(messages: list):
    if not messages:
        return messages
    repaired_messages = []
    pending_call_ids = set()

    def flush_pending(reason: str):
        nonlocal pending_call_ids
        for tool_call_id in pending_call_ids:
            repaired_messages.append(
                {"role": "tool", "tool_call_id": tool_call_id, "content": reason}
            )
        pending_call_ids = set()

    for msg in messages:
        role = msg.get("role")
        if role == "assistant":
            flush_pending("[Already supplement tool response miss]")
            repaired_messages.append(msg)
            tool_calls = msg.get("tool_calls") or []
            pending_call_ids = {
                tool_call.get("id")
                for tool_call in tool_calls
                if isinstance(tool_call, dict) and tool_call.get("id")
            }
            continue
        elif role == "tool":
            tool_call_id = msg.get("tool_call_id")
            if tool_call_id and tool_call_id in pending_call_ids:
                repaired_messages.append(msg)
                pending_call_ids.discard(tool_call_id)
            continue
        else:
            flush_pending("[Already supplement tool response miss]")
            repaired_messages.append(msg)

    flush_pending("[Already supplement tool response miss]")
    return repaired_messages


def snip_compact(messages: list, max_messages: int = MAX_MESSAGE_LENGTH):
    if len(messages) <= max_messages:
        return messages
    keep_head, keep_tail = 3, max_messages - 3
    snipped = len(messages) - keep_head - keep_tail
    compacted_messages = (
        messages[:keep_head]
        + [
            {
                "role": "user",
                "content": f"[snipped {snipped} messages from conversation middle]",
            }
        ]
        + messages[-keep_tail:]
    )
    log.magenta("[🍔 HISTORY] snip_compact")
    return repair_message_chain(compacted_messages)


def collect_tool_messages(messages: list):
    return [
        (index, msg) for index, msg in enumerate(messages) if msg.get("role") == "tool"
    ]


def micro_compact(messages: list):
    tool_msgs = collect_tool_messages(messages)
    if len(tool_msgs) <= KEEP_RECENT:
        return messages
    for index, msg in tool_msgs[:-KEEP_RECENT]:
        content = str(msg.get("content", ""))
        if len(content) > 1000:
            log.magenta("[🍔 HISTORY] micro_compact")
            msg["content"] = "[Eearlier tool result compacted. Re-run if needed.]"
    return messages


def estimate_size(messages: list):
    return len(str(messages))


def write_transcript(messages: list):
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    path = TRANSCRIPTS_DIR / f"transcript_{int(time.time())}.jsonl"
    with path.open("w", encoding=TEXT_ENCODING) as f:
        for msg in messages:
            f.write(json.dumps(msg, default=str, ensure_ascii=False) + "\n")
    return path


@with_loading("📜 summarize history...")
def summarize_history(messages: list):
    conversation = json.dumps(messages, default=str, ensure_ascii=False)[:80000]
    prompt = (
        "Summarize the following Agent dialogue to continue the work\n"
        "Retain:\n"
        "1. Current Objective"
        "2. Key findings and decisions"
        "3. Documents read and modified"
        "4. Remaining work"
        "5. User constraints"
        "\nConcise but specific. \n\n" + conversation
    )
    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=DEFAULT_MAX_TOKENS,
    )
    return (response.choices[0].message.content or "").strip() or "(empty summarize)"


def compact_history(messages: list):
    transcript_path = write_transcript(messages)
    log.magenta(f"[🍔 HISTORY] compact_history: f{transcript_path}")
    summary = summarize_history(messages)
    return [{"role": "user", "content": f"[Compressed]\n\n {summary}"}]


def reactive_compact(messages: list):
    write_transcript(messages)
    summary = summarize_history(messages)
    log.magenta(f"[🍔 HISTORY] reactive compact")
    return repair_message_chain(
        [
            {"role": "user", "content": f"[reactive compact]\n\n{summary}"},
            *messages[-5:],
        ]
    )
