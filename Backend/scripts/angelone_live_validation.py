#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Wrapper for Django Angel One live validation command")
    parser.add_argument("--broker-details-id", type=int)
    parser.add_argument("--user-email")
    parser.add_argument("--client-code")
    parser.add_argument("--skip-logout", action="store_true")
    parser.add_argument("--skip-concurrency", action="store_true")
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--inject", choices=["redis_down", "broker_down", "network_timeout", "invalid_credentials"])
    args = parser.parse_args()

    backend_root = Path(__file__).resolve().parents[1]
    manage_py = backend_root / "manage.py"
    python_bin = backend_root / "venv" / "bin" / "python"
    cmd = [
        str(python_bin),
        str(manage_py),
        "validate_angelone_live",
        "--concurrency",
        str(args.concurrency),
        "--iterations",
        str(args.iterations),
    ]

    for flag in ("skip_logout", "skip_concurrency"):
        if getattr(args, flag):
            cmd.append(f"--{flag.replace('_', '-')}")
    if args.broker_details_id:
        cmd.extend(["--broker-details-id", str(args.broker_details_id)])
    if args.user_email:
        cmd.extend(["--user-email", args.user_email])
    if args.client_code:
        cmd.extend(["--client-code", args.client_code])
    if args.inject:
        cmd.extend(["--inject", args.inject])

    completed = subprocess.run(cmd, cwd=str(backend_root), capture_output=True, text=True)
    if completed.stdout:
        try:
            print(json.dumps(json.loads(completed.stdout), indent=2))
        except Exception:
            print(completed.stdout)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
