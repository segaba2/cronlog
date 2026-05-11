"""Replay module: re-execute a previous job run by its run_id."""

from __future__ import annotations

from typing import Optional

from cronlog.models import JobRun
from cronlog.runner import run_job
from cronlog.storage import JobRunStorage


def find_run(storage: JobRunStorage, run_id: str) -> Optional[JobRun]:
    """Return the JobRun matching *run_id*, or None if not found."""
    for run in storage.load_all():
        if run.run_id == run_id:
            return run
    return None


def replay_run(
    storage: JobRunStorage,
    run_id: str,
    *,
    timeout: Optional[float] = None,
) -> JobRun:
    """Re-execute the command from a previous run and persist the result.

    Parameters
    ----------
    storage:
        A :class:`JobRunStorage` instance used to look up the original run
        and persist the new one.
    run_id:
        The unique identifier of the run to replay.
    timeout:
        Optional timeout (seconds) forwarded to :func:`run_job`.

    Returns
    -------
    JobRun
        The *new* run produced by re-executing the original command.

    Raises
    ------
    ValueError
        If no run with the given *run_id* can be found.
    """
    original = find_run(storage, run_id)
    if original is None:
        raise ValueError(f"No run found with id '{run_id}'")

    new_run = run_job(
        job_name=original.job_name,
        command=original.command,
        storage=storage,
        timeout=timeout,
    )
    return new_run
