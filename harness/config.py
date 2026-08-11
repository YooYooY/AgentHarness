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

KEEP_RECENT = 3

CONTEXT_LIMIT = 100000

TRANSCRIPTS_DIR = WORKDIR / ".transcripts"

MEMORY_DIR = WORKDIR / ".memory"

MEMORY_DIR.mkdir(exist_ok=True)

MEMORY_INDEX = MEMORY_DIR / "MEMORY.md"

CONSOLIDATE_THRESHOLD = 10
