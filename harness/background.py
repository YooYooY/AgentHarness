import re
import threading

from tools.executor import execute_tool
from utils import log


_SLOW_PATTERNS = [
    "install",
    "build",
    "test",
    "deploy",
    "compile",
    "docker build",
    "pip install",
    "npm install",
    "cargo build",
    "pytest",
    "make",
]

# pre-compiled, word-boundary matched (so "install" won't match "uninstall",
# "test" won't match "_test_bg.py", "make" won't match "makefile", etc.)
_slow_pattern_re = re.compile(
    r"\b(?:" + "|".join(re.escape(p) for p in _SLOW_PATTERNS) + r")\b"
)

_bg_counter = 0

background_lock = threading.Lock()
background_tasks = {}
background_results = {}


def is_slow_operation(name, tool_input: dict) -> bool:
    if name != "bash":
        return False
    cmd = tool_input.get("command", "").lower()
    return bool(_slow_pattern_re.search(cmd))


def should_run_background(name, tool_input: dict) -> bool:
    if name == "bash" and tool_input.get("run_in_background", False):
        return True
    return is_slow_operation(name, tool_input)


def start_background_task(tool_call_id: str, name: str, tool_input: dict):
    global _bg_counter
    _bg_counter += 1
    bg_id = f"bg_{_bg_counter:04d}"
    cmd = tool_input.get("command", name)

    def worker():
        try:
            result = execute_tool(name, tool_input)
        except Exception as e:
            result = f"Error: {type(e).__name__}: {e}"

        with background_lock:
            background_results[bg_id] = result
            background_tasks[bg_id]["status"] = "completed"

    with background_lock:
        background_tasks[bg_id] = {
            "tool_call_id": tool_call_id,
            "command": cmd,
            "status": "running",
        }

    threading.Thread(target=worker, daemon=True).start()
    log.info(f"[Run Background Task] {bg_id}: {cmd[:40]}")
    return bg_id


def collect_background_results():
    with background_lock:
        ready_ids = [
            bg_id
            for bg_id, task in background_tasks.items()
            if task["status"] == "completed"
        ]
    notifications = []
    for bg_id in ready_ids:
        with background_lock:
            task = background_tasks[bg_id]
            output = background_results.pop(bg_id, "")
        summary = output[:500] if len(output) > 500 else output
        notifications.append(
            f"<task_notification>\n"
            f"  <task_id>{bg_id}</task_id>"
            f"  <status>completed</status>"
            f"  <command>{task['command']}</command>"
            f"  <summary>{summary}</summary>"
            f"</task_notification>\n"
        )
        log.magenta(
            f"[🎉 Background task completed] {bg_id}: {task['command']} ({len(output)} characters)"
        )
    return notifications
