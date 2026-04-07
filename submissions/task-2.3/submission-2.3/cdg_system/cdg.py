"""Task 2.3 CDG core interface implementation.

Implements the required interface:
- generate(iteration, coverage_state) -> Stimulus
- adjust(iteration, new_coverage, cumulative_coverage)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .constraint_tuner import ReinforcementConstraintTuner, PolicyUpdateResult
from .coverage_analyzer import CoverageAnalyzer, CoverageMetrics
from .generator import Stimulus, StimulusGenerator


@dataclass
class CoverageReport:
    iteration: int
    cycles_used: int
    line_coverage: float
    branch_coverage: float
    toggle_coverage: float
    functional_coverage: float
    uncovered_targets: list[str] = field(default_factory=list)

    @property
    def combined_coverage(self) -> float:
        return (
            self.line_coverage + self.branch_coverage + self.functional_coverage
        ) / 3.0


@dataclass
class CoverageState:
    history: list[CoverageReport] = field(default_factory=list)


class CDGSystem:
    """Hybrid B+C CDG strategy controller."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.analyzer = CoverageAnalyzer()
        self.tuner = ReinforcementConstraintTuner(
            learning_rate=float(config.get("learning_rate", 0.12)),
            floor=float(config.get("prob_floor", 0.03)),
            ceiling=float(config.get("prob_ceiling", 0.92)),
        )
        self.generator = StimulusGenerator(seed=int(config.get("seed", 2026)))

        self.policy: dict[str, dict[str, float]] = {
            "msg_len_profile": {
                "zero": 0.10,
                "short": 0.45,
                "medium": 0.30,
                "long": 0.15,
            },
            "intr_pattern": {"none": 0.40, "enable": 0.20, "test": 0.20, "both": 0.20},
            "burst_count": {"1": 0.38, "2": 0.30, "3": 0.20, "4": 0.12},
            "chunking": {"1": 0.35, "4": 0.30, "8": 0.20, "16": 0.15},
        }

        self.reward_weights = {
            "line": float(config.get("reward_line", 0.35)),
            "branch": float(config.get("reward_branch", 0.45)),
            "functional": float(config.get("reward_functional", 0.20)),
        }

        self.focus_queue: list[str] = list(config.get("focus_targets", []))
        self.last_stimulus: Stimulus | None = None
        self.strategy_evolution: list[dict[str, Any]] = []

    def generate(self, iteration: int, coverage_state: CoverageState) -> Stimulus:
        """Produce stimulus for the next simulation run."""
        if coverage_state.history:
            latest = coverage_state.history[-1]
            ranked = self.analyzer.rank_focus_targets(latest.uncovered_targets)
            if ranked:
                self.focus_queue = ranked

        focus_target = (
            self.focus_queue[0] if self.focus_queue else "global:coverage_efficiency"
        )
        target_cycles = int(self.config.get("cycles_per_iteration", 8000))

        stimulus = self.generator.generate(
            iteration=iteration,
            target_cycles=target_cycles,
            focus_target=focus_target,
            policy=self.policy,
        )
        self.last_stimulus = stimulus
        return stimulus

    def adjust(
        self,
        iteration: int,
        new_coverage: CoverageReport,
        cumulative_coverage: CoverageState,
    ) -> None:
        """Update strategy policy from latest coverage outcome."""
        if self.last_stimulus is None:
            return

        prev = (
            cumulative_coverage.history[-2]
            if len(cumulative_coverage.history) >= 2
            else None
        )
        prev_line = prev.line_coverage if prev else 0.0
        prev_branch = prev.branch_coverage if prev else 0.0
        prev_func = prev.functional_coverage if prev else 0.0

        delta_line = max(0.0, new_coverage.line_coverage - prev_line)
        delta_branch = max(0.0, new_coverage.branch_coverage - prev_branch)
        delta_func = max(0.0, new_coverage.functional_coverage - prev_func)

        reward = (
            self.reward_weights["line"] * (delta_line / 100.0)
            + self.reward_weights["branch"] * (delta_branch / 100.0)
            + self.reward_weights["functional"] * (delta_func / 100.0)
        )

        update: PolicyUpdateResult = self.tuner.update_policy(
            policy=self.policy,
            selected_knobs=self.last_stimulus.selected_knobs,
            reward=reward,
            focus_targets=self.analyzer.rank_focus_targets(
                new_coverage.uncovered_targets
            ),
        )

        self.strategy_evolution.append(
            {
                "iteration": iteration,
                "focus_target": self.last_stimulus.focus_target,
                "selected_knobs": dict(self.last_stimulus.selected_knobs),
                "coverage": {
                    "line": new_coverage.line_coverage,
                    "branch": new_coverage.branch_coverage,
                    "functional": new_coverage.functional_coverage,
                    "combined": new_coverage.combined_coverage,
                },
                "delta": {
                    "line": delta_line,
                    "branch": delta_branch,
                    "functional": delta_func,
                },
                "reward": update.reward,
                "reward_clamped": update.reward_clamped,
                "policy_after": {k: dict(v) for k, v in self.policy.items()},
                "focus_targets_after": list(update.focus_targets),
            }
        )


def to_report(
    iteration: int, cycles_used: int, metrics: CoverageMetrics
) -> CoverageReport:
    """Convert analyzer metrics to CoverageReport."""
    return CoverageReport(
        iteration=iteration,
        cycles_used=cycles_used,
        line_coverage=metrics.line,
        branch_coverage=metrics.branch,
        toggle_coverage=metrics.toggle,
        functional_coverage=metrics.functional,
        uncovered_targets=list(metrics.uncovered_targets),
    )


def report_to_dict(report: CoverageReport) -> dict[str, Any]:
    data = asdict(report)
    data["combined_coverage"] = report.combined_coverage
    return data
