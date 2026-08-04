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
        "Run a shell command.",
        {"command": {"type": "string"}},
        ["command"],
    ),
    _fn_tool(
        "read_file",
        "Read file contents.",
        {"path": {"type": "string"}, "limit": {"type": "integer"}},
        ["path"],
    ),
    _fn_tool(
        "write_file",
        "Write content to file.",
        {"path": {"type": "string"}, "content": {"type": "string"}},
        ["path", "content"],
    ),
    _fn_tool(
        "edit_file",
        "Replace text in file once.",
        {
            "path": {"type": "string"},
            "old_text": {"type": "string"},
            "new_text": {"type": "string"},
        },
        ["path", "old_text", "new_text"],
    ),
    _fn_tool(
        "glob",
        "Find files by pattern.",
        {"pattern": {"type": "string"}},
        ["pattern"],
    ),
]
