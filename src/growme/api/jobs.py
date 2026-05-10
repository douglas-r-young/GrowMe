"""Small in-process background job runner for local GrowMe demos."""

from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Literal

from growme.api import store

JobStatus = Literal["queued", "running", "complete", "error"]


@dataclass
class Job:
    id: str
    kind: str
    session_id: str
    status: JobStatus = "queued"
    messages: list[str] = field(default_factory=list)
    error: str | None = None

    def log(self, message: str) -> None:
        self.messages.append(message)
        _persist(self)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _persist(job: Job) -> None:
    """Snapshot a job's state onto its session pickle so a server restart
    leaves the UI with a recoverable state instead of polling a missing job."""
    snapshot = {
        "id": job.id,
        "kind": job.kind,
        "status": job.status,
        "error": job.error,
        "messages": list(job.messages),
        "updated_at": _now_iso(),
    }
    try:
        store.update(job.session_id, "last_job", snapshot)
    except Exception:
        # Don't let persistence problems crash the actual pipeline.
        pass


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=3)

    def create(
        self,
        *,
        kind: str,
        session_id: str,
        target: Callable[[Job], None],
    ) -> Job:
        job = Job(id=str(uuid.uuid4()), kind=kind, session_id=session_id)
        with self._lock:
            self._jobs[job.id] = job
        _persist(job)
        self._executor.submit(self._run, job.id, target)
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _run(self, job_id: str, target: Callable[[Job], None]) -> None:
        job = self.get(job_id)
        if job is None:
            return
        job.status = "running"
        _persist(job)
        try:
            target(job)
        except Exception as exc:
            job.error = str(exc)
            job.status = "error"
            _persist(job)
            return
        job.status = "complete"
        _persist(job)


jobs = JobManager()
