#!/usr/bin/env python3
"""Compatibility entrypoint for Task 4.2 task-page interface.

This wrapper preserves the task-page command shape:
  python run_regression_agent.py --baseline_rtl ... --baseline_env ... --listen ...

It forwards execution to the canonical implementation in agent/run_agent.py.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description="Task 4.2 compatibility runner")
    parser.add_argument("--baseline_rtl", required=True, help="Baseline RTL directory")
    parser.add_argument(
        "--baseline_env",
        required=True,
        help="Baseline verification environment directory",
    )
    parser.add_argument(
        "--listen",
        choices=["file", "stdin", "http"],
        default="http",
        help="Input mode (default: http)",
    )
    parser.add_argument(
        "--commit_stream",
        required=False,
        help="Commit stream JSON path (required for --listen file)",
    )
    parser.add_argument(
        "--output_dir",
        default="output",
        help="Output directory for verdict artifacts",
    )
    parser.add_argument(
        "--config",
        default="agent/agent_config.yaml",
        help="Path to agent configuration YAML",
    )
    parser.add_argument("--port", type=int, default=8080, help="HTTP listen port")
    args, extra = parser.parse_known_args()
    return args, extra


def main() -> int:
    args, extra = parse_args()

    if args.listen == "file" and not args.commit_stream:
        raise SystemExit("--commit_stream is required when --listen file")

    repo_root = Path(__file__).resolve().parent
    run_agent = repo_root / "agent" / "run_agent.py"

    cmd = [
        sys.executable,
        str(run_agent),
        "--listen",
        args.listen,
        "--baseline_rtl",
        args.baseline_rtl,
        "--baseline_env",
        args.baseline_env,
        "--output_dir",
        args.output_dir,
        "--config",
        args.config,
        "--port",
        str(args.port),
    ]
    if args.commit_stream:
        cmd.extend(["--commit_stream", args.commit_stream])
    if extra:
        cmd.extend(extra)

    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())