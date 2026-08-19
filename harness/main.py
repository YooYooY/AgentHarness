import threading
from agent import agent_loop
from cron import start_cron_scheduler, start_queue_processor
from hooks import trigger_user_prompt_hooks
from utils import log
from prompt_toolkit import prompt

agent_lock = threading.Lock()


history = []

def run_agent_turn_locked(query: str | None = None):
    if query:
        history.append({"role": "user", "content": query})
    agent_loop(history)
    final = history[-1]
    if final.get("role") == "assistant" and final.get("content"):
        log.green(f"🤖: {final['content']}")


def main():

    start_cron_scheduler()
    start_queue_processor(run_agent_turn_locked, agent_lock)

    log.yellow("Enter your question and press Enter to send, Type 'q' to exit\n")

    while True:
        try:
            query = prompt("You: ")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("quit", "exit"):
            break
        query = trigger_user_prompt_hooks(query)
        with agent_lock:
            run_agent_turn_locked(query)


if __name__ == "__main__":
    main()
