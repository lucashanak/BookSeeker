"""Simple job tracking for downloads."""
import json
import time
import uuid
from pathlib import Path

from app.config import DATA_DIR

JOBS_FILE = Path(DATA_DIR) / "jobs.json"
MAX_JOBS = 100


def _load_jobs() -> list[dict]:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    if JOBS_FILE.exists():
        try:
            return json.loads(JOBS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return []


def _save_jobs(jobs: list[dict]):
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    JOBS_FILE.write_text(json.dumps(jobs[-MAX_JOBS:], indent=2))


def create_job(title: str, indexer: str, size: int, username: str) -> dict:
    job = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "indexer": indexer,
        "size": size,
        "username": username,
        "status": "downloading",
        "created_at": time.time(),
        "error": "",
    }
    jobs = _load_jobs()
    jobs.append(job)
    _save_jobs(jobs)
    return job


def update_job(job_id: str, **kwargs):
    jobs = _load_jobs()
    for job in jobs:
        if job["id"] == job_id:
            job.update(kwargs)
            break
    _save_jobs(jobs)


def get_jobs(username: str | None = None) -> list[dict]:
    jobs = _load_jobs()
    if username:
        jobs = [j for j in jobs if j.get("username") == username]
    return sorted(jobs, key=lambda j: j.get("created_at", 0), reverse=True)
