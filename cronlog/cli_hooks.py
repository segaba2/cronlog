"""CLI subcommand for managing and testing hooks."""

import argparse
from cronlog import hooks
from cronlog.models import JobRun, JobStatus
from datetime import datetime, timezone


def add_hooks_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("hooks", help="Manage pre/post execution hooks")
    sub = parser.add_subparsers(dest="hooks_cmd")

    sub.add_parser("list", help="List registered hooks")

    fire_p = sub.add_parser("fire", help="Fire hooks for a simulated job run")
    fire_p.add_argument("job_name", help="Job name to simulate")
    fire_p.add_argument(
        "--phase",
        choices=["pre", "post", "both"],
        default="both",
        help="Which hooks to fire (default: both)",
    )
    fire_p.add_argument(
        "--status",
        choices=["success", "failure"],
        default="success",
        help="Simulated job status (default: success)",
    )

    parser.set_defaults(func=cmd_hooks)


def cmd_hooks(args: argparse.Namespace) -> None:
    cmd = getattr(args, "hooks_cmd", None)

    if cmd == "list":
        pre_count = len(hooks._pre_hooks)
        post_count = len(hooks._post_hooks)
        print(f"Pre-hooks  : {pre_count} registered")
        print(f"Post-hooks : {post_count} registered")
        return

    if cmd == "fire":
        run = JobRun(job_name=args.job_name, command=f"simulate:{args.job_name}")
        if args.phase in ("pre", "both"):
            hooks.run_pre_hooks(run)
        if args.phase in ("post", "both"):
            status = JobStatus.SUCCESS if args.status == "success" else JobStatus.FAILURE
            run.finish(exit_code=0 if status == JobStatus.SUCCESS else 1, stdout="", stderr="")
            hooks.run_post_hooks(run)
        print(f"Hooks fired for job '{args.job_name}' (phase={args.phase}).")
        return

    print("Use 'cronlog hooks list' or 'cronlog hooks fire <job_name>'.")
