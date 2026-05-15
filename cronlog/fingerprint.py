"""Fingerprinting module: generate and compare stable identity hashes for job runs."""

from __future__ import annotations

import hashlib
import json
from typing import List, Optional

from cronlog.models import JobRun


def _stable_fields(run: JobRun) -> dict:
    """Extract the fields used to compute a run's fingerprint."""
    return {
        "job_name": run.job_name,
        "exit_code": run.exit_code,
        "stdout": (run.stdout or "").strip(),
        "stderr": (run.stderr or "").strip(),
    }


def compute_fingerprint(run: JobRun) -> str:
    """Return a stable SHA-256 hex digest for the given run.

    The fingerprint is derived from the job name, exit code, stdout, and
    stderr so that two runs producing identical output are considered
    equivalent regardless of when they ran.
    """
    payload = json.dumps(_stable_fields(run), sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def fingerprints_match(a: JobRun, b: JobRun) -> bool:
    """Return True when two runs share the same fingerprint."""
    return compute_fingerprint(a) == compute_fingerprint(b)


def group_by_fingerprint(runs: List[JobRun]) -> dict:
    """Group runs by their fingerprint.

    Returns a mapping of fingerprint -> list[JobRun].
    """
    groups: dict = {}
    for run in runs:
        fp = compute_fingerprint(run)
        groups.setdefault(fp, []).append(run)
    return groups


def find_matching_runs(target: JobRun, runs: List[JobRun]) -> List[JobRun]:
    """Return all runs from *runs* whose fingerprint matches *target*."""
    target_fp = compute_fingerprint(target)
    return [r for r in runs if compute_fingerprint(r) == target_fp]


def unique_fingerprints(runs: List[JobRun]) -> List[str]:
    """Return the sorted list of distinct fingerprints across *runs*."""
    return sorted({compute_fingerprint(r) for r in runs})
