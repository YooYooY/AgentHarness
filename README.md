A lightweight Claude Code inspired agent runtime.

Implemented:

- Agent execution loop
- Tool calling system
- Context management
- Memory architecture
- Planning and reflection
- Multi-step task execution
- Evaluation framework

### Simply Agent Loop

verify:

```
cd project
uv run  ../harness/main.py
```

Try these prompts:

- Create a file named hello.py with the content "Hello, World!"
- List all Python files in the current directory
- What is the current git branch?

### Tool Use

Add a Tool, Add Just One Line

The loop stays stable while capabilities register into a dispatch table.

```
const handlers = { bash, read_file, write_file, edit_file, }{};
```

Try these prompts:

- Read the README.md file and tell me what this project does.
- Create a file named test.py that prints "hello", then read that file.
- Find all Python files in the current directory.
- Read both README.md and pyproject.toml, then generate a summary file.

### Permission

Check Permissions Before Execution

Try these prompts:

Create a file named test.txt in the current directory (should pass directly)

Delete all temporary files in the tmp directory (bash + rm will trigger gate)

What files are in the current directory? (Read-only, all will pass)

Use the write_file tool to write an empty text file named hello.txt to the Desktop directory (write outside the working directory, triggering gate)

### Hooks

Cross-cutting behavior belongs around the loop, not tangled inside it.

Try these prompts:

- Read the file `README.md` (should pass directly, observe the hook logs)
- Create a file named test.txt (after passing, observe if PostToolUse is triggered)
- Delete all files in the tmp directory (bash + rm will trigger a permission hook)

### TodoWrite

Explicit plans keep long-running work visible and correctable.

Try these prompts:

- Refactor `example/hello.py`: Add type annotations, docstrings, and main protection (list the 3 steps first, then execute)
- Create a Python package under `example/demo_pkg` containing `__init__.py`, `utils.py`, and `tests/test_utils.py`
- Inspect all Python files under example and fix any code style issues.

### Subagent

Break Large Tasks into Small Ones with Clean Context

> Subagents give each subtask a clean message history while preserving the main thread.

Try these prompts:

- Use subtasks to find which third-party modules are installed in this project (the sub-Agent reads the files, the main Agent only receives the conclusions).
- Use the `spawn_subagent` tool to read all `.py` files in the `agents/` directory and summarize the function of each file.
- Use the `spawn_subagent` tool to create `example/string_tools.py` containing the `slugify(text: str)` function, and then have the main Agent verify this file.

### Skills

Load Only When Needed

> Inject specialized knowledge only when the task actually needs it.

Try these prompts:

- What skills are available?
- Load the code-review skill and follow its instructions
- I need to do a code review -- load the relevant skill first

### Context Compact

Context Will Fill Up

> compression keeps the conversation usable when the context window gets crowded.

Try these prompts:

- Read the food.md file in the current directory and summarize its contents for me.

### Memory

Keep a Layer That Doesn't Lose Details

> Some facts should survive summarization and future sessions

Try these prompts:

- I prefer using tabs for indentation over spaces. Please keep this in mind.
- Create a Python file named test.py (observe if the Agent uses tabs).
- Did I tell you about my preferences before? (Observe if the Agent remembers).
- I also prefer strings enclosed in single quotes instead of double quotes.

### System Prompt

Assembled at Runtime, Never Hardcoded

> The system prompt is a generated product of policy, tools, skills, and context.

Try these prompts:

- Read the file README.md (and observe the three sections that are always loaded).

### Error Recovery

Errors Are the Start of a Retry

> A robust harness classifies failures and decides what kind of retry is worthwhile.

Try these prompts:

- Have the Agent generate a very long piece of code and observe whether it automatically resumes writing after truncation (see the `[max_tokens] escalating` log).
- Continuously read a large number of files to expand the context and observe reactive compaction.
- If you encounter 429/529 errors, observe the log output for exponential backoff.

### Task System

Break Big Goals into Small Tasks

> A task graph turns vague goals into ordered, observable work.

Try these prompts:

- Create tasks: setup database schema, create API endpoints (depends on schema), write tests (depends on endpoints), write docs (depends on schema)
- List all tasks and their statuses
- Claim the first unblocked task and complete it
- List tasks again — which ones are now unblocked?

### Background Tasks

Slow Operations Go to the Background

> The agent can keep reasoning while slow work completes elsewhere.

Try these prompts:

- Run pip list in the background and find all Python files in this directory
- Run npm install (use run_in_background) and while waiting, read package.json
- Create a task to setup the project, then run pip list in the background
