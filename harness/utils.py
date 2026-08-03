class Logger:
    _RESET = "\033[0m"
    _COLORS = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
    }

    def _print(self, color: str, *values, **kwargs) -> None:
        separator = kwargs.pop("sep", " ")
        if separator is None:
            separator = " "
        message = separator.join(str(value) for value in values)
        print(f"{self._COLORS[color]}{message}{self._RESET}", **kwargs)

    def red(self, *values, **kwargs) -> None:
        self._print("red", *values, **kwargs)

    def green(self, *values, **kwargs) -> None:
        self._print("green", *values, **kwargs)

    def yellow(self, *values, **kwargs) -> None:
        self._print("yellow", *values, **kwargs)

    def blue(self, *values, **kwargs) -> None:
        self._print("blue", *values, **kwargs)

    def magenta(self, *values, **kwargs) -> None:
        self._print("magenta", *values, **kwargs)

    def cyan(self, *values, **kwargs) -> None:
        self._print("cyan", *values, **kwargs)


log = Logger()


def assistant_message_dict(message)->dict:
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
