import json
from utils import log
from config import WORKDIR

DENY_LIST = [
    "rm -rf /",
    "rm -rf /*",
    "rm -rf ~",
    "rm -rf $HOME",
    "sudo",
    "shutdown",
    "reboot",
    "poweroff",
    "halt",
    "mkfs",
    "dd if=",
    "> /dev/sda",
    ":(){ :|:& };:",
    "chmod -R 777 /",
    "chown -R",
]

DESTRUCTIVE = [
    "rm ",
    "rmdir ",
    "unlink ",
    "del ",
    "erase ",
    " -delete",
    " -exec ",
    " -execdir ",
    "chmod ",
    "chown ",
    "sed -i",
    "perl -i",
    "git clean",
    "git reset --hard",
    "git checkout --",
    "git restore",
]

HOOKS = {"UserPromptSubmit": [], "PreToolUse": [], "PostToolUse": [], "Stop": []}


def permission_hook(name: str, args: dict):
    if name == "bash":
        for pattern in DENY_LIST:
            if pattern in args.get("command", ""):
                return log.red(f"Blocked: '{pattern}' is on the deny list")
        for kw in DESTRUCTIVE:
            if kw in args.get("command", ""):
                log.warn("Potentially destructive command")
                log.warn(f"tool: {name}({args})")
                choice = input("   Allow? [y/N] ").strip().lower()
                if choice not in ("y", "yes"):
                    return "Deny"

    if name in ("write_file", "edit_file"):
        path = args.get("path", "")
        if not (WORKDIR / path).resolve().is_relative_to(WORKDIR):
            log.warn("Writing outside workspace")
            log.warn(f"tool: {name}({args})")
            choice = input("   Allow? [y/N] ").strip().lower()
            if choice not in ("y", "yes"):
                return "Denied: paths outside workspace are never allowed."

    return None


def log_hook(name: str, args: dict):
    log.info(f"[🪝HOOK PreToolUse] {name} {json.dumps(args, ensure_ascii=False)}")
    return None

def tool_output_hook(name: str, args: dict, output: str | None):
    log.cyan(f"[🪝HOOK PostToolUse] Tool [{name}] output: {output}")
    return None

def large_output_hook(name: str, args: dict, output):
    if len(str(output)) > 100000:
        log.info(
            f"[🪝HOOK PostToolUse]  ⚠️ {name} Large output from {name}, size = {len(str(output))}"
        )


def summary_hook(messages: list):
    tool_count = sum(1 for msg in messages if msg.get("role") == "tool")
    log.info(f"[🪝HOOK Stop]: session used {tool_count} tool calls")
    return None


def register_hook(event: str, callback):
    HOOKS[event].append(callback)


def trigger_user_prompt_hooks(query: str) -> str:
    current = query
    for callback in HOOKS["UserPromptSubmit"]:
        result = callback(current)
        if isinstance(result, str):
            current = result
    return current


def trigger_hooks(event: str, *args):
    for callback in HOOKS[event]:
        result = callback(*args)
        if result is not None:
            return result
    return None


def workspace_inject_hook(query: str) -> str | None:
    log.info(f"[🪝HOOK] Inject current working directory {WORKDIR}.\nquery: {query}")
    return f"<workspace>\n UserPromptSubmit: working in {WORKDIR}</workspace>\n\n{query}"


register_hook("UserPromptSubmit", workspace_inject_hook)
register_hook("PreToolUse", permission_hook)
register_hook("PreToolUse", log_hook)
register_hook("PostToolUse", large_output_hook)
register_hook("PostToolUse", tool_output_hook)
register_hook("Stop", summary_hook)
