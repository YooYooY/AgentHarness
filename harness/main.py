from agent import agent_loop
from hooks import trigger_user_prompt_hooks
from utils import log
from prompt_toolkit import prompt


def main():
    log.yellow("Enter your question and press Enter to send, Type 'q' to exit\n")
    history = []
    while True:
        try:
            query = prompt("You: ")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("quit", "exit"):
            break
        query = trigger_user_prompt_hooks(query)
        history.append({"role": "user", "content": query})
        agent_loop(history)
        final = history[-1]
        if final.get("role") == "assistant" and final.get("content"):
            log.green(f"🤖: {final['content']}")


if __name__ == "__main__":
    main()
