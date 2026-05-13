"""CLI subcommand: cronlog profile — show slow-run profiling reports."""

from __future__ import annotations

import argparse
import json

from cronlog.profiler import compute_average_duration, find_slow_runs, profile_by_job, slowest_runs
from cronlog.storage import JobRunStorage


def add_profiler_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("profile", help="Profile job run durations")
    sub = p.add_subparsers(dest="profile_cmd")

    slow = sub.add_parser("slow", help="List runs exceeding a duration threshold")
    slow.add_argument("--threshold", type=float, default=60.0, metavar="SECONDS",
                      help="Duration threshold in seconds (default: 60)")
    slow.add_argument("--job", metavar="NAME", help="Filter by job name")

    top = sub.add_parser("top", help="Show the N slowest runs")
    top.add_argument("--n", type=int, default=5, metavar="N")
    top.add_argument("--json", dest="as_json", action="store_true")

    by_job = sub.add_parser("by-job", help="Per-job profiling stats")
    by_job.add_argument("--json", dest="as_json", action="store_true")

    p.set_defaults(func=cmd_profile)


def cmd_profile(args: argparse.Namespace, storage: JobRunStorage) -> None:
    runs = storage.load_all()

    if args.profile_cmd == "slow":
        candidates = [r for r in runs if not args.job or r.job_name == args.job]
        slow = find_slow_runs(candidates, args.threshold)
        if not slow:
            print(f"No runs exceeded {args.threshold}s.")
            return
        for r in slow:
            from cronlog.profiler import _duration_seconds
            d = _duration_seconds(r)
            print(f"{r.run_id[:8]}  {r.job_name:<24}  {d:.1f}s")

    elif args.profile_cmd == "top":
        top = slowest_runs(runs, n=args.n)
        if not top:
            print("No finished runs found.")
            return
        if getattr(args, "as_json", False):
            from cronlog.profiler import _duration_seconds
            print(json.dumps([{"run_id": r.run_id, "job_name": r.job_name,
                               "duration_seconds": _duration_seconds(r)} for r in top], indent=2))
        else:
            for r in top:
                from cronlog.profiler import _duration_seconds
                print(f"{r.run_id[:8]}  {r.job_name:<24}  {_duration_seconds(r):.1f}s")

    elif args.profile_cmd == "by-job":
        stats = profile_by_job(runs)
        if not stats:
            print("No profiling data available.")
            return
        if getattr(args, "as_json", False):
            print(json.dumps(stats, indent=2))
        else:
            print(f"{'Job':<28} {'Count':>6} {'Avg(s)':>9} {'Min(s)':>9} {'Max(s)':>9}")
            print("-" * 65)
            for job_name, s in sorted(stats.items()):
                print(f"{job_name:<28} {s['count']:>6} {s['avg_seconds']:>9.1f} "
                      f"{s['min_seconds']:>9.1f} {s['max_seconds']:>9.1f}")
    else:
        avg = compute_average_duration(runs)
        print(f"Total runs: {len(runs)}")
        print(f"Average duration: {avg:.1f}s" if avg is not None else "Average duration: n/a")
