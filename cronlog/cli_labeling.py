"""CLI sub-commands for managing run labels."""

from __future__ import annotations

import argparse

from cronlog.labeling import (
    all_label_keys,
    filter_by_label,
    filter_has_label,
    get_label,
    remove_label,
    set_label,
)
from cronlog.storage import JobRunStorage


def add_labeling_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("labels", help="Manage labels on job runs")
    sub = p.add_subparsers(dest="labels_cmd")

    # set
    ps = sub.add_parser("set", help="Set a label on a run")
    ps.add_argument("run_id", help="Run ID")
    ps.add_argument("key", help="Label key")
    ps.add_argument("value", help="Label value")

    # remove
    pr = sub.add_parser("remove", help="Remove a label from a run")
    pr.add_argument("run_id", help="Run ID")
    pr.add_argument("key", help="Label key")

    # get
    pg = sub.add_parser("get", help="Get a label value from a run")
    pg.add_argument("run_id", help="Run ID")
    pg.add_argument("key", help="Label key")

    # list-keys
    sub.add_parser("list-keys", help="List all label keys across all runs")

    # filter
    pf = sub.add_parser("filter", help="Filter runs by label")
    pf.add_argument("key", help="Label key")
    pf.add_argument("value", nargs="?", default=None, help="Label value (omit to match any)")

    p.set_defaults(func=cmd_labels)


def cmd_labels(args: argparse.Namespace, storage: JobRunStorage) -> None:
    runs = storage.load_all()

    if args.labels_cmd == "set":
        matched = [r for r in runs if r.run_id == args.run_id]
        if not matched:
            print(f"Run '{args.run_id}' not found.")
            return
        set_label(matched[0], args.key, args.value)
        storage.save(matched[0])
        print(f"Label '{args.key}={args.value}' set on run {args.run_id}.")

    elif args.labels_cmd == "remove":
        matched = [r for r in runs if r.run_id == args.run_id]
        if not matched:
            print(f"Run '{args.run_id}' not found.")
            return
        remove_label(matched[0], args.key)
        storage.save(matched[0])
        print(f"Label '{args.key}' removed from run {args.run_id}.")

    elif args.labels_cmd == "get":
        matched = [r for r in runs if r.run_id == args.run_id]
        if not matched:
            print(f"Run '{args.run_id}' not found.")
            return
        val = get_label(matched[0], args.key)
        print(val if val is not None else f"(no label '{args.key}')")

    elif args.labels_cmd == "list-keys":
        keys = all_label_keys(runs)
        if keys:
            print("\n".join(keys))
        else:
            print("No labels found.")

    elif args.labels_cmd == "filter":
        if args.value is not None:
            result = filter_by_label(runs, args.key, args.value)
        else:
            result = filter_has_label(runs, args.key)
        if result:
            for r in result:
                print(r.run_id, r.job_name)
        else:
            print("No matching runs.")

    else:
        print("Specify a labels sub-command: set, remove, get, list-keys, filter")
