import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(override=True)

MODEL_ID = os.environ["MODEL_ID"]

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_BASE_URL"]
)

DEFAULT_MAX_TOKENS = 8000

WORKDIR = Path.cwd()

TEXT_ENCODING = "utf-8"

SKILLS_DIR = WORKDIR / "skills"

MAX_BYTES = 10000

PERSIST_THRESHOLD = 1000

TOOL_RESULT_DIR = WORKDIR / ".task_outputs" / "tool_results"

MAX_MESSAGE_LENGTH = 50

KEEP_RECENT = 5

CONTEXT_LIMIT = 100000

# History Context Compact
TRANSCRIPTS_DIR = WORKDIR / ".transcripts"

# Memory
MEMORY_DIR = WORKDIR / ".memory"

MEMORY_DIR.mkdir(exist_ok=True)

MEMORY_INDEX = MEMORY_DIR / "MEMORY.md"

CONSOLIDATE_THRESHOLD = 10

# TodoWrite
TODO_REMINDER_ROUNDS = 5

# Error Recovery
MAX_RETRIES = 10

MAX_RECOVERY_RETRIES = 3

ESCALATE_MAX_TOKENS = 64000

FALLBACK_MODEL_ID = os.environ["FALLBACK_MODEL_ID"]

BASE_DELAY_MS = 500

# dedine how many times consecutively the event occurs 529 befor switching to the backup model
MAX_CONSECUTIVE_529 = 3

CONTINUATION_PROMPT = """
Output token limit hit. Resume directly-
no apology, no recap. Pick up mid-thought.
"""

# Task System
TASKS_DIR = WORKDIR / ".tasks"
TASKS_DIR.mkdir(exist_ok=True)
