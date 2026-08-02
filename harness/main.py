from agent import agent_loop


def main():
  print("Enter your question and press Enter to send, Type 'q' to exit \n")
  history = []
  while True:
    try:
      query = input("\x1b[36m] \x1b[0m")
    except (EOFError, KeyboardInterrupt):
      break
    if query.strip().lower() in ("q", "exit", ""):
      break
    history.append({"role": "user", "content": query})
    agent_loop(history)
    final = history[-1]
    if final.get("role") == "assistant" and final.get("content"):
      print(final["content"])
      
if __name__ == "__main__":
  main()