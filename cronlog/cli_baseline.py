"""CLI subcommand for baseline management."""

from __future__ import annotations

import argparse
from typing import List

from cronlog.baseline import (
    compute_baseline,
    exceeds_baseline,
    load_all_baselines,
    load_baseline,
    save_baseline,
)
from cronlog.storage import JobRunStorage


def add_baseline_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("baseline", help="Manage job duration baselines")
    sub = parser.add_subparsers(dest="baseline_cmd")

    set_p = sub.add_parser("set", help="Compute and save baseline for a job")
    set_p.add_argument("job_name", help="Job name")
    set_p.add_argument("--last", type=int, default=20, help="Number of recent runs to average")

    sub.add_parser("list", help="List all stored baselines")

    check_p = sub.add_parser("check", help="Check recent runs against their baselines")
    check_p.add_argument("--threshold", type=float, default=0.2, help="Fractional threshold (default 0.2)")

    parser.set_defaults(func=cmd_baseline)


def cmd_baseline(args: argparse.Namespace, storage: JobRunStorage) -> None:
    cmd = getattr(args, "baseline_cmd", None)

    if cmd == "set":
        runs = [r for r in storage.load_all() if r.job_name == args.job_name]
        runs = sorted(runs, key=lambda r: r.started_at or __import__("datetime").datetime.min)[-args.last :]
        baseline = compute_baseline(runs)
        if baseline is None:
            print(f"No finished runs found for '{args.job_name}'.")
            return
        save_baseline(storage.log_dir, args.job_name, baseline)
        print(f"Baseline for '{args.job_name}' set to {baseline:.2f}s (averaged over {len(runs)} run(s)).")

    elif cmd == "list":
        baselines = load_all_baselines(storage.log_dir)
        if not baselines:
            print("No baselines stored.")
            return
        print(f"{'Job':<30} {'Baseline (s)':>12}")
        print("-" * 44)
        for job, val in sorted(baselines.items()):
            print(f"{job:<30} {val:>12.2f}")

    elif cmd == "check":
        all_runs = storage.load_all()
        baselines = load_all_baselines(storage.log_dir)
        flagged = []
        for run in all_runs:
            b = baselines.get(run.job_name)
            if b is not None and exceeds_baseline(run, b, threshold=args.threshold):
                flagged.append((run, b))
        if not flagged:
            print("All runs within baseline thresholds.")
            return
        print(f"{'Run ID':<36} {'Job':<20} {'Duration (s)':>12} {'Baseline (s)':>12}")
        print("-" * 84)
        for run, b in flagged:
            from cronlog.baseline import _duration_seconds
            d = _duration_seconds(run) or 0.0
            print(f"{run.run_id:<36} {run.job_name:<20} {d:>12.2f} {b:>12.2f}")
    else:
        print("Usage: cronlog baseline {set,list,check}")
