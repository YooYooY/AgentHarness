import os
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(override=True)

MODEL_ID=os.environ["MODEL_ID"]

client = OpenAI(
  api_key=os.environ["OPENAI_API_KEY"],
  base_url=os.environ["OPENAI_BASE_URL"]
)

DEFAULT_MAX_TOKENS = 8000