from __future__ import annotations

import re
import time
from dataclasses import dataclass

from agent_logger import AgentLogger, LLMStats


@dataclass
class LLMResult:
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    requested_reasoning_effort: str
    effective_reasoning_effort: str


class LLMProvider:
    """Strict OpenAI provider for Task 4.3 with fixed model policy."""

    def __init__(self, config: dict, logger: AgentLogger | None = None) -> None:
        import os

        llm_cfg = config.get("llm", {})
        self.mode = str(llm_cfg.get("mode", "online"))
        self.provider = str(llm_cfg.get("provider", "openai"))
        self.primary_model = str(llm_cfg.get("primary_model", "gpt-5.4-mini"))
        self.primary_reasoning_effort = str(
            llm_cfg.get("primary_reasoning_effort", "xhigh")
        )
        self.max_total_calls = int(llm_cfg.get("max_total_calls", 80))
        self.temperature = float(llm_cfg.get("temperature", 0.1))
        self.timeout_seconds = int(llm_cfg.get("timeout_seconds", 90))
        self.input_cost_per_1m_tokens_usd = float(
            llm_cfg.get("input_cost_per_1m_tokens_usd", 0.25)
        )
        self.output_cost_per_1m_tokens_usd = float(
            llm_cfg.get("output_cost_per_1m_tokens_usd", 2.0)
        )

        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required for Task 4.3 online mode. "
                "Set OPENAI_API_KEY in the environment before running the agent."
            )

        if self.provider.lower().strip() != "openai":
            raise RuntimeError("Only provider=openai is supported in Task 4.3")

        self.logger = logger
        self.stats = LLMStats()
        self.provider_name = "openai"

    def generate(
        self,
        *,
        stage: str,
        system_prompt: str,
        user_prompt: str,
    ) -> LLMResult:
        if self.stats.total_calls >= self.max_total_calls:
            raise RuntimeError(
                f"Max LLM call budget reached ({self.max_total_calls}). "
                "Increase max_total_calls in config if needed."
            )

        start = time.monotonic()
        result = self._call_openai(
            model=self.primary_model,
            requested_effort=self.primary_reasoning_effort,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        self.stats.total_calls += 1
        self.stats.prompt_tokens += result.prompt_tokens
        self.stats.completion_tokens += result.completion_tokens
        estimated_call_cost = (
            (result.prompt_tokens / 1_000_000.0) * self.input_cost_per_1m_tokens_usd
            + (result.completion_tokens / 1_000_000.0)
            * self.output_cost_per_1m_tokens_usd
        )
        self.stats.estimated_cost_usd += estimated_call_cost

        if self.logger is not None:
            prompt_preview = user_prompt[:500].replace("\n", " ").strip()
            response_preview = result.text[:500].replace("\n", " ").strip()
            self.logger.record_action(
                stage=stage,
                action="llm_api_call",
                duration_seconds=time.monotonic() - start,
                input_summary=(
                    "provider=openai; "
                    f"requested_reasoning_effort={result.requested_reasoning_effort}; "
                    f"prompt_preview={prompt_preview}"
                ),
                output_summary=(
                    f"provider=openai; model={result.model}; "
                    f"estimated_call_cost_usd={estimated_call_cost:.6f}; "
                    f"response_preview={response_preview}"
                ),
                llm_call=True,
                model=result.model,
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                requested_reasoning_effort=result.requested_reasoning_effort,
                effective_reasoning_effort=result.effective_reasoning_effort,
            )

        return result

    def generate_json(
        self,
        *,
        stage: str,
        system_prompt: str,
        user_prompt: str,
    ) -> dict:
        result = self.generate(
            stage=stage,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        parsed = self._extract_json_dict(result.text)
        if parsed is not None:
            return parsed

        repair_prompt = (
            "The previous response was not strict JSON. "
            "Return only valid JSON that matches the requested schema.\n\n"
            f"Previous response:\n{result.text[:12000]}"
        )
        repaired = self.generate(
            stage=f"{stage}_json_repair",
            system_prompt="Return strict JSON only. No markdown.",
            user_prompt=repair_prompt,
        )
        parsed = self._extract_json_dict(repaired.text)
        if parsed is None:
            raise RuntimeError("Failed to parse model output as JSON")
        return parsed

    def _call_openai(
        self,
        *,
        model: str,
        requested_effort: str,
        system_prompt: str,
        user_prompt: str,
    ) -> LLMResult:
        from openai import OpenAI

        # Keep runtime predictable for judged dry-runs by avoiding hidden client retries.
        client = OpenAI(
            api_key=self.api_key,
            timeout=self.timeout_seconds,
            max_retries=0,
        )
        prompt_tokens = 0
        completion_tokens = 0

        request_kwargs: dict = {
            "model": model,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "reasoning": {"effort": requested_effort},
        }
        # Some GPT-5 family models reject temperature; omit it for compatibility.
        if not model.lower().startswith("gpt-5"):
            request_kwargs["temperature"] = self.temperature

        response = client.responses.create(**request_kwargs)  # type: ignore[call-overload]
        text = getattr(response, "output_text", "") or ""
        usage = getattr(response, "usage", None)
        if usage is not None:
            prompt_tokens = int(getattr(usage, "input_tokens", 0) or 0)
            completion_tokens = int(getattr(usage, "output_tokens", 0) or 0)

        return LLMResult(
            text=text.strip() or "{}",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            requested_reasoning_effort=requested_effort,
            effective_reasoning_effort=requested_effort,
        )

    def _extract_json_dict(self, text: str) -> dict | None:
        import json

        candidate = text.strip()
        if not candidate:
            return None

        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", candidate, flags=re.DOTALL)
        if not match:
            return None

        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
