"""CLI subcommands for pipeline inspection."""

from __future__ import annotations

import argparse
import json
from typing import List

from cronlog import pipeline as pl
from cronlog.models import JobRun
from cronlog.storage import JobRunStorage


def add_pipeline_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("pipeline", help="Inspect job pipelines")
    sub = parser.add_subparsers(dest="pipeline_cmd")

    # list
    sub.add_parser("list", help="List all known pipeline IDs")

    # status
    status_p = sub.add_parser("status", help="Show aggregate status of a pipeline")
    status_p.add_argument("pipeline_id", help="Pipeline ID to inspect")
    status_p.add_argument("--json", dest="as_json", action="store_true",
                          help="Output as JSON")

    # runs
    runs_p = sub.add_parser("runs", help="List runs belonging to a pipeline")
    runs_p.add_argument("pipeline_id", help="Pipeline ID to inspect")

    parser.set_defaults(func=cmd_pipeline)


def cmd_pipeline(args: argparse.Namespace, storage: JobRunStorage) -> None:
    cmd = getattr(args, "pipeline_cmd", None)
    if cmd is None or cmd == "list":
        _cmd_list(args)
    elif cmd == "status":
        _cmd_status(args, storage)
    elif cmd == "runs":
        _cmd_runs(args, storage)
    else:
        print(f"Unknown pipeline subcommand: {cmd}")


def _cmd_list(args: argparse.Namespace) -> None:
    ids = pl.all_pipeline_ids()
    if not ids:
        print("No pipelines registered.")
        return
    for pid in ids:
        print(pid)


def _cmd_status(args: argparse.Namespace, storage: JobRunStorage) -> None:
    runs: List[JobRun] = storage.load_all()
    status = pl.pipeline_status(args.pipeline_id, runs)
    if getattr(args, "as_json", False):
        print(json.dumps({"pipeline_id": args.pipeline_id, "status": status.value}))
    else:
        print(f"Pipeline '{args.pipeline_id}': {status.value}")


def _cmd_runs(args: argparse.Namespace, storage: JobRunStorage) -> None:
    all_runs: List[JobRun] = storage.load_all()
    members = pl.get_pipeline_runs(args.pipeline_id, all_runs)
    if not members:
        print(f"No runs found for pipeline '{args.pipeline_id}'.")
        return
    for run in members:
        print(f"{run.run_id}  {run.job_name}  {run.status.value}")
