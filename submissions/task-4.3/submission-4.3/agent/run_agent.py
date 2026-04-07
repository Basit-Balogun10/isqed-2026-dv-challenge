#!/usr/bin/env python3
"""Task 4.3 Spec Interpreter entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml  # type: ignore[import-untyped]

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from io_utils import load_dotenv_upwards
from spec_orchestrator import SpecInterpreterOrchestrator  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Task 4.3 Spec Interpreter")
    parser.add_argument(
        "--spec",
        required=True,
        help="Path to natural-language specification markdown file",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Directory where generated artifacts will be written",
    )
    parser.add_argument(
        "--config",
        default=str(SCRIPT_DIR / "agent_config.yaml"),
        help="Path to agent config YAML",
    )
    return parser.parse_args()


def load_config(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as file_handle:
        loaded = yaml.safe_load(file_handle) or {}
    if not isinstance(loaded, dict):
        raise RuntimeError("agent config must be a YAML mapping")
    return loaded


def _validate_inputs(args: argparse.Namespace) -> None:
    spec_path = Path(args.spec)
    if not spec_path.exists() or not spec_path.is_file():
        raise FileNotFoundError(f"Spec file not found: {spec_path}")


def main() -> int:
    args = parse_args()

    # Allow local execution with root-level .env while keeping secrets out of repo.
    load_dotenv_upwards(start_dir=Path.cwd())

    _validate_inputs(args)
    config = load_config(args.config)

    orchestrator = SpecInterpreterOrchestrator(config=config)
    orchestrator.run(
        spec_path=Path(args.spec).resolve(),
        output_dir=Path(args.output_dir).resolve(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
