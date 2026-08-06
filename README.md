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
