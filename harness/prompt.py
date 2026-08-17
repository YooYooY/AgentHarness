from config import MEMORY_INDEX, TEXT_ENCODING, WORKDIR
from skills import SKILL_REGISTRY
from utils import log, read_text


PROMPT_SECTIONS = {
    "identity": (
        "You are a programming agent. Act directly and modify files when needed. "
        # "For multi-step tasks, use todo_write to create a plan before execution "
        "and update the task status as you make progress. "
        "When a task contains a complex independent subtask, use spawn_subagent "
        "to delegate that subtask. "
        "All destructive actions require user approval. "
        "If a file tool rejects your request, do not bypass it using other methods "
        "such as bash, Python, or Node.js."
        "When the context is too long, you can use the compact tool."
        "Bash supports the `run_in_background` parameter to run time-consuming commands in the background"
        "Scheduled tasks can be performed using schedule_cron/list_crons/cancel-cron"
    ),
    "workspace": f"workspace: {WORKDIR}",
    "skill": "Use load_skill to get full details when needed.",
    "memory": (
        "The relevant memory text will be injected below."
        "Please adhere to the user preferences in the memory."
        "When user says remember or expresses a clear preference, it should be extracted as a memory"
    ),
}

SUB_SYSTEM = (
    f"You are a subagent working in the {WORKDIR} directory. "
    f"Complete only the assigned task. "
    f"Act directly using available tools and return a concise summary when finished. "
    f"Do not delegate tasks to other agents."
)


def _assemble_system_prompt(skills: str, memories: str) -> str:
    sections = [PROMPT_SECTIONS["identity"], PROMPT_SECTIONS["workspace"]]
    if skills:
        sections.append(f"Skills available:\n{skills}")
        sections.append(PROMPT_SECTIONS["skill"])
    if memories:
        sections.append(PROMPT_SECTIONS["memory"])
        sections.append(f"Relevant memories:\n{memories}")
    return "\n\n".join(sections)


def _skills_text():
    if not SKILL_REGISTRY:
        return ""
    return "\n".join(
        f"- ** {skill.get("name", "")} **:{skill.get("description", "")}"
        for skill in SKILL_REGISTRY.values()
    )


def _memory_index_text():
    if not MEMORY_INDEX.exists():
        return ""
    return read_text(MEMORY_INDEX).strip()


_last_prompt = None
_last_memory_mtime = None


def get_system_prompt() -> str:
    global _last_prompt, _last_memory_mtime

    mtime = MEMORY_INDEX.stat().st_mtime if MEMORY_INDEX.exists() else 0
    if _last_prompt is not None and mtime == _last_memory_mtime:
        log.info("[🎯 Cache Hit] System prompt remains unchanged")
        return _last_prompt
    _last_memory_mtime = mtime
    _last_prompt = _assemble_system_prompt(_skills_text(), _memory_index_text())
    return _last_prompt
