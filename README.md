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

