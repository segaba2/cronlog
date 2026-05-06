"""Export job run data to various formats (JSON, CSV)."""

import csv
import json
import io
from typing import List

from cronlog.models import JobRun


def export_to_json(runs: List[JobRun], indent: int = 2) -> str:
    """Serialize a list of JobRun objects to a JSON string."""
    return json.dumps([run.to_dict() for run in runs], indent=indent, default=str)


def export_to_csv(runs: List[JobRun]) -> str:
    """Serialize a list of JobRun objects to a CSV string."""
    if not runs:
        return ""

    fieldnames = [
        "run_id",
        "job_name",
        "command",
        "status",
        "exit_code",
        "started_at",
        "finished_at",
        "stdout",
        "stderr",
    ]

    output = io.StringIO()
    writer = csv.DictWriter(
        output, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()

    for run in runs:
        row = run.to_dict()
        # Flatten datetime objects to ISO strings if not already strings
        for key in ("started_at", "finished_at"):
            if row.get(key) is not None and not isinstance(row[key], str):
                row[key] = row[key].isoformat()
        writer.writerow(row)

    return output.getvalue()


def export_runs(runs: List[JobRun], fmt: str) -> str:
    """Export runs in the specified format ('json' or 'csv')."""
    fmt = fmt.lower()
    if fmt == "json":
        return export_to_json(runs)
    elif fmt == "csv":
        return export_to_csv(runs)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}. Use 'json' or 'csv'.")
