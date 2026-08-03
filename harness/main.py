from agent import agent_loop
from utils import log


def main():
    log.yellow("Enter your question and press Enter to send, Type 'q' to exit\n")
    history = []
    while True:
        try:
            query = input("\x1b[36m] \x1b[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "quit", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
        final = history[-1]
        if final.get("role") == "assistant" and final.get("content"):
            log.green(f"🤖: {final['content']}")


if __name__ == "__main__":
    main()
