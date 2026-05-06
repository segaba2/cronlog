"""Text formatting helpers for displaying JobRun records in the CLI."""

from typing import List

from cronlog.models import JobRun, JobStatus

_STATUS_LABEL = {
    JobStatus.RUNNING: "RUNNING",
    JobStatus.SUCCESS: "OK     ",
    JobStatus.FAILURE: "FAIL   ",
}

_STATUS_COLOR = {
    JobStatus.RUNNING: "\033[33m",  # yellow
    JobStatus.SUCCESS: "\033[32m",  # green
    JobStatus.FAILURE: "\033[31m",  # red
}
_RESET = "\033[0m"


def _format_duration(run: JobRun) -> str:
    if run.finished_at is None:
        return "--"
    delta = run.finished_at - run.started_at
    total = int(delta.total_seconds())
    minutes, seconds = divmod(total, 60)
    return f"{minutes}m{seconds:02d}s"


def format_run_row(run: JobRun, color: bool = True) -> str:
    """Return a single-line summary of a JobRun."""
    label = _STATUS_LABEL.get(run.status, "UNKNOWN")
    started = run.started_at.strftime("%Y-%m-%d %H:%M:%S")
    duration = _format_duration(run)
    exit_code = str(run.exit_code) if run.exit_code is not None else "-"

    if color:
        color_code = _STATUS_COLOR.get(run.status, "")
        label = f"{color_code}{label}{_RESET}"

    return f"{started}  {label}  {run.job_name:<20}  exit={exit_code:<4}  duration={duration}"


def format_run_detail(run: JobRun, color: bool = True) -> str:
    """Return a multi-line detailed view of a single JobRun."""
    lines = [
        f"Run ID   : {run.run_id}",
        f"Job      : {run.job_name}",
        f"Command  : {run.command}",
        f"Status   : {run.status.value}",
        f"Started  : {run.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Finished : {run.finished_at.strftime('%Y-%m-%d %H:%M:%S UTC') if run.finished_at else 'still running'}",
        f"Duration : {_format_duration(run)}",
        f"Exit code: {run.exit_code}",
    ]
    if run.stdout:
        lines += ["", "--- stdout ---", run.stdout.rstrip()]
    if run.stderr:
        lines += ["", "--- stderr ---", run.stderr.rstrip()]
    return "\n".join(lines)


def format_run_table(runs: List[JobRun], color: bool = True) -> str:
    """Return a formatted table of multiple runs."""
    if not runs:
        return "No runs found."
    header = f"{'STARTED':<19}  {'STATUS':<9}  {'JOB':<20}  {'EXIT':<9}  DURATION"
    separator = "-" * len(header)
    rows = [header, separator] + [format_run_row(r, color=color) for r in runs]
    return "\n".join(rows)
