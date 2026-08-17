from dataclasses import asdict, dataclass
import json
import random
import threading
from harness.config import DURABLE_PATH
from utils import log, write_text


@dataclass
class CronJob:
    id: str
    cron: str
    prompt: str
    recurring: bool
    durable: bool


cron_lock = threading.Lock()
scheduled_jobs: dict[str, CronJob] = {}


def _validate_cron_field(field: str, low: int, high: int):
    if field == "*":
        return None
    if field.startswith("*/"):
        step_str = field[2:]
        if not step_str.isdigit():
            return f"Invalid step size:{field}"
        if int(step_str) <= 0:
            return f"Step size must be greater than 0:{field}"
        return None
    if "," in field:  # 1,5,8
        for part in field.split(","):
            err = _validate_cron_field(part.strip(), low, high)
            if err:
                return err
        return None
    if "-" in field:  # 1-5
        parts = field.split("-", 1)
        if not parts[0].isdigit() or not parts[1].isdigit():
            return f"Invalid range:{field}"
        a, b = int(parts[0]), int(parts[1])
        if a < low or a > high or b < low or b > high:
            return f"range {field} excessive {low}-{high}"
        if a > b:
            return f"The starting value of the range must be less than the ending value:{field}"
    if not field.isdigit():
        return f"Invalid filed:{field}"
    val = int(field)
    if val < low or val > high:
        return f"value: {val} excessive {low}-{high}"
    return None


def validate_cron(cron_expr: str):
    fileds = cron_expr.strip().split()
    if len(fileds) != 5:
        return f"cron require 5 fileds, currently passes {len(fileds)} "
    bounds = [
        (0, 59),
        (0, 23),
        (1, 31),
        (1, 12),
        (0, 6),
    ]
    names = ["minute", "hour", "day", "month", "week"]
    for field, (low, high), name in zip(fileds, bounds, names):
        err = _validate_cron_field(field, low, high)
        if err:
            return f"{name}: {err}"
    return None


def save_durable_jobs():
    durable = [asdict(job) for job in scheduled_jobs.values() if job.durable]
    write_text(DURABLE_PATH, json.dumps(durable, indent=2, ensure_ascii=False))


def schedule_cron(cron: str, prompt: str, recurring: bool, durable: bool):
    err = validate_cron(cron)
    if err:
        return err
    job = CronJob(
        id=f"cron_{random.randint(0, 0,999999):06d}",
        cron=cron,
        prompt=prompt,
        recurring=recurring,
        durable=durable,
    )

    with cron_lock:
        scheduled_jobs[job.id] = job
    if durable:
        save_durable_jobs()
    log.yellow(f"[⏰ Register schedule task cron] {job.id} {cron} -> {prompt}")
    return job
