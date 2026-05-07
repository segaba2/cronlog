"""CLI subcommand for applying retention policies to stored job runs."""

import argparse
from pathlib import Path

from cronlog.storage import JobRunStorage, DEFAULT_LOG_PATH
from cronlog.retention import apply_retention


def add_retention_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "prune",
        help="Remove old job run records according to retention policies",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=None,
        metavar="DAYS",
        help="Delete runs older than DAYS days",
    )
    parser.add_argument(
        "--max-count",
        type=int,
        default=None,
        metavar="N",
        help="Keep only the N most recent runs overall",
    )
    parser.add_argument(
        "--max-per-job",
        type=int,
        default=None,
        metavar="N",
        help="Keep only the N most recent runs per job",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help="Path to the run log file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show how many runs would be pruned without modifying the log",
    )
    parser.set_defaults(func=cmd_prune)


def cmd_prune(args: argparse.Namespace) -> None:
    if args.max_age_days is None and args.max_count is None and args.max_per_job is None:
        print("Error: specify at least one of --max-age-days, --max-count, --max-per-job")
        return

    storage = JobRunStorage(path=args.log_file)

    if args.dry_run:
        from cronlog.retention import prune_by_age, prune_by_count, prune_by_job_count
        runs = storage.load_all()
        original = len(runs)
        if args.max_age_days is not None:
            runs = prune_by_age(runs, args.max_age_days)
        if args.max_per_job is not None:
            runs = prune_by_job_count(runs, args.max_per_job)
        if args.max_count is not None:
            runs = prune_by_count(runs, args.max_count)
        pruned = original - len(runs)
        print(f"Dry run: would prune {pruned} of {original} run(s).")
        return

    pruned = apply_retention(
        storage,
        max_age_days=args.max_age_days,
        max_count=args.max_count,
        max_per_job=args.max_per_job,
    )
    print(f"Pruned {pruned} run(s).")
