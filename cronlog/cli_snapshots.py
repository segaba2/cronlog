"""CLI sub-commands for snapshot management."""

from __future__ import annotations

import json
import sys

from cronlog.snapshots import create_snapshot, load_snapshots, delete_snapshot
from cronlog.storage import JobRunStorage


def add_snapshots_subparser(subparsers) -> None:
    p = subparsers.add_parser("snapshot", help="Manage run-stat snapshots")
    sp = p.add_subparsers(dest="snapshot_cmd", required=True)

    # create
    c = sp.add_parser("create", help="Create a new snapshot")
    c.add_argument("--label", default="", help="Optional snapshot label")
    c.add_argument("--log-dir", default=".cronlog", dest="log_dir")

    # list
    ls = sp.add_parser("list", help="List existing snapshots")
    ls.add_argument("--log-dir", default=".cronlog", dest="log_dir")
    ls.add_argument("--json", action="store_true", dest="as_json")

    # delete
    d = sp.add_parser("delete", help="Delete a snapshot by label")
    d.add_argument("label", help="Label of the snapshot to delete")
    d.add_argument("--log-dir", default=".cronlog", dest="log_dir")

    p.set_defaults(func=cmd_snapshot)


def cmd_snapshot(args) -> None:
    if args.snapshot_cmd == "create":
        storage = JobRunStorage(args.log_dir)
        runs = storage.load_all()
        snap = create_snapshot(runs, args.log_dir, label=args.label)
        print(f"Snapshot created: {snap['label']}")

    elif args.snapshot_cmd == "list":
        snaps = load_snapshots(args.log_dir)
        if not snaps:
            print("No snapshots found.")
            return
        if args.as_json:
            print(json.dumps(snaps, indent=2))
        else:
            print(f"{'Label':<30} {'Created':<30} {'Total':>6}")
            print("-" * 70)
            for s in snaps:
                total = s.get("summary", {}).get("total", 0)
                print(f"{s['label']:<30} {s['created_at']:<30} {total:>6}")

    elif args.snapshot_cmd == "delete":
        removed = delete_snapshot(args.log_dir, args.label)
        if removed:
            print(f"Deleted snapshot: {args.label}")
        else:
            print(f"Snapshot not found: {args.label}", file=sys.stderr)
            sys.exit(1)
