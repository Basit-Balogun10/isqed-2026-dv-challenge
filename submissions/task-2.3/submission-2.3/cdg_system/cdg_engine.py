"""Task 2.3 CDG engine runner.

CLI (required by submission requirements):
python cdg_system/cdg_engine.py --dut <dut_id> --budget 100000 --output results/
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml  # type: ignore[import-untyped]

# Support direct execution: python cdg_system/cdg_engine.py
if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cdg_system.cdg import CDGSystem, CoverageState, report_to_dict, to_report
from cdg_system.coverage_analyzer import CoverageAnalyzer, CoverageMetrics
from cdg_system.generator import StimulusGenerator


class _NoAliasSafeDumper(yaml.SafeDumper):
    """Dumper variant that disables YAML anchors for repeated structures."""

    def ignore_aliases(self, data: Any) -> bool:
        return True


def _dump_yaml_no_alias(payload: Any) -> str:
    return yaml.dump(payload, Dumper=_NoAliasSafeDumper, sort_keys=False)


def _run_command(command: list[str], cwd: Path, env: dict[str, str]) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _resolve_results_dir(submission_root: Path, output_arg: str) -> Path:
    output_path = Path(output_arg)
    if not output_path.is_absolute():
        output_path = (submission_root / output_path).resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def _ensure_dirs(root: Path) -> tuple[Path, Path]:
    logs_dir = root / "logs"
    stimulus_dir = root / "cdg_system" / "generated"
    logs_dir.mkdir(parents=True, exist_ok=True)
    stimulus_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir, stimulus_dir


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Task 2.3 CDG loop")
    parser.add_argument("--dut", default="sentinel_hmac", help="Target DUT ID")
    parser.add_argument("--budget", type=int, default=100000, help="Cycle budget")
    parser.add_argument("--output", default="results", help="Output directory")
    parser.add_argument(
        "--iterations", type=int, default=12, help="Number of adaptive iterations"
    )
    parser.add_argument(
        "--sim", default="verilator", choices=["icarus", "verilator"], help="Simulator"
    )
    parser.add_argument("--seed", type=int, default=2026, help="Random seed")
    return parser.parse_args()


def _load_config(config_path: Path, args: argparse.Namespace) -> dict[str, Any]:
    base: dict[str, Any] = {}
    if config_path.exists():
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            base = loaded

    base["seed"] = int(args.seed)
    base["iterations"] = max(10, int(args.iterations))
    base["budget_cycles"] = int(args.budget)
    base["cycles_per_iteration"] = max(
        1000, int(args.budget) // max(10, int(args.iterations))
    )
    base["dut"] = str(args.dut)
    base["sim"] = str(args.sim)
    return base


def _run_iteration(
    submission_root: Path,
    sim: str,
    stimulus_path: Path,
    iteration: int,
    logs_dir: Path,
) -> tuple[CoverageMetrics, str]:
    env = os.environ.copy()
    env["STIMULUS_FILE"] = str(stimulus_path)
    env["FUNC_COV_OUT"] = str(logs_dir / f"functional_cov_iter_{iteration:02d}.txt")

    # Clean per-iteration coverage artifacts for deterministic parsing.
    for rel in [
        "coverage.dat",
        "coverage_line.info",
        "coverage_branch.info",
        "coverage_toggle.info",
    ]:
        path = submission_root / rel
        if path.exists():
            path.unlink()

    cmd = [
        "make",
        "--no-print-directory",
        "SIM=" + sim,
        "COCOTB_TEST_MODULES=tests.test_cdg_generated",
        "EXTRA_ARGS=--coverage --coverage-line --coverage-toggle --coverage-expr",
        "sim",
    ]
    rc, output = _run_command(cmd, submission_root, env)
    (logs_dir / f"sim_iter_{iteration:02d}.log").write_text(output, encoding="utf-8")

    if rc != 0:
        # Graceful fallback keeps loop alive (required for >=10 autonomous iterations).
        return CoverageMetrics(), f"simulation_failed_rc_{rc}"

    # Extract typed coverage info files.
    for cov_type, out_name in [
        ("line", "coverage_line.info"),
        ("branch", "coverage_branch.info"),
        ("toggle", "coverage_toggle.info"),
    ]:
        cov_cmd = [
            "verilator_coverage",
            "--filter-type",
            cov_type,
            "--write-info",
            out_name,
            "coverage.dat",
        ]
        rc_cov, _ = _run_command(cov_cmd, submission_root, env)
        if rc_cov != 0:
            # Non-fatal; parser will handle missing files.
            pass

    analyzer = CoverageAnalyzer()
    metrics = analyzer.parse_metrics(
        line_info=submission_root / "coverage_line.info",
        branch_info=submission_root / "coverage_branch.info",
        toggle_info=submission_root / "coverage_toggle.info",
        functional_report=Path(env["FUNC_COV_OUT"]),
    )
    return metrics, "ok"


def _write_submission_convergence_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "iteration",
        "cycles_used",
        "line_coverage",
        "branch_coverage",
        "functional_coverage",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def _write_curve_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "iteration",
        "cycles_used",
        "line_coverage",
        "branch_coverage",
        "functional_coverage",
        "combined_coverage",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def _write_final_reports(results_dir: Path, history: list[dict[str, Any]]) -> None:
    latest = (
        history[-1]
        if history
        else {
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "toggle_coverage": 0.0,
            "functional_coverage": 0.0,
            "combined_coverage": 0.0,
            "cycles_used": 0,
        }
    )
    latest_toggle = float(latest.get("toggle_coverage", 0.0))

    final_txt = results_dir / "final_coverage.txt"
    final_txt.write_text(
        "\n".join(
            [
                f"line_coverage: {latest['line_coverage']:.2f}",
                f"branch_coverage: {latest['branch_coverage']:.2f}",
                f"toggle_coverage: {latest_toggle:.2f}",
                f"functional_coverage: {latest['functional_coverage']:.2f}",
                f"combined_coverage: {latest['combined_coverage']:.2f}",
                f"cycles_used: {latest['cycles_used']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    final_html = results_dir / "final_coverage.html"
    final_html.write_text(
        """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Task 2.3 Final Coverage</title></head>
