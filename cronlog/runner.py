import subprocess
import time
from datetime import datetime, timezone
from typing import List, Optional

from cronlog.models import JobRun
from cronlog.storage import JobRunStorage


def run_job(
    job_name: str,
    command: List[str],
    storage: Optional[JobRunStorage] = None,
    timeout: Optional[int] = None,
) -> JobRun:
    """Execute a shell command as a named cron job, capture output, and persist the run."""
    run = JobRun(job_name=job_name, command=command)

    stdout_lines = []
    stderr_lines = []

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout_lines = result.stdout.splitlines()
        stderr_lines = result.stderr.splitlines()
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        stderr_lines = [f"Job '{job_name}' timed out after {timeout} seconds."]
        exit_code = -1
    except FileNotFoundError as exc:
        stderr_lines = [f"Command not found: {exc}"]
        exit_code = 127
    except Exception as exc:  # noqa: BLE001
        stderr_lines = [f"Unexpected error: {exc}"]
        exit_code = -1

    run.finish(exit_code=exit_code, stdout=stdout_lines, stderr=stderr_lines)

    if storage is not None:
        storage.save(run)

    return run
