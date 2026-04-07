#!/usr/bin/env python3
"""Compatibility entrypoint for Task 4.3 task-page interface.

This wrapper preserves the task-page command shape:
  python run_spec_interpreter.py --spec ... --output_dir ...

It forwards execution to the canonical implementation in agent/run_agent.py.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description="Task 4.3 compatibility runner")
    parser.add_argument(
        "--spec",
        required=True,
        help="Path to natural-language specification markdown file",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Output directory for generated spec-interpretation artifacts",
    )
    parser.add_argument(
        "--config",
        default="agent/agent_config.yaml",
        help="Path to agent configuration YAML",
    )
    args, extra = parser.parse_known_args()
    return args, extra


def main() -> int:
    args, extra = parse_args()

    repo_root = Path(__file__).resolve().parent
    run_agent = repo_root / "agent" / "run_agent.py"

    cmd = [
        sys.executable,
        str(run_agent),
        "--spec",
        args.spec,
        "--output_dir",
        args.output_dir,
        "--config",
        args.config,
    ]
    if extra:
        cmd.extend(extra)

    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
