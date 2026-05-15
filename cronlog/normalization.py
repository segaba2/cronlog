"""Normalize job run fields for consistent comparison and storage."""

from __future__ import annotations

import re
from typing import List

from cronlog.models import JobRun


def normalize_job_name(name: str) -> str:
    """Lowercase, strip whitespace, collapse internal spaces to underscores."""
    if not name or not name.strip():
        return ""
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_\-\.]", "", name)
    return name


def normalize_output(text: str | None) -> str:
    """Strip trailing whitespace from each line and trailing blank lines."""
    if not text:
        return ""
    lines = text.splitlines()
    lines = [line.rstrip() for line in lines]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def normalize_run(run: JobRun) -> JobRun:
    """Return a copy of *run* with normalized job_name and output fields."""
    run.job_name = normalize_job_name(run.job_name)
    if hasattr(run, "stdout") and run.stdout is not None:
        run.stdout = normalize_output(run.stdout)
    if hasattr(run, "stderr") and run.stderr is not None:
        run.stderr = normalize_output(run.stderr)
    return run


def normalize_runs(runs: List[JobRun]) -> List[JobRun]:
    """Normalize every run in *runs* in-place and return the list."""
    for run in runs:
        normalize_run(run)
    return runs


def is_valid_job_name(name: str) -> bool:
    """Return True if *name* is a non-empty, already-normalized job name."""
    if not name:
        return False
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9_\-\.]*", name))
