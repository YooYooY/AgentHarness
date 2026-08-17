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


BASE_TOOLS = [
    # _fn_tool(
    #     "bash",
    #     "Run a shell command.",
    #     {"command": {"type": "string"}},
    #     ["command"],
    # ),
    _fn_tool(
        "bash",
        "Run a shell command, you can use `run_in_background=true` spawn daemon background threads for parallel work",
        {
            "command": {"type": "string"},
            "run_in_background": {"type": "boolean", "default": False},
        },
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
    # _fn_tool(
    #     "todo_write",
    #     "Create and manage a task list ...",
    #     {
    #         "todos": {
    #             "type": "array",
    #             "items": {
    #                 "type": "object",
    #                 "properties": {
    #                     "content": {"type": "string"},
    #                     "status": {
    #                         "type": "string",
    #                         "enum": ["pending", "in_progress", "completed"],
    #                     },
    #                 },
    #                 "required": ["content", "status"],
    #             },
    #         }
    #     },
    #     ["todos"],
    # ),
    _fn_tool(
        "create_task",
        "create new task, with optional blockedBy dependency",
        {
            "subject": {"type": "string"},
            "description": {"type": "string"},
            "blockedBy": {"type": "array", "items": {"type": "string"}},
        },
        ["subject"],
    ),
    _fn_tool("list_tasks", "list all tasks status, owner and blockedBy", {}, []),
    _fn_tool(
        "get_task",
        "get full task details by task ID",
        {
            "task_id": {"type": "string"},
        },
        ["task_id"],
    ),
    _fn_tool(
        "claim_task",
        "claim the pending task, set the owner, and change the status to in_progress",
        {"task_id": {"type": "string"}},
        ["task_id"],
    ),
    _fn_tool(
        "complete_task",
        "complete tasks with the status->in_progress and report downstream unblocking tasks",
        {"task_id": {"type": "string"}},
        ["task_id"],
    ),
    _fn_tool(
        "schedule_cron",
        "Schedule cron jobs; cron has 5 segments: minute, hour, day, month, week",
        {
            "cron": {"type": "string", "description": "5 segments cron expression"},
            "prompt": {
                "type": "string",
                "description": "Messages to injected upon triggering",
            },
            "recurring": {
                "type": "boolean",
                "description": "True=loop, False=single iteration",
            },
            "durable": {"type": "boolean", "description": "True=Persist to disk"},
        },
        ["cron", "prompt"],
    ),
]

TOOLS = [
    *BASE_TOOLS,
    _fn_tool(
        "spawn_subagent",
        "Launch a subagent to handle a complex subtask. Returns only the final conclusion.",
        {"description": {"type": "string"}},
        ["description"],
    ),
    _fn_tool(
        "load_skill",
        "Load the full content of the skill by name",
        {"name": {"type": "string"}},
        ["name"],
    ),
    _fn_tool(
        "compact",
        "Summarize earlier dialogues to free up context space.",
        {
            "focus": {"type": "string"},
        },
        [],
    ),
    _fn_tool(
        "delete_task",
        "delete completed task",
        {"task_id": {"type": "string"}},
        ["task_id"],
    ),
]
