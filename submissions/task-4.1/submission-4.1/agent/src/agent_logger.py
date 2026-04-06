from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from io_utils import utc_now_iso


@dataclass
class LLMStats:
    total_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_usd: float = 0.0


class AgentLogger:
    """Structured execution log writer for Task 4.1 agent runs."""

    def __init__(self) -> None:
        self._start_wall = time.time()
        self._step = 0
        self.metadata: dict = {
            "agent_name": "task_4_1_autoverifier",
            "start_time": utc_now_iso(),
            "end_time": "",
            "total_duration_seconds": 0,
            "llm_provider": "none",
            "llm_model": "none",
            "total_llm_calls": 0,
            "total_tokens_used": 0,
            "estimated_cost_usd": 0.0,
        }
        self.actions: list[dict] = []

    def set_llm_identity(self, provider: str, model: str) -> None:
        self.metadata["llm_provider"] = provider
        self.metadata["llm_model"] = model

    def record_action(
        self,
        *,
        stage: str,
        action: str,
        duration_seconds: float,
        input_summary: str,
        output_summary: str,
        llm_call: bool = False,
        model: str = "",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        requested_reasoning_effort: str = "",
        effective_reasoning_effort: str = "",
    ) -> None:
        self._step += 1
        self.actions.append(
            {
                "step": self._step,
                "stage": stage,
                "action": action,
                "timestamp": utc_now_iso(),
                "duration_seconds": round(duration_seconds, 3),
                "duration_ms": int(round(duration_seconds * 1000.0)),
                "input_summary": input_summary,
                "output_summary": output_summary,
                "summary": output_summary,
                "llm_call": llm_call,
                "model": model,
                "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(completion_tokens),
                "requested_reasoning_effort": requested_reasoning_effort,
                "effective_reasoning_effort": effective_reasoning_effort,
            }
        )

    def finalize(self, output_path: Path, stats: LLMStats) -> None:
        self.metadata["end_time"] = utc_now_iso()
        self.metadata["total_duration_seconds"] = int(time.time() - self._start_wall)
        self.metadata["total_llm_calls"] = int(stats.total_calls)
        self.metadata["total_tokens_used"] = int(
            stats.prompt_tokens + stats.completion_tokens
        )
        self.metadata["estimated_cost_usd"] = float(round(stats.estimated_cost_usd, 6))

        llm_api_calls = []
        for entry in self.actions:
            if not bool(entry.get("llm_call", False)):
                continue
            llm_api_calls.append(
                {
                    "timestamp": entry.get("timestamp", ""),
                    "action": entry.get("action", ""),
                    "model": entry.get("model", ""),
                    "prompt_tokens": int(entry.get("prompt_tokens", 0) or 0),
                    "completion_tokens": int(entry.get("completion_tokens", 0) or 0),
                    "requested_reasoning_effort": entry.get(
                        "requested_reasoning_effort", ""
                    ),
                    "effective_reasoning_effort": entry.get(
                        "effective_reasoning_effort", ""
                    ),
                    "duration_ms": int(entry.get("duration_ms", 0) or 0),
                    "summary": entry.get("summary", ""),
                }
            )

        payload = {
            "metadata": self.metadata,
            "llm_api_calls": llm_api_calls,
            "actions": self.actions,
        }
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
