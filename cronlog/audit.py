"""Audit log for cronlog — records significant events (run start, finish, prune, etc.)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

_AUDIT_FILENAME = "audit.log"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _audit_path(log_dir: str) -> str:
    return os.path.join(log_dir, _AUDIT_FILENAME)


def record_event(
    log_dir: str,
    event: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Append a single audit event to the audit log and return the entry."""
    entry: Dict[str, Any] = {
        "timestamp": _utcnow().isoformat(),
        "event": event,
        "details": details or {},
    }
    path = _audit_path(log_dir)
    os.makedirs(log_dir, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


def load_events(log_dir: str) -> List[Dict[str, Any]]:
    """Return all audit events recorded in *log_dir*, oldest first."""
    path = _audit_path(log_dir)
    if not os.path.exists(path):
        return []
    events: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def filter_events_by_type(events: List[Dict[str, Any]], event: str) -> List[Dict[str, Any]]:
    """Return only events whose *event* field matches *event*."""
    return [e for e in events if e.get("event") == event]


def clear_audit_log(log_dir: str) -> None:
    """Delete the audit log file if it exists."""
    path = _audit_path(log_dir)
    if os.path.exists(path):
        os.remove(path)
