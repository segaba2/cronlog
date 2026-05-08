"""Scheduled job definitions and next-run time calculation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from croniter import croniter


@dataclass
class ScheduledJob:
    """Represents a cron-style scheduled job definition."""

    name: str
    command: str
    cron_expr: str
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    description: str = ""

    def next_run(self, after: Optional[datetime] = None) -> datetime:
        """Return the next scheduled run time (UTC)."""
        base = after or datetime.now(timezone.utc)
        itr = croniter(self.cron_expr, base)
        return itr.get_next(datetime).replace(tzinfo=timezone.utc)

    def is_due(self, window_seconds: int = 60, now: Optional[datetime] = None) -> bool:
        """Return True if the job is due within *window_seconds* from *now*."""
        now = now or datetime.now(timezone.utc)
        delta = (self.next_run(now) - now).total_seconds()
        return 0 <= delta <= window_seconds

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduledJob":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class ScheduleStore:
    """Persist and retrieve scheduled job definitions from a JSON file."""

    def __init__(self, path: str | Path = "schedules.json"):
        self._path = Path(path)

    def _load_raw(self) -> List[dict]:
        if not self._path.exists():
            return []
        with self._path.open() as fh:
            return json.load(fh)

    def all(self) -> List[ScheduledJob]:
        return [ScheduledJob.from_dict(d) for d in self._load_raw()]

    def save_all(self, jobs: List[ScheduledJob]) -> None:
        with self._path.open("w") as fh:
            json.dump([j.to_dict() for j in jobs], fh, indent=2)

    def add(self, job: ScheduledJob) -> None:
        jobs = self.all()
        if any(j.name == job.name for j in jobs):
            raise ValueError(f"A scheduled job named '{job.name}' already exists.")
        jobs.append(job)
        self.save_all(jobs)

    def remove(self, name: str) -> bool:
        jobs = self.all()
        filtered = [j for j in jobs if j.name != name]
        if len(filtered) == len(jobs):
            return False
        self.save_all(filtered)
        return True

    def get(self, name: str) -> Optional[ScheduledJob]:
        return next((j for j in self.all() if j.name == name), None)
