from dataclasses import asdict, dataclass
from datetime import datetime
import json
import random
import threading
import time
from config import DURABLE_PATH
from utils import log, read_text, write_text
from cron_utils import cron_matchs, cron_validate


@dataclass
class CronJob:
    id: str
    cron: str
    prompt: str
    recurring: bool
    durable: bool


cron_lock = threading.Lock()
scheduled_jobs: dict[str, CronJob] = {}
cron_queue: list[CronJob] = []
_last_fired: dict[str, str] = {}


def save_durable_jobs():
    durable = [asdict(job) for job in scheduled_jobs.values() if job.durable]
    write_text(DURABLE_PATH, json.dumps(durable, indent=2, ensure_ascii=False))


def schedule_cron(cron: str, prompt: str, recurring: bool, durable: bool):
    err = cron_validate(cron)
    if err:
        return err
    job = CronJob(
        id=f"cron_{random.randint(0, 999999):06d}",
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


def load_durable_jobs():
    if not DURABLE_PATH.exists():
        return
    jobs = json.loads(read_text(DURABLE_PATH))
    for job in jobs:
        job = CronJob(**job)
        err = cron_validate(job.cron)
        if err:
            log.error(f"[⏰ Cron job invalid] {job.id}: {err}")
            continue
        scheduled_jobs[job.id] = job
    valid_jobs = [job for job in jobs if job["id"] in scheduled_jobs]
    if valid_jobs:
        log.info(f"[⏰ Cron job load] loaded {len(valid_jobs)} durable cron tasks")


def cron_scheduler_loop():
    while True:
        time.sleep(1)
        now = datetime.now()
        minute_mark = now.strftime("%Y-%m-%d %H:%M")
        with cron_lock:
            for job in list(scheduled_jobs.values()):
                if cron_matchs(job.cron, now):
                    if _last_fired.get(job.id) != minute_mark:
                        cron_queue.append(job)
                        _last_fired[job.id] = minute_mark
                        # log.info(f"[⏰ Cron trigger] {job.id}->{job.prompt}")
                    if not job.recurring:
                        scheduled_jobs.pop(job.id, None)
                        if job.durable:
                            save_durable_jobs()


def start_cron_scheduler():
    load_durable_jobs()
    threading.Thread(target=cron_scheduler_loop, daemon=True).start()


def has_cron_queue():
    with cron_lock:
        return bool(cron_queue)


def _queue_processor_loop(dispatch_fn, agent_lock):
    while True:
        time.sleep(0.2)

        if not has_cron_queue():
            continue

        if not agent_lock.acquire(blocking=False):
            continue

        try:
            if not has_cron_queue():
                continue
            # log.info(f"[⏰ Cron Queue Processor] Send Cron Task")
            dispatch_fn()
        finally:
            agent_lock.release()


def start_queue_processor(run_agent_run_locked, agent_lock):
    threading.Thread(
        target=_queue_processor_loop,
        args=(run_agent_run_locked, agent_lock),
        daemon=True,
    ).start()
    log.info("⏰ Cron Queue Processor Start")


def consume_cron_queue():
    with cron_lock:
        fired = list(cron_queue)
        cron_queue.clear()
    return fired


def cancel_cron(job_id):
    with cron_lock:
        job = scheduled_jobs.pop(job_id, None)
    if not job:
        return log.error(f"Cron job {job_id} Not Found")
    if job.durable:
        save_durable_jobs()
    return log.info(f"[Cron job cancel] {job_id}")
