def _fn_tool(
    name: str, description: str, properties: dict, required: list[str]
) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }

TOOLS = [
    _fn_tool(
        "bash",
        "Execute a shell command",
        {"command": {"type": "string"}},
        ["command"],
    )
]
