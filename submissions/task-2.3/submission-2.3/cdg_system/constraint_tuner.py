"""Constraint-tuning logic for Task 2.3 CDG.

Implements a lightweight reinforcement-style policy update:
- Reward productive stimulus settings that increase coverage
- Decay unproductive settings
- Apply target-specific boosts for uncovered functional bins
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping


def _renormalize(probabilities: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(v, 0.0) for v in probabilities.values())
    if total <= 0.0:
        # Safe fallback to uniform probabilities.
        uniform = 1.0 / max(len(probabilities), 1)
        return {k: uniform for k in probabilities}
    return {k: max(v, 0.0) / total for k, v in probabilities.items()}


@dataclass
class PolicyUpdateResult:
    """Captures policy updates for observability logs."""

    reward: float
    reward_clamped: float
    touched_knobs: Dict[str, str]
    focus_targets: list[str]


class ReinforcementConstraintTuner:
    """Hybrid B+C tuning backend used by CDGSystem.

    Approach B:
    - Uses reward to increase/decrease selected knob probabilities.

    Approach C:
    - Uses uncovered target hints to bias knobs toward likely useful values.
    """

    def __init__(self, learning_rate: float = 0.12, floor: float = 0.03, ceiling: float = 0.92):
        self.learning_rate = learning_rate
        self.floor = floor
        self.ceiling = ceiling

    def _bounded(self, value: float) -> float:
        return min(self.ceiling, max(self.floor, value))

    def update_policy(
        self,
        policy: Dict[str, Dict[str, float]],
        selected_knobs: Mapping[str, str],
        reward: float,
        focus_targets: Iterable[str],
    ) -> PolicyUpdateResult:
        """Apply reward and target-driven updates to the policy in-place."""
        reward_clamped = max(-1.0, min(1.0, reward))
        focus_targets = list(focus_targets)

        # Reward/punish selected values.
        for knob_name, selected_value in selected_knobs.items():
            knob_probs = policy.get(knob_name)
            if not knob_probs or selected_value not in knob_probs:
                continue

            for value_name in list(knob_probs.keys()):
                current = knob_probs[value_name]
                if value_name == selected_value:
                    delta = self.learning_rate * reward_clamped
                else:
                    # Slight opposite move for competing bins.
                    delta = -0.5 * self.learning_rate * reward_clamped / max(len(knob_probs) - 1, 1)
                knob_probs[value_name] = self._bounded(current + delta)

            policy[knob_name] = _renormalize(knob_probs)

        # Coverage-point targeting boosts (Approach C).
        targets_text = " ".join(focus_targets)
        if "intr_write_kind" in targets_text:
            self._boost(policy, "intr_pattern", ["test", "both"], 0.06)
        if "msg_len_bucket" in targets_text:
            if "long" in targets_text:
                self._boost(policy, "msg_len_profile", ["long"], 0.07)
            elif "short" in targets_text:
                self._boost(policy, "msg_len_profile", ["short"], 0.05)
        if "msg_len_nonzero" in targets_text:
            self._boost(policy, "msg_len_profile", ["short", "medium", "long"], 0.04)

        return PolicyUpdateResult(
            reward=reward,
            reward_clamped=reward_clamped,
            touched_knobs=dict(selected_knobs),
            focus_targets=focus_targets,
        )

    def _boost(
        self,
        policy: Dict[str, Dict[str, float]],
        knob_name: str,
        boosted_values: list[str],
        delta: float,
    ) -> None:
        knob_probs = policy.get(knob_name)
        if not knob_probs:
            return

        for value in boosted_values:
            if value in knob_probs:
                knob_probs[value] = self._bounded(knob_probs[value] + delta)

        policy[knob_name] = _renormalize(knob_probs)
