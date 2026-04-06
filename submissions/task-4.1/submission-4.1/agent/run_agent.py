#!/usr/bin/env python3
"""Task 4.1 AutoVerifier entry point."""

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
from orchestrator import AutoVerifierOrchestrator  # noqa: E402


MAX_ITERATIONS_CAP = 12


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Task 4.1 AutoVerifier agent")
    parser.add_argument(
        "--rtl", required=True, help="Path to RTL file or RTL directory"
    )
    parser.add_argument(
        "--spec", required=True, help="Path to specification markdown file"
    )
    parser.add_argument("--csr_map", required=True, help="Path to CSR map Hjson file")
    parser.add_argument(
        "--output_dir", required=True, help="Directory to write generated outputs"
    )
    parser.add_argument(
        "--simulator",
        choices=("auto", "both", "icarus", "verilator"),
        default="auto",
        help="Simulator mode for generated tests",
    )
    parser.add_argument(
        "--max_iterations",
        type=int,
        default=4,
        help=(
            "Maximum iterate-stage rounds (default: 4). "
            f"Clamped to [1, {MAX_ITERATIONS_CAP}] to avoid unbounded loops."
        ),
    )
    parser.add_argument(
        "--max_repair_generations_per_iteration",
        type=int,
        default=1,
        help="Maximum repair tests generated per iteration (default: 1)",
    )
    parser.add_argument(
        "--iteration_mode",
        choices=("fixed", "auto"),
        default="auto",
        help=(
            "Iteration controller mode. "
            "'fixed' stops at max_iterations, 'auto' can extend in steps up to cap."
        ),
    )
    parser.add_argument(
        "--min_iterations",
        type=int,
        default=4,
        help=(
            "Minimum iterations to run when iteration_mode=auto (default: 4). "
            f"Clamped to [1, {MAX_ITERATIONS_CAP}]."
        ),
    )
    parser.add_argument(
        "--auto_extension_step",
        type=int,
        default=2,
        help="Additional iterations to grant per auto-extension event (default: 2)",
    )
    parser.add_argument(
        "--timeout_minutes",
        type=float,
        default=60.0,
        help=(
            "Global timeout for LLM generation (minutes). Default is 60 to "
            "match Task 4.1 budget."
        ),
    )
    parser.add_argument(
        "--config",
        default=str(SCRIPT_DIR / "agent_config.yaml"),
        help="Path to agent config YAML",
    )
    return parser.parse_args()


def load_config(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _validate_inputs(args: argparse.Namespace) -> None:
    rtl_path = Path(args.rtl)
    if not rtl_path.exists():
        raise FileNotFoundError(f"RTL path not found: {rtl_path}")

    spec_path = Path(args.spec)
    if not spec_path.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_path}")

    csr_map_path = Path(args.csr_map)
    if not csr_map_path.exists():
        raise FileNotFoundError(f"CSR map file not found: {csr_map_path}")

    if args.max_iterations < 1:
        raise ValueError("--max_iterations must be >= 1")
    if args.min_iterations < 1:
        raise ValueError("--min_iterations must be >= 1")
    if args.auto_extension_step < 1:
        raise ValueError("--auto_extension_step must be >= 1")
    if args.max_repair_generations_per_iteration < 0:
        raise ValueError("--max_repair_generations_per_iteration must be >= 0")
    if args.timeout_minutes < 0:
        raise ValueError("--timeout_minutes must be >= 0")


def main() -> int:
    args = parse_args()
    # Allow local execution with `.env` while keeping secrets out of logs.
    load_dotenv_upwards(start_dir=Path.cwd())

    _validate_inputs(args)
    config = load_config(args.config)
    if not isinstance(config, dict):
        raise RuntimeError("agent config must be a YAML mapping")

    agent_cfg = config.get("agent")
    if not isinstance(agent_cfg, dict):
        agent_cfg = {}
        config["agent"] = agent_cfg
    agent_cfg["simulator_mode"] = str(args.simulator)
    agent_cfg["max_iterations_cap"] = int(
        agent_cfg.get("max_iterations_cap", MAX_ITERATIONS_CAP)
    )
    requested_iterations = max(1, int(args.max_iterations))
    effective_cap = max(1, int(agent_cfg.get("max_iterations_cap", MAX_ITERATIONS_CAP)))
    agent_cfg["max_iterations"] = min(requested_iterations, effective_cap)
    requested_min_iterations = max(1, int(args.min_iterations))
    agent_cfg["min_iterations"] = min(requested_min_iterations, effective_cap)
    agent_cfg["max_repair_generations_per_iteration"] = max(
        0, int(args.max_repair_generations_per_iteration)
    )
    agent_cfg["iteration_mode"] = str(args.iteration_mode).strip().lower()
    agent_cfg["auto_extension_step"] = max(1, int(args.auto_extension_step))
    agent_cfg["timeout_minutes"] = max(0.0, float(args.timeout_minutes))

    rtl_path = Path(args.rtl).resolve()
    spec_path = Path(args.spec).resolve()
    csr_map_path = Path(args.csr_map).resolve()
    output_dir = Path(args.output_dir).resolve()

    orchestrator = AutoVerifierOrchestrator(config=config)
    orchestrator.run(
        rtl_path=rtl_path,
        spec_path=spec_path,
        csr_map_path=csr_map_path,
        output_dir=output_dir,
        simulator_mode=str(args.simulator),
        max_iterations=int(agent_cfg.get("max_iterations", 4)),
        max_repair_generations_per_iteration=int(
            agent_cfg.get("max_repair_generations_per_iteration", 1)
        ),
        iteration_mode=str(agent_cfg.get("iteration_mode", "auto")),
        min_iterations=int(agent_cfg.get("min_iterations", 4)),
        timeout_minutes=float(agent_cfg.get("timeout_minutes", 0.0)),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
