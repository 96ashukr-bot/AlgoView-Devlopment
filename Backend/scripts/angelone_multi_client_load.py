#!/usr/bin/env python3
import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def run_for_client(backend_root: Path, client_code: str, concurrency: int, iterations: int):
    python_bin = backend_root / "venv" / "bin" / "python"
    manage_py = backend_root / "manage.py"
    cmd = [
        str(python_bin),
        str(manage_py),
        "validate_angelone_live",
        "--client-code",
        client_code,
        "--concurrency",
        str(concurrency),
        "--iterations",
        str(iterations),
        "--skip-logout",
    ]
    completed = subprocess.run(cmd, cwd=str(backend_root), capture_output=True, text=True)
    payload = {}
    if completed.stdout:
        try:
            payload = json.loads(completed.stdout)
        except Exception:
            payload = {"raw_stdout": completed.stdout}
    return {
        "client_code": client_code,
        "returncode": completed.returncode,
        "result": payload,
        "stderr": completed.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Angel One validation across multiple clients")
    parser.add_argument("--client-file", required=True, help="Path to newline-delimited client-code file")
    parser.add_argument("--parallel-clients", type=int, default=3)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--iterations", type=int, default=10)
    args = parser.parse_args()

    backend_root = Path(__file__).resolve().parents[1]
    client_codes = [line.strip() for line in Path(args.client_file).read_text().splitlines() if line.strip()]
    summaries = []
    with ThreadPoolExecutor(max_workers=args.parallel_clients) as pool:
        futures = [
            pool.submit(run_for_client, backend_root, client_code, args.concurrency, args.iterations)
            for client_code in client_codes
        ]
        for future in as_completed(futures):
            summaries.append(future.result())

    print(json.dumps({"clients": summaries}, indent=2))
    return 0 if all(item["returncode"] == 0 for item in summaries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
