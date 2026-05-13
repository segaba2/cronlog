"""Snapshot support: capture point-in-time summaries of all job run stats."""

from __future__ import annotations

import gzip
import json
import os
from datetime import datetime, timezone
from typing import Any

from cronlog.summary import summarise_runs, summarise_by_job


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _snapshot_path(log_dir: str) -> str:
    return os.path.join(log_dir, "snapshots")


def create_snapshot(runs: list, log_dir: str, label: str = "") -> dict[str, Any]:
    """Create and persist a snapshot of current run statistics."""
    now = _utcnow()
    snapshot = {
        "created_at": now.isoformat(),
        "label": label or now.strftime("%Y%m%dT%H%M%SZ"),
        "summary": summarise_runs(runs),
        "by_job": summarise_by_job(runs),
    }
    _persist_snapshot(snapshot, log_dir)
    return snapshot


def _persist_snapshot(snapshot: dict, log_dir: str) -> None:
    path = _snapshot_path(log_dir)
    os.makedirs(path, exist_ok=True)
    label = snapshot["label"]
    filename = os.path.join(path, f"{label}.json.gz")
    with gzip.open(filename, "wt", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2)


def load_snapshots(log_dir: str) -> list[dict[str, Any]]:
    """Load all persisted snapshots, sorted oldest-first."""
    path = _snapshot_path(log_dir)
    if not os.path.isdir(path):
        return []
    results = []
    for fname in sorted(os.listdir(path)):
        if fname.endswith(".json.gz"):
            full = os.path.join(path, fname)
            with gzip.open(full, "rt", encoding="utf-8") as fh:
                results.append(json.load(fh))
    return results


def delete_snapshot(log_dir: str, label: str) -> bool:
    """Delete a snapshot by label. Returns True if deleted, False if not found."""
    path = os.path.join(_snapshot_path(log_dir), f"{label}.json.gz")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
