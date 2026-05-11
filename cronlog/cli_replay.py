"""CLI sub-command: cronlog replay <run_id>."""

from __future__ import annotations

import argparse

from cronlog.replay import replay_run
from cronlog.storage import JobRunStorage
from cronlog.formatter import format_run_detail


def add_replay_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *replay* sub-command on *subparsers*."""
    parser = subparsers.add_parser(
        "replay",
        help="Re-run a previous job by its run ID",
    )
    parser.add_argument("run_id", help="ID of the run to replay")
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Optional timeout for the replayed command",
    )
    parser.add_argument(
        "--log-dir",
        default=".cronlog",
        metavar="DIR",
        help="Directory where run logs are stored (default: .cronlog)",
    )
    parser.set_defaults(func=cmd_replay)


def cmd_replay(args: argparse.Namespace) -> None:
    """Handle the *replay* sub-command."""
    storage = JobRunStorage(args.log_dir)
    try:
        new_run = replay_run(storage, args.run_id, timeout=args.timeout)
    except ValueError as exc:
        print(f"Error: {exc}")
        return

    print("Replay complete.")
    print(format_run_detail(new_run.to_dict()))
