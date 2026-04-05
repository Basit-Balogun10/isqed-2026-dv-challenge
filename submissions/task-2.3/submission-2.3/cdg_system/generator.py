"""Stimulus generator for Task 2.3 CDG."""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Dict, Mapping


@dataclass
class Stimulus:
    """Generated stimulus plan consumed by tests/test_cdg_generated.py."""

    seed: int
    iteration: int
    target_cycles: int
    focus_target: str
    selected_knobs: Dict[str, str]
    transactions: list[dict]


class StimulusGenerator:
    """Samples constrained-random stimulus from adaptive policy distributions."""

    def __init__(self, seed: int):
        self._rng = random.Random(seed)

    def generate(
        self,
        iteration: int,
        target_cycles: int,
        focus_target: str,
        policy: Mapping[str, Mapping[str, float]],
    ) -> Stimulus:
        msg_len_profile = self._sample(policy["msg_len_profile"])
        intr_pattern = self._sample(policy["intr_pattern"])
        burst_count = int(self._sample(policy["burst_count"]))
        chunking = int(self._sample(policy["chunking"]))

        transactions: list[dict] = []
        for tx_id in range(burst_count):
            msg_len = self._choose_msg_length(msg_len_profile)
            tx_seed = self._rng.randint(1, 2**31 - 1)
            transactions.append(
                {
                    "id": tx_id,
                    "msg_len": msg_len,
                    "intr_pattern": intr_pattern,
                    "chunking": chunking,
                    "tx_seed": tx_seed,
                    "pattern": self._sample_payload_pattern(focus_target),
                }
            )

        return Stimulus(
            seed=self._rng.randint(1, 2**31 - 1),
            iteration=iteration,
            target_cycles=target_cycles,
            focus_target=focus_target,
            selected_knobs={
                "msg_len_profile": msg_len_profile,
                "intr_pattern": intr_pattern,
                "burst_count": str(burst_count),
                "chunking": str(chunking),
            },
            transactions=transactions,
        )

    def _sample(self, probabilities: Mapping[str, float]) -> str:
        roll = self._rng.random()
        cumulative = 0.0
        items = list(probabilities.items())
        for value, prob in items:
            cumulative += prob
            if roll <= cumulative:
                return value
        return items[-1][0]

    def _choose_msg_length(self, profile: str) -> int:
        if profile == "zero":
            return 0
        if profile == "short":
            return self._rng.choice([1, 4, 8, 12, 16])
        if profile == "medium":
            return self._rng.choice([24, 32, 40, 48])
        return self._rng.choice([64, 80, 96, 112, 128])

    def _sample_payload_pattern(self, focus_target: str) -> str:
        if "intr_write_kind" in focus_target:
            return self._rng.choice(["walking_ones", "alternating"])
        if "msg_len_bucket" in focus_target:
            return self._rng.choice(["incremental", "all_zero", "all_ff"])
        return self._rng.choice(["incremental", "all_zero", "all_ff", "alternating"])
