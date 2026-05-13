"""Correlation utilities for linking related job runs together."""

from __future__ import annotations

from typing import Dict, List, Optional

from cronlog.models import JobRun

# correlation_id -> list of run_ids
_correlation_map: Dict[str, List[str]] = {}


def link_runs(correlation_id: str, *runs: JobRun) -> None:
    """Associate one or more runs under a shared correlation ID."""
    if not correlation_id:
        raise ValueError("correlation_id must not be empty")
    correlation_id = correlation_id.strip().lower()
    bucket = _correlation_map.setdefault(correlation_id, [])
    for run in runs:
        if run.run_id not in bucket:
            bucket.append(run.run_id)
            run.metadata["correlation_id"] = correlation_id


def get_correlated_ids(correlation_id: str) -> List[str]:
    """Return all run IDs linked to the given correlation ID."""
    return list(_correlation_map.get(correlation_id.strip().lower(), []))


def find_correlated_runs(correlation_id: str, runs: List[JobRun]) -> List[JobRun]:
    """Filter a list of runs to those linked under the given correlation ID."""
    linked_ids = set(get_correlated_ids(correlation_id))
    return [r for r in runs if r.run_id in linked_ids]


def get_correlation_id(run: JobRun) -> Optional[str]:
    """Return the correlation ID recorded on a run, if any."""
    return run.metadata.get("correlation_id")


def all_correlation_ids() -> List[str]:
    """Return all known correlation IDs."""
    return list(_correlation_map.keys())


def unregister_all() -> None:
    """Clear all correlation state (useful for testing)."""
    _correlation_map.clear()
