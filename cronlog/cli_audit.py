"""CLI sub-commands for the cronlog audit log."""

from __future__ import annotations

import argparse
from typing import Any

from cronlog.audit import load_events, filter_events_by_type, clear_audit_log


def add_audit_subparser(subparsers: Any) -> None:
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "audit", help="View or clear the audit log"
    )
    sub = parser.add_subparsers(dest="audit_cmd")

    list_p = sub.add_parser("list", help="List audit events")
    list_p.add_argument(
        "--event", metavar="TYPE", help="Filter by event type"
    )

    sub.add_parser("clear", help="Clear the audit log")

    parser.set_defaults(func=cmd_audit)


def cmd_audit(args: argparse.Namespace, log_dir: str) -> None:
    audit_cmd = getattr(args, "audit_cmd", None)

    if audit_cmd == "clear":
        clear_audit_log(log_dir)
        print("Audit log cleared.")
        return

    # Default: list
    events = load_events(log_dir)
    event_type = getattr(args, "event", None)
    if event_type:
        events = filter_events_by_type(events, event_type)

    if not events:
        print("No audit events found.")
        return

    for entry in events:
        details = entry.get("details", {})
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        line = f"[{entry['timestamp']}] {entry['event']}"
        if detail_str:
            line += f"  ({detail_str})"
        print(line)
