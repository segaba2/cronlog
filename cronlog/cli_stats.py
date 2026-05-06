import argparse
from cronlog.storage import JobRunStorage
from cronlog.stats import compute_stats, compute_stats_by_job


def add_stats_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("stats", help="Show run statistics")
    parser.add_argument("--job", metavar="NAME", help="Filter to a specific job name")
    parser.add_argument("--by-job", action="store_true", help="Break down stats per job")
    parser.set_defaults(func=cmd_stats)


def cmd_stats(args: argparse.Namespace, storage: JobRunStorage) -> None:
    runs = storage.load_all()

    if args.job:
        runs = [r for r in runs if r.job_name == args.job]

    if not runs:
        print("No runs found.")
        return

    if args.by_job:
        breakdown = compute_stats_by_job(runs)
        for job_name, stats in sorted(breakdown.items()):
            print(f"\n{job_name}")
            _print_stats(stats)
    else:
        label = f" for '{args.job}'" if args.job else ""
        print(f"Statistics{label}:")
        _print_stats(compute_stats(runs))


def _print_stats(stats: dict) -> None:
    print(f"  Total runs   : {stats['total']}")
    print(f"  Success      : {stats['success']}")
    print(f"  Failure      : {stats['failure']}")
    sr = stats['success_rate']
    print(f"  Success rate : {sr}%" if sr is not None else "  Success rate : N/A")
    avg = stats['avg_duration_seconds']
    print(f"  Avg duration : {avg}s" if avg is not None else "  Avg duration : N/A")
    mn = stats['min_duration_seconds']
    mx = stats['max_duration_seconds']
    print(f"  Min duration : {mn}s" if mn is not None else "  Min duration : N/A")
    print(f"  Max duration : {mx}s" if mx is not None else "  Max duration : N/A")
