from config import WORKDIR
from utils import log

DENY_LIST = [
    "rm -rf /",
    "sudo",
    "shutdown",
    "reboot",
    "mkfs",
    "dd if=",
    "> /dev/sda",
]

DESTRUCTIVE = ["rm ", "> /etc/", "chmod 777", "del ", "erase "]


def check_permission(tool_name: str, args: dict) -> str | None:
    if tool_name == "bash":
        for pattern in DENY_LIST:
            if pattern in args.get("command", ""):
                return log.red(f"Blocked: '{pattern}' is on the deny list")
        for kw in DESTRUCTIVE:
            if kw in args.get("command", ""):
                log.warn("Potentially destructive command")
                log.warn(f"tool: {tool_name}({args})")
                choice = input("   Allow? [y/N] ").strip().lower()
                if choice not in ("y", "yes"):
                    return "Deny"

    if tool_name in ("write_file", "edit_file"):
        path = args.get("path", "")
        if not (WORKDIR / path).resolve().is_relative_to(WORKDIR):
            log.warn("Writing outside workspace")
            log.warn(f"tool: {tool_name}({args})")
            choice = input("   Allow? [y/N] ").strip().lower()
            if choice not in ("y", "yes"):
                return "Denied: paths outside workspace are never allowed."

    return None