<body>
  <h1>Task 2.3 Final Coverage</h1>
  <ul>
    <li>Line: {line:.2f}%</li>
    <li>Branch: {branch:.2f}%</li>
    <li>Toggle: {toggle:.2f}%</li>
    <li>Functional: {functional:.2f}%</li>
    <li>Combined (line+branch+functional)/3: {combined:.2f}%</li>
    <li>Cycles Used: {cycles}</li>
  </ul>
</body>
</html>
""".format(
            line=latest["line_coverage"],
            branch=latest["branch_coverage"],
            toggle=latest_toggle,
            functional=latest["functional_coverage"],
            combined=latest["combined_coverage"],
            cycles=latest["cycles_used"],
        ),
        encoding="utf-8",
    )


def _combined(row: dict[str, Any]) -> float:
    return (
        float(row["line_coverage"])
        + float(row["branch_coverage"])
        + float(row["functional_coverage"])
    ) / 3.0


def _auc(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    area = 0.0
    prev_x = 0.0
    prev_y = 0.0
    for row in rows:
        x = float(row["cycles_used"])
        y = _combined(row)
        dx = max(0.0, x - prev_x)
        area += (prev_y + y) * dx * 0.5
        prev_x = x
        prev_y = y
    return area


def _write_baseline_comparison(
    results_dir: Path,
    adaptive_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
) -> None:
    adaptive_auc = _auc(adaptive_rows)
    baseline_auc = _auc(baseline_rows)
    auc_ratio = adaptive_auc / baseline_auc if baseline_auc > 0 else 0.0

    adaptive_final = _combined(adaptive_rows[-1]) if adaptive_rows else 0.0
    baseline_final = _combined(baseline_rows[-1]) if baseline_rows else 0.0

    baseline_note = results_dir / "baseline_comparison.md"
    baseline_note.write_text(
        "\n".join(
            [
                "# Baseline Comparison",
                "",
                "This report compares adaptive CDG against a fixed-policy static baseline ",
                "using equal iteration count and cycle budget.",
                "",
                f"Adaptive AUC (combined coverage vs cycles): {adaptive_auc:.2f}",
                f"Baseline AUC (combined coverage vs cycles): {baseline_auc:.2f}",
                f"Efficiency ratio (adaptive / baseline): {auc_ratio:.4f}",
                "",
                f"Adaptive final combined coverage: {adaptive_final:.2f}%",
                f"Baseline final combined coverage: {baseline_final:.2f}%",
                "",
                "Interpretation:",
                "- Ratio > 1.0 means adaptive loop outperformed fixed static policy.",
                "- Ratio < 1.0 means static policy performed better for this run.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = _parse_args()

    submission_root = Path(__file__).resolve().parents[1]
    results_dir = _resolve_results_dir(submission_root, args.output)
    logs_dir, stimulus_dir = _ensure_dirs(submission_root)

    config = _load_config(submission_root / "cdg_system" / "config.yaml", args)
    system = CDGSystem(config)
    state = CoverageState()

    convergence_rows: list[dict[str, Any]] = []
    iteration_log: list[dict[str, Any]] = []

    iterations = int(config["iterations"])
    cycles_per_iteration = int(config["cycles_per_iteration"])

    for iteration in range(iterations):
        stimulus = system.generate(iteration=iteration, coverage_state=state)
        stimulus_path = stimulus_dir / f"stimulus_iter_{iteration:02d}.json"
        _write_json(
            stimulus_path,
            {
                "seed": stimulus.seed,
                "iteration": stimulus.iteration,
                "target_cycles": stimulus.target_cycles,
                "focus_target": stimulus.focus_target,
                "selected_knobs": stimulus.selected_knobs,
                "transactions": stimulus.transactions,
            },
        )

        metrics, run_status = _run_iteration(
            submission_root=submission_root,
            sim=str(config["sim"]),
            stimulus_path=stimulus_path,
            iteration=iteration,
            logs_dir=logs_dir,
        )

        cycles_used = (iteration + 1) * cycles_per_iteration
        report = to_report(
            iteration=iteration + 1, cycles_used=cycles_used, metrics=metrics
        )
        state.history.append(report)
        system.adjust(
            iteration=iteration + 1, new_coverage=report, cumulative_coverage=state
        )

        row = {
            "iteration": report.iteration,
            "cycles_used": report.cycles_used,
            "line_coverage": round(report.line_coverage, 2),
            "branch_coverage": round(report.branch_coverage, 2),
            "toggle_coverage": round(report.toggle_coverage, 2),
            "functional_coverage": round(report.functional_coverage, 2),
            "combined_coverage": round(report.combined_coverage, 2),
        }
        convergence_rows.append(row)

        iteration_log.append(
            {
                "iteration": report.iteration,
                "run_status": run_status,
                "stimulus_file": str(stimulus_path.relative_to(submission_root)),
                "stimulus": {
                    "focus_target": stimulus.focus_target,
                    "selected_knobs": stimulus.selected_knobs,
                    "transaction_count": len(stimulus.transactions),
                },
                "coverage": report_to_dict(report),
                "policy_after": {k: dict(v) for k, v in system.policy.items()},
            }
        )

    # Static baseline (fixed policy, no adaptation) for measurable-improvement evidence.
    baseline_generator = StimulusGenerator(seed=int(config.get("seed", 2026)) + 1000)
    baseline_system = CDGSystem(config)
    baseline_policy = {k: dict(v) for k, v in baseline_system.policy.items()}
    baseline_rows: list[dict[str, Any]] = []

    for iteration in range(iterations):
        baseline_stimulus = baseline_generator.generate(
            iteration=iteration,
            target_cycles=cycles_per_iteration,
            focus_target="baseline:uniform_random",
            policy=baseline_policy,
        )
        baseline_stimulus_path = (
            stimulus_dir / f"stimulus_baseline_iter_{iteration:02d}.json"
        )
        _write_json(
            baseline_stimulus_path,
            {
                "seed": baseline_stimulus.seed,
                "iteration": baseline_stimulus.iteration,
                "target_cycles": baseline_stimulus.target_cycles,
                "focus_target": baseline_stimulus.focus_target,
                "selected_knobs": baseline_stimulus.selected_knobs,
                "transactions": baseline_stimulus.transactions,
            },
        )

        baseline_metrics, _ = _run_iteration(
            submission_root=submission_root,
            sim=str(config["sim"]),
            stimulus_path=baseline_stimulus_path,
            iteration=iteration + 100,  # avoid filename collisions in functional logs
            logs_dir=logs_dir,
        )
        baseline_cycles = (iteration + 1) * cycles_per_iteration
        baseline_report = to_report(
            iteration=iteration + 1,
            cycles_used=baseline_cycles,
            metrics=baseline_metrics,
        )
        baseline_rows.append(
            {
                "iteration": baseline_report.iteration,
                "cycles_used": baseline_report.cycles_used,
                "line_coverage": round(baseline_report.line_coverage, 2),
                "branch_coverage": round(baseline_report.branch_coverage, 2),
                "functional_coverage": round(baseline_report.functional_coverage, 2),
                "combined_coverage": round(baseline_report.combined_coverage, 2),
            }
        )

    # Required by submission_requirements.md
    _write_submission_convergence_csv(
        results_dir / "convergence_log.csv", convergence_rows
    )
    _write_final_reports(results_dir, convergence_rows)
    _write_baseline_comparison(results_dir, convergence_rows, baseline_rows)

    # Required by task page observability
    _write_curve_csv(logs_dir / "coverage_curve.csv", convergence_rows)
    _write_curve_csv(logs_dir / "baseline_curve.csv", baseline_rows)
    (logs_dir / "iteration_log.yaml").write_text(
        _dump_yaml_no_alias(iteration_log), encoding="utf-8"
    )
    (logs_dir / "strategy_evolution.yaml").write_text(
        _dump_yaml_no_alias(system.strategy_evolution),
        encoding="utf-8",
    )

    print(
        f"[CDG] Completed {iterations} iterations for DUT={config['dut']} SIM={config['sim']}"
    )
    print(f"[CDG] Results written to {results_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
