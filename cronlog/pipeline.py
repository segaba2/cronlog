"""Pipeline support: chain multiple job runs and track their collective status."""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional

from cronlog.models import JobRun, JobStatus

# pipeline_id -> list of run_ids (ordered)
_pipelines: Dict[str, List[str]] = {}


def create_pipeline(pipeline_id: Optional[str] = None) -> str:
    """Create a new named pipeline and return its ID."""
    pid = pipeline_id or str(uuid.uuid4())
    if pid not in _pipelines:
        _pipelines[pid] = []
    return pid


def add_run_to_pipeline(pipeline_id: str, run: JobRun) -> None:
    """Append a run to an existing pipeline. Creates the pipeline if absent."""
    if pipeline_id not in _pipelines:
        _pipelines[pipeline_id] = []
    if run.run_id not in _pipelines[pipeline_id]:
        _pipelines[pipeline_id].append(run.run_id)
    run.metadata["pipeline_id"] = pipeline_id


def get_pipeline_run_ids(pipeline_id: str) -> List[str]:
    """Return ordered list of run IDs belonging to *pipeline_id*."""
    return list(_pipelines.get(pipeline_id, []))


def get_pipeline_runs(pipeline_id: str, runs: List[JobRun]) -> List[JobRun]:
    """Filter *runs* to those belonging to *pipeline_id*, preserving order."""
    ids = get_pipeline_run_ids(pipeline_id)
    by_id = {r.run_id: r for r in runs}
    return [by_id[rid] for rid in ids if rid in by_id]


def pipeline_status(pipeline_id: str, runs: List[JobRun]) -> JobStatus:
    """Return aggregate status of a pipeline.

    - RUNNING  if any run is still running
    - FAILURE  if any finished run failed (and none are still running)
    - SUCCESS  if all runs finished successfully
    - RUNNING  (fallback) if the pipeline has no runs yet
    """
    members = get_pipeline_runs(pipeline_id, runs)
    if not members:
        return JobStatus.RUNNING
    if any(r.status == JobStatus.RUNNING for r in members):
        return JobStatus.RUNNING
    if any(r.status == JobStatus.FAILURE for r in members):
        return JobStatus.FAILURE
    return JobStatus.SUCCESS


def all_pipeline_ids() -> List[str]:
    """Return all known pipeline IDs."""
    return list(_pipelines.keys())


def unregister_all() -> None:
    """Clear all pipeline state (useful in tests)."""
    _pipelines.clear()
