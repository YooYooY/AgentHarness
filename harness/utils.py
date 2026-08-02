def assistant_message_dict(message)->dict:
  data = message.model_dump(exclude_none=True)
  data["role"] = "assistant"
  return data