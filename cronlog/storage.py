"""Persistent storage for JobRun records using newline-delimited JSON."""

import json
import os
from pathlib import Path
from typing import List, Optional

from cronlog.models import JobRun


DEFAULT_LOG_PATH = Path(os.environ.get("CRONLOG_PATH", "~/.cronlog/runs.jsonl"))


class JobRunStorage:
    def __init__(self, path: Path = DEFAULT_LOG_PATH) -> None:
        self.path = Path(path).expanduser()

    def _ensure_dir(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, run: JobRun) -> None:
        self._ensure_dir()
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(run.to_dict()) + "\n")

    def load_all(self) -> List[JobRun]:
        if not self.path.exists():
            return []
        runs = []
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    runs.append(JobRun.from_dict(json.loads(line)))
        return runs

    def save_all(self, runs: List[JobRun]) -> None:
        """Overwrite storage with the given list of runs."""
        self._ensure_dir()
        with self.path.open("w", encoding="utf-8") as fh:
            for run in runs:
                fh.write(json.dumps(run.to_dict()) + "\n")

    def find_by_job_name(self, job_name: str) -> List[JobRun]:
        return [r for r in self.load_all() if r.job_name == job_name]

    def find_by_run_id(self, run_id: str) -> Optional[JobRun]:
        for run in self.load_all():
            if run.run_id == run_id:
                return run
        return None

    def delete_by_run_id(self, run_id: str) -> bool:
        runs = self.load_all()
        new_runs = [r for r in runs if r.run_id != run_id]
        if len(new_runs) == len(runs):
            return False
        self.save_all(new_runs)
        return True
