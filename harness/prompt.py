from config import WORKDIR
from skills import SKILL_REGISTRY


PROMPT_SECTIONS = {
    "identity": (
        "You are a programming agent. Act directly and modify files when needed. "
        "For multi-step tasks, use todo_write to create a plan before execution "
        "and update the task status as you make progress. "
        "When a task contains a complex independent subtask, use spawn_subagent "
        "to delegate that subtask. "
        "All destructive actions require user approval. "
        "If a file tool rejects your request, do not bypass it using other methods "
        "such as bash, Python, or Node.js."
        "When the context is too long, you can use the compact tool."
    ),
    "workspace": f"workspace: {WORKDIR}",
    "skill": "Use load_skill to get full details when needed.",
}

SUB_SYSTEM = (
    f"You are a subagent working in the {WORKDIR} directory. "
    f"Complete only the assigned task. "
    f"Act directly using available tools and return a concise summary when finished. "
    f"Do not delegate tasks to other agents."
)


def _assemble_system_prompt(skills: str) -> str:
    sections = [PROMPT_SECTIONS["identity"], PROMPT_SECTIONS["workspace"]]
    if skills:
        sections.append(f"Skills available:\n{skills}\n")
        sections.append(PROMPT_SECTIONS["skill"])
    return "\n\n".join(sections)


def _skills_text():
    if not SKILL_REGISTRY:
        return ""
    return "\n".join(
        f"- ** {skill.get("name", "")} **:{skill.get("description", "")}"
        for skill in SKILL_REGISTRY.values()
    )


def get_system_prompt() -> str:
    return _assemble_system_prompt(_skills_text())
