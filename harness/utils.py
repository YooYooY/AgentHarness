from pathlib import Path
from rich.console import Console
from config import TEXT_ENCODING, WORKDIR


def read_text(path, encoding=TEXT_ENCODING, errors="replace"):
    return Path(path).read_text(encoding=encoding, errors=errors)

def write_text(path, content, encoding=TEXT_ENCODING):
    return Path(path).write_text(content, encoding=encoding)

def open_text(path, mode="w", encoding=TEXT_ENCODING):
    return Path(path).open(mode, encoding=encoding)

def assistant_message_dict(message) -> dict:
    data = message.model_dump(exclude_none=True)
    data["role"] = "assistant"
    return data


def decode_subprocess_output(data: bytes | None) -> str:
    if not data:
        return ""
    for encoding in ("utf-8", "gbk", "cp936"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(log.error(f"Beyond the workplace: {p}"))
    return path


def extract_text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    return str(content)


console = Console()


class Logger:
    _STYLES = {
        "info": "yellow",
        "error": "bold red",
        "warn": "cyan",
        "red": "red",
        "green": "green",
        "yellow": "yellow",
        "blue": "blue",
        "magenta": "magenta",
        "cyan": "cyan",
    }

    def __init__(self, output: Console | None = None) -> None:
        self.console = output or console

    def _print(self, level: str, *values: object, **kwargs) -> str:
        separator = kwargs.pop("sep", " ") or " "
        message = separator.join(str(value) for value in values)
        kwargs.setdefault("style", self._STYLES[level])
        kwargs.setdefault("markup", False)
        kwargs.setdefault("highlight", False)
        self.console.print(message, **kwargs)
        return message

    def info(self, *values: object, **kwargs) -> str:
        return self._print("info", *values, **kwargs)

    def error(self, *values: object, **kwargs) -> str:
        return self._print("error", *values, **kwargs)

    def warn(self, *values: object, **kwargs) -> str:
        return self._print("warn", *values, **kwargs)

    def red(self, *values: object, **kwargs) -> str:
        return self._print("red", *values, **kwargs)

    def green(self, *values: object, **kwargs) -> str:
        return self._print("green", *values, **kwargs)

    def yellow(self, *values: object, **kwargs) -> str:
        return self._print("yellow", *values, **kwargs)

    def blue(self, *values: object, **kwargs) -> str:
        return self._print("blue", *values, **kwargs)

    def magenta(self, *values: object, **kwargs) -> str:
        return self._print("magenta", *values, **kwargs)

    def cyan(self, *values: object, **kwargs) -> str:
        return self._print("cyan", *values, **kwargs)


log = Logger()


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, parts[2].strip()


def message_text(msg: dict):
    content = msg.get("content", "")
    if isinstance(content, str):
        return content.strip()
    return str(content).strip()


def llm_text(response):
    return (response.choices[0].message.content or "").strip()
