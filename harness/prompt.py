PROMPT_SECTIONS = {
  "identity": (
    f"You are a programming agent; act directly, do not explain"
  )
}

def get_system_prompt()->str:
  return PROMPT_SECTIONS["identity"]