"""CLI subcommand for managing job run annotations."""

import argparse
from cronlog.storage import JobRunStorage
from cronlog.annotations import annotate, remove_annotation, get_annotation, all_annotation_keys


def add_annotations_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("annotate", help="Manage annotations on job runs")
    sub = parser.add_subparsers(dest="annotation_cmd", required=True)

    # annotate set <run_id> <key> <value>
    p_set = sub.add_parser("set", help="Set an annotation on a run")
    p_set.add_argument("run_id", help="Run ID to annotate")
    p_set.add_argument("key", help="Annotation key")
    p_set.add_argument("value", help="Annotation value")

    # annotate remove <run_id> <key>
    p_rm = sub.add_parser("remove", help="Remove an annotation from a run")
    p_rm.add_argument("run_id", help="Run ID")
    p_rm.add_argument("key", help="Annotation key to remove")

    # annotate get <run_id> <key>
    p_get = sub.add_parser("get", help="Get a single annotation value")
    p_get.add_argument("run_id", help="Run ID")
    p_get.add_argument("key", help="Annotation key")

    # annotate list-keys
    sub.add_parser("list-keys", help="List all annotation keys across all runs")

    parser.set_defaults(func=cmd_annotations)


def cmd_annotations(args: argparse.Namespace, storage: JobRunStorage) -> None:
    cmd = args.annotation_cmd

    if cmd == "list-keys":
        runs = storage.load_all()
        keys = all_annotation_keys(runs)
        if keys:
            for k in keys:
                print(k)
        else:
            print("No annotations found.")
        return

    # Commands that need a specific run
    runs = storage.load_all()
    match = [r for r in runs if r.run_id == args.run_id]
    if not match:
        print(f"Error: run '{args.run_id}' not found.")
        return
    run = match[0]

    if cmd == "set":
        annotate(run, args.key, args.value)
        storage.save(run)
        print(f"Annotation '{args.key}' set on run {run.run_id}.")

    elif cmd == "remove":
        remove_annotation(run, args.key)
        storage.save(run)
        print(f"Annotation '{args.key}' removed from run {run.run_id}.")

    elif cmd == "get":
        value = get_annotation(run, args.key)
        if value is None:
            print(f"No annotation '{args.key}' on run {run.run_id}.")
        else:
            print(value)
