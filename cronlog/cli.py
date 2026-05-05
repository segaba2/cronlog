"""Minimal CLI entry point: cronlog run <job_name> -- <command...>"""
import argparse
import sys

from cronlog.runner import run_job
from cronlog.storage import JobRunStorage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronlog",
        description="Capture and store cron job output with structured metadata.",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    run_p = sub.add_parser("run", help="Execute a job and log its output.")
    run_p.add_argument("job_name", help="Logical name for the job.")
    run_p.add_argument(
        "command", nargs=argparse.REMAINDER, help="Command to execute."
    )
    run_p.add_argument(
        "--log-dir", default=".cronlog", help="Directory to store log files."
    )
    run_p.add_argument(
        "--timeout", type=int, default=None, help="Timeout in seconds."
    )

    list_p = sub.add_parser("list", help="List recent job runs.")
    list_p.add_argument("--log-dir", default=".cronlog")
    list_p.add_argument("--job-name", default=None, help="Filter by job name.")

    return parser


def cmd_run(args: argparse.Namespace) -> int:
    command = [c for c in args.command if c != "--"]
    if not command:
        print("Error: no command provided.", file=sys.stderr)
        return 2

    storage = JobRunStorage(log_dir=args.log_dir)
    run = run_job(args.job_name, command, storage=storage, timeout=args.timeout)

    status_label = run.status.value.upper()
    print(f"[{status_label}] {run.job_name} (run_id={run.run_id}, exit={run.exit_code})")
    if run.stdout:
        print("\n".join(run.stdout))
    if run.stderr:
        print("\n".join(run.stderr), file=sys.stderr)

    return 0 if run.exit_code == 0 else 1


def cmd_list(args: argparse.Namespace) -> int:
    storage = JobRunStorage(log_dir=args.log_dir)
    runs = (
        storage.find_by_job_name(args.job_name)
        if args.job_name
        else storage.load_all()
    )
    if not runs:
        print("No runs found.")
        return 0
    for r in runs:
        ts = r.started_at.strftime("%Y-%m-%d %H:%M:%S") if r.started_at else "?"
        print(f"{ts}  {r.job_name:<20}  {r.status.value:<8}  {r.run_id}")
    return 0


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.subcommand == "run":
        return cmd_run(args)
    if args.subcommand == "list":
        return cmd_list(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
