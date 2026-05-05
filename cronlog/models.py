"""Data models for cronlog structured metadata."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class JobStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"
    TIMEOUT = "timeout"


@dataclass
class JobRun:
    """Represents a single execution of a cron job."""

    job_name: str
    command: str
    started_at: datetime
    status: JobStatus = JobStatus.RUNNING
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    finished_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: Optional[float] = None
    tags: dict = field(default_factory=dict)

    def finish(self, exit_code: int, stdout: str = "", stderr: str = "") -> None:
        """Mark the job run as finished and compute duration."""
        self.finished_at = datetime.utcnow()
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration_seconds = (
            self.finished_at - self.started_at
        ).total_seconds()
        self.status = JobStatus.SUCCESS if exit_code == 0 else JobStatus.FAILURE

    def to_dict(self) -> dict:
        """Serialize the job run to a plain dictionary."""
        return {
            "run_id": self.run_id,
            "job_name": self.job_name,
            "command": self.command,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "JobRun":
        """Deserialize a job run from a plain dictionary."""
        run = cls(
            run_id=data["run_id"],
            job_name=data["job_name"],
            command=data["command"],
            started_at=datetime.fromisoformat(data["started_at"]),
            status=JobStatus(data["status"]),
            exit_code=data.get("exit_code"),
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", ""),
            duration_seconds=data.get("duration_seconds"),
            tags=data.get("tags", {}),
        )
        if data.get("finished_at"):
            run.finished_at = datetime.fromisoformat(data["finished_at"])
        return run
