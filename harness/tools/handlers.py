import os
import subprocess

from utils import decode_subprocess_output, log


def run_bash(command: str)->str:
    log.blue(f"run bash > {command}")
    dangerous = ["rm -rf", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command has been blocked!"
    try:
        result = subprocess.run(
        command,
        shell=True,
        cwd=os.getcwd(),
        capture_output=True,
        timeout=120
      )
        out = decode_subprocess_output((result.stdout or b"") +result.stderr or b"")
        return out[:500000] if out else "(empty output)"
    except subprocess.TimeoutExpired:
        return "Error: timeout (120 secs)"
    except (FileNotFoundError, OSError) as e:
        return f"Error: {str(e)}"

TOOL_HANDLERS = {
  "bash": run_bash
}
