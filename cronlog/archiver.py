"""Archive completed job runs to a compressed file for long-term storage."""

from __future__ import annotations

import gzip
import json
import os
from datetime import datetime, timezone
from typing import List

from cronlog.models import JobRun


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _archive_path(log_dir: str, label: str | None = None) -> str:
    """Return the path for an archive file."""
    if label is None:
        label = _utcnow().strftime("%Y%m%dT%H%M%S")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f"archive_{label}.jsonl.gz")


def archive_runs(runs: List[JobRun], log_dir: str, label: str | None = None) -> str:
    """Compress and write *runs* to a gzipped JSONL archive file.

    Returns the path of the created archive.
    """
    path = _archive_path(log_dir, label)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for run in runs:
            fh.write(json.dumps(run.to_dict()) + "\n")
    return path


def load_archive(path: str) -> List[JobRun]:
    """Load job runs previously written by :func:`archive_runs`."""
    runs: List[JobRun] = []
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            runs.append(JobRun.from_dict(data))
    return runs


def list_archives(log_dir: str) -> List[str]:
    """Return sorted list of archive file paths found in *log_dir*."""
    if not os.path.isdir(log_dir):
        return []
    return sorted(
        os.path.join(log_dir, f)
        for f in os.listdir(log_dir)
        if f.startswith("archive_") and f.endswith(".jsonl.gz")
    )
