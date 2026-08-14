from dataclasses import asdict, dataclass
import json
import random
import time
from typing import Literal

from config import TASKS_DIR
from utils import read_text, write_text, log


@dataclass
class Task:
    id: str
    subject: str
    description: str
    status: Literal["pending", "in_progress", "completed"]
    owner: str | None
    blockedBy: list[str]


def _task_path(task_id: str):
    return TASKS_DIR / f"{task_id}.json"


def jsondumps_task(task: Task):
    return json.dumps(asdict(task), indent=2, ensure_ascii=False)


def save_task(task: Task):
    write_text(_task_path(task.id), jsondumps_task(task))


def create_task(subject: str, description: str, blockedBy: list[str] | None = None):
    task = Task(
        id=f"task_{int(time.time())}_{random.randint(0, 9999):04d}",
        subject=subject,
        description=description,
        status="pending",
        owner=None,
        blockedBy=blockedBy or [],
    )
    save_task(task)
    return task


def list_tasks():
    return [
        Task(**json.loads(read_text(p))) for p in sorted(TASKS_DIR.glob("task_*.json"))
    ]


def load_task(task_id: str):
    return Task(**json.loads(read_text(_task_path(task_id))))


def get_task(task_id: str):
    return jsondumps_task(load_task(task_id))


def can_start(task_id: str) -> bool:
    task = load_task(task_id)
    for dep_id in task.blockedBy:
        if not _task_path(dep_id).exists():
            return False
        if load_task(dep_id).status != "completed":
            return False
    return True


def claim_task(task_id, owner: str = "agent"):
    task = load_task(task_id)
    if task.status != "pending":
        return f"task {task_id} in {task.status} status, claim fail"
    if not can_start(task_id):
        deps = [
            d
            for d in task.blockedBy
            if not _task_path(d).exists() or load_task(d).status != "completed"
        ]
        return f"can't claim task, task blockedby: {deps}"
    task.owner = owner
    task.status = "in_progress"
    save_task(task)
    log.info(f"[🙋‍♂️ Claim Task] {task.subject}-> in_progress(owner: {owner})")
    return f"claim task {task.id} {task.subject} succeed!"


def complete_task(task_id):
    task = load_task(task_id)
    if task.status != "in_progress":
        return f"task {task_id} in {task.status} status, complete fail"
    task.status = "completed"
    save_task(task)
    unblocked = [
        t.subject
        for t in list_tasks()
        if t.status == "pending" and t.blockedBy and can_start(t.id)
    ]
    log.info(f"[🎊 complete] {task.subject}")
    msg = f"complete {task_id} {task.subject}"
    if unblocked:
        msg += f"\n unblocked: {','.join(unblocked)}"
        print(f"\n unblocked: {','.join(unblocked)}")
    return msg
