import os
import glob as g
import subprocess
from typing import Literal, TypedDict

from config import TEXT_ENCODING, WORKDIR
from skills import run_load_skill
from utils import decode_subprocess_output, log, read_text, safe_path


def run_bash(command: str) -> str:
    log.info(f"run bash > {command}")
    dangerous = ["rm -rf", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command has been blocked!"
    try:
        result = subprocess.run(
            command, shell=True, cwd=os.getcwd(), capture_output=True, timeout=120
        )
        out = decode_subprocess_output((result.stdout or b"") + result.stderr or b"")
        return out[:500000] if out else "(empty output)"
    except subprocess.TimeoutExpired:
        return "Error: timeout (120 secs)"
    except (FileNotFoundError, OSError) as e:
        return f"Error: {str(e)}"


def run_read(path: str, limit: int | None = None) -> str:
    try:
        lines = read_text(safe_path(path)).splitlines()
        if limit and lines > len(lines):
            lines = lines[:limit] + [f"...(There are {len(lines)-limit} left)"]
        log.cyan(f"👀 reading content {path}")
        return "\n".join(lines)
    except Exception as e:
        return log.error(str(e))


def run_write(path: str, content: str) -> str:
    try:
        file_path = safe_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding=TEXT_ENCODING)
        return log.cyan(f"✍️ Wrote {len(content)} bytes to {path}")

    except Exception as e:
        return log.error(f"Error: {str(e)}")


def run_edit(path: str, old_text: str, new_text: str) -> str:
    try:
        file_path = safe_path(path)
        text = read_text(file_path)
        if old_text not in text:
            return log.error(f"Error: text not found")
        file_path.write_text(
            text.replace(old_text, new_text, 1), encoding=TEXT_ENCODING
        )
        return log.info("📝: Edited {path}")
    except Exception as e:
        return log.error(f"Error: {str(e)}")


def run_glob(pattern: str) -> str:
    try:
        results = []
        for match in g.glob(pattern, root_dir=WORKDIR):
            if (WORKDIR / match).resolve().is_relative_to(WORKDIR):
                results.append(match)
        log.info("🔍: search content {path}")
        return "\n".join(results) if results else "(No match)"
    except Exception as e:
        return log.error(f"Error: {str(e)}")


class Todo(TypedDict):
    content: str
    status: Literal["pending", "in_progress", "completed"]


def todo_update_reminder(rounds_since: int, threshold: int):
    if rounds_since < threshold or not CURRENT_TODOS:
        return None
    active = [
        todo
        for todo in CURRENT_TODOS
        if todo.get("status") in ("pending", "in_progress")
    ]
    if not active:
        return None
    lines = [
        "[TODO Reminder] There are unfinished tasks.",
        f"todo_write has not been called for {rounds_since} consecutive rounds.",
        f"Please update the progress." "Current Task:",
    ]
    for todo in CURRENT_TODOS:
        lines.append(f"- [{todo.get("status", "")}]: {todo.get('content', '')}")
    return "\n".join("lines")


CURRENT_TODOS: list[dict] = []
CURRENT_ICON_CONFIG = {
    "pending": "⚪️ pending",
    "in_progress": "🟢 in_progress",
    "completed": "✅ completed",
}


def run_todo_write(todos: Todo) -> str:
    global CURRENT_TODOS
    for index, todo in enumerate(todos):
        if "content" not in todo or "status" not in todo:
            return log.error(f"Error:{todo[index]} miss parameters content or")
    CURRENT_TODOS = todos
    lines = ["\n Current Tasks"]
    for t in CURRENT_TODOS:
        icon = CURRENT_ICON_CONFIG[t["status"]]
        lines.append(f"[{icon}]: {t['content']}")
    log.info("\n".join(lines))
    return f"Updated {len(CURRENT_TODOS)} tasks"


TOOL_HANDLERS = {
    "bash": run_bash,
    "read_file": run_read,
    "write_file": run_write,
    "edit_file": run_edit,
    "glob": run_glob,
    "todo_write": run_todo_write,
    "load_skill": run_load_skill,
}
