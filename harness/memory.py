import json
import keyword
import re
import time
from config import (
    CONSOLIDATE_THRESHOLD,
    MEMORY_DIR,
    MEMORY_INDEX,
    MODEL_ID,
    TEXT_ENCODING,
)
from utils import llm_text, message_text, parse_frontmatter, log
from config import client


def list_memory_files():
    result = []
    for file in sorted(MEMORY_DIR.glob("*.md")):
        if file.name == "MEMORY.md":
            continue
        raw = file.read_text(encoding=TEXT_ENCODING, errors="replace")
        meta, body = parse_frontmatter(raw)
        result.append(
            {
                "filename": file.name,
                "name": meta.get("name", file.stem),
                "description": meta.get("description", ""),
                "type": meta.get("type", "user"),
                "body": body,
            }
        )
    return result


def select_relevant_memories(messages, max_items=5):
    files = list_memory_files()
    if not files:
        return []
    recent_texts = []
    for msg in reversed(messages):
        if msg.get("role") == "user":
            text = message_text(msg)
            if text:
                recent_texts.append(text)
            if len(recent_texts) >= 3:
                break

    recent = " ".join(reversed(recent_texts))[:2000]
    if not recent.strip():
        return []
    # log.magenta(f"[🔖 Memories->Recent message]\n{recent}")
    catalog = "\n".join(
        f"index: {index}: {file['name']} - {file['description']}"
        for index, file in enumerate(files)
    )
    # log.magenta("[🔖 Catalog]", catalog)
    prompt = (
        f"Select releveant memory indices. Return JSON array.\n"
        f"Example: [0, 3], if empty return [].\n"
        f"Recent conversation: \n{recent}\n\nMemory catalog:\n{catalog}"
    )
    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        text = llm_text(response)
        match = re.reach(r"\[.*\]", text, re.DOTALL)
        if match:
            indices = json.loads(match.group())
            selected = []
            for idx in indices:
                if isinstance(idx, int) and 0 <= idx < len(files):
                    selected.append(files[idx]["filename"])
                    if len(selected) >= max_items:
                        break
            return selected

    except Exception:
        return []

    keywords = [word.lower() for word in recent.split() if len(word) > 3]
    selected = []
    for f in files:
        text = f["name"] + " " + f["description"].lower()
        if any(kw in text for kw in keywords):
            selected.append(f["filename"])
            if len(selected) > max_items:
                break
    return selected


def read_memory_file(filename):
    path = MEMORY_DIR / filename
    if not path.exists():
        return None
    return path.read_text(encoding=TEXT_ENCODING, errors="replace")


def load_memories(messages: list):
    selected_files = select_relevant_memories(messages)
    if not selected_files:
        return ""
    parts = ["<relevant_memories>"]
    for filename in selected_files:
        content = read_memory_file(filename)
        if content:
            parts.append(content)
    parts.append("</relevant_memories>")
    return "\n\n".join(parts)


def _rebuild_index():
    lines = []
    for f in sorted(MEMORY_DIR.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        raw = f.read_text(encoding=TEXT_ENCODING, errors="replace")
        meta, body = parse_frontmatter(raw)
        name = meta.get("name", f.stem)
        desc = meta.get("description", body.split("\n")[0][:80])
        lines.append(f"- [{name}]({f.name}) - {desc}")
    MEMORY_INDEX.write_text(
        "\n".join(lines) + "\n" if lines else "", encoding=TEXT_ENCODING
    )


def write_memory_file(name, mem_type, description, body):
    slug = name.lower().replace(" ", "-").replace("/", "-")
    filepath = MEMORY_DIR / f"{slug}.md"
    filepath.write_text(
        f"---\nname: {name}\ndescription: {description}\ntype: {mem_type}\n---\n\n{body}\n",
        encoding=TEXT_ENCODING,
    )

    _rebuild_index()
    return filepath


def extract_memories(messages: list):
    dialogue_parts = []
    for msg in messages[-10:]:
        role = msg.get("role", "?")
        text = message_text(msg)
        if text:
            dialogue_parts.append(f"{role}:{text}")
    dialogue = "\n".join(dialogue_parts)
    if not dialogue.strip():
        return
    existing = list_memory_files()
    existing_desc = (
        "\n".join(f"- {m['name']}: {m['description']}" for m in existing)
        if existing
        else "(empty)"
    )

    prompt = (
        "Extract user preferences, constraints, or project fact.\n"
        "Return JSON array: [{name, type, description, body}]. \n"
        "If nothing new or already covered, return [].\n\n"
        f"Existing memories:\n{existing_desc}\n\nDialogue:\n{dialogue[:4000]}"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_ID, messages=[{"role": "user", "content": prompt}]
        )
        text = llm_text(response)
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return
        items = json.loads(match.group())
        if not items:
            return
        count = 0
        names = []
        for mem in items:
            name = mem.get("name", f"memory_{int(time.time())}")
            names.append(name)
            mem_type = mem.get("type", "user")
            desc = mem.get("description", "")
            body = mem.get("body", "")
            if desc and body:
                write_memory_file(name, mem_type, desc, body)
                count += 1
        if count:
            log.magenta(f"[🔖 Memories] {count} new memories has extracted!")
    except Exception as e:
        pass


def consolidate_memories():
    files = list_memory_files()
    if len(files) < CONSOLIDATE_THRESHOLD:
        return
    catalog = "\n\n".join(
        f"## {f['filename']}\nname:{f['name']}\ndescription:{f['description']}\n{f['body']}"
        for f in files
    )
    prompt = (
        "Merge the following memory files, rules:\n"
        "1. Merge duplicates into one.\n"
        "2. Delete outdated/contradictory memories\n"
        "3. Keep the total number of memories under 30.\n"
        "4. Prioritize retaining important user preferences.\n"
        "Return a JSON array, each item: {name, type, description, body}\n\n"
        f"{catalog}"
    )
    try:
        response = client.chat.completions.create(
            model=MODEL_ID, messages=[{"role": "user", "content": prompt}]
        )
        text = llm_text(response)
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return
        items = json.loads(match.group())
        for f in MEMORY_DIR.glob("*.md"):
            if f.name != "MEMORY.md":
                f.unlink()
        for mem in items:
            name = mem.get("name", f"memory_{int(time.time())}")
            mem_type = mem.get("type", "user")
            desc = mem.get("description", "")
            body = mem.get("body", "")
            if desc and body:
                write_memory_file(name, mem_type, desc, body)
        log.magenta(
            f"[🔖 Memories Consolidate] The memory Entries {len(files)}->{len(items)} have been organized"
        )

    except Exception:
        pass
