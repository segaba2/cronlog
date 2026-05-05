"""Simple JSON-based storage for JobRun records."""

import json
import os
from pathlib import Path
from typing import List, Optional

from cronlog.models import JobRun

DEFAULT_LOG_DIR = Path.home() / ".cronlog"


class JobRunStorage:
    """Persists and retrieves JobRun records as newline-delimited JSON."""

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "runs.jsonl"

    def save(self, run: JobRun) -> None:
        """Append a JobRun record to the log file."""
        with self.log_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(run.to_dict()) + "\n")

    def load_all(self) -> List[JobRun]:
        """Load all JobRun records from the log file."""
        if not self.log_file.exists():
            return []
        runs: List[JobRun] = []
        with self.log_file.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    runs.append(JobRun.from_dict(json.loads(line)))
        return runs

    def find_by_job_name(self, job_name: str) -> List[JobRun]:
        """Return all runs matching the given job name."""
        return [r for r in self.load_all() if r.job_name == job_name]

    def find_by_run_id(self, run_id: str) -> Optional[JobRun]:
        """Return the run with the given ID, or None if not found."""
        for run in self.load_all():
            if run.run_id == run_id:
                return run
        return None

    def clear(self) -> None:
        """Delete all stored records."""
        if self.log_file.exists():
            self.log_file.unlink()
