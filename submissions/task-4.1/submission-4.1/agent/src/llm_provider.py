from __future__ import annotations

import os
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
    """Strict OpenAI provider with no local or deterministic fallback."""

    def __init__(self, config: dict, logger: AgentLogger | None = None) -> None:
        llm_cfg = config.get("llm", {})

        self.mode = str(llm_cfg.get("mode", "online"))
        self.provider = str(llm_cfg.get("provider", "openai"))
        self.primary_model = str(llm_cfg.get("primary_model", "gpt-5.4-mini"))
        self.primary_reasoning_effort = str(
            llm_cfg.get("primary_reasoning_effort", "xhigh")
        )
        self.escalation_model = str(llm_cfg.get("escalation_model", "gpt-5.4"))
        self.escalation_reasoning_effort = str(
            llm_cfg.get("escalation_reasoning_effort", "xhigh")
        )
        self.judge_min_score = int(llm_cfg.get("judge_min_score", 80))
        self.max_total_calls = int(llm_cfg.get("max_total_calls", 60))
        self.temperature = float(llm_cfg.get("temperature", 0.1))
        self.timeout_seconds = int(llm_cfg.get("timeout_seconds", 90))

        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required for Task 4.1 online mode. "
                "Set OPENAI_API_KEY in the environment before running the agent."
            )

        if self.provider.lower().strip() != "openai":
            raise RuntimeError(
                "Only provider=openai is supported in strict online mode."
            )

        self.logger = logger
        self.stats = LLMStats()
        self.provider_name, _ = self.identity()

    def identity(self) -> tuple[str, str]:
        return ("openai", self.primary_model)

    def can_escalate(self) -> bool:
        if self.escalation_model == self.primary_model:
            return False
        return self.stats.total_calls < self.max_total_calls

    def generate_with_quality_gate(
        self,
        *,
        stage: str,
        system_prompt: str,
        user_prompt: str,
        min_score: int | None = None,
    ) -> tuple[LLMResult, int, bool]:
        target_score = self.judge_min_score if min_score is None else min_score
        primary = self.generate(
            stage=stage,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            escalated=False,
        )

        primary_score = self._judge(
            stage=stage, prompt=user_prompt, candidate=primary.text
        )
        if primary_score >= target_score or not self.can_escalate():
            return (primary, primary_score, False)

        # Escalation step: stronger model (gpt-5.4) at configured effort.
        upgraded = self.generate(
            stage=stage,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            escalated=True,
        )
        upgraded_score = self._judge(
            stage=stage, prompt=user_prompt, candidate=upgraded.text
        )

        if upgraded_score >= primary_score:
            return (upgraded, upgraded_score, True)
        return (primary, primary_score, False)

    def generate(
        self,
        *,
        stage: str,
        system_prompt: str,
        user_prompt: str,
        escalated: bool = False,
        force_effort: str | None = None,
    ) -> LLMResult:
        model = self.escalation_model if escalated else self.primary_model
        requested_effort = str(force_effort or "").strip() or (
            self.escalation_reasoning_effort
            if escalated
            else self.primary_reasoning_effort
        )
        call_start = time.monotonic()

        if self.stats.total_calls >= self.max_total_calls:
            raise RuntimeError(
                f"Max LLM call budget reached ({self.max_total_calls}). "
                "Increase max_total_calls in config for longer runs."
            )

        try:
            result = self._call_openai(
                model=model,
                requested_effort=requested_effort,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            self.stats.total_calls += 1
            self.stats.prompt_tokens += result.prompt_tokens
            self.stats.completion_tokens += result.completion_tokens

            if (
                self.logger is not None
                and result.requested_reasoning_effort
                != result.effective_reasoning_effort
            ):
                self.logger.record_action(
                    stage=stage,
                    action="reasoning_effort_fallback",
                    duration_seconds=0.0,
                    input_summary=f"requested_reasoning_effort={result.requested_reasoning_effort}",
                    output_summary=f"effective_reasoning_effort={result.effective_reasoning_effort}",
                    llm_call=False,
                    model=model,
                )

            self._record_call(
                stage=stage,
                user_prompt=user_prompt,
                result=result,
                escalated=escalated,
                duration_seconds=time.monotonic() - call_start,
            )
            return result
        except Exception as exc:
            self._record_failure(
                stage=stage,
                user_prompt=user_prompt,
                model=model,
                escalated=escalated,
                requested_effort=requested_effort,
                duration_seconds=time.monotonic() - call_start,
                error_text=str(exc),
            )
            raise RuntimeError(
                f"OpenAI API call failed at stage {stage}: {exc}"
            ) from exc

    def _record_failure(
        self,
        *,
        stage: str,
        user_prompt: str,
        model: str,
        escalated: bool,
        requested_effort: str,
        duration_seconds: float,
        error_text: str,
    ) -> None:
        if self.logger is None:
            return

        prompt_preview = user_prompt[:500].replace("\n", " ").strip()
        self.logger.record_action(
            stage=stage,
            action="llm_api_call_failed",
            duration_seconds=duration_seconds,
            input_summary=(
                f"provider=openai; requested_reasoning_effort={requested_effort}; "
                f"prompt_preview={prompt_preview}"
            ),
            output_summary=(
                f"provider=openai; escalated={escalated}; " f"error={error_text[:300]}"
            ),
            llm_call=False,
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            requested_reasoning_effort=requested_effort,
            effective_reasoning_effort="",
        )

    def _record_call(
        self,
        *,
        stage: str,
        user_prompt: str,
        result: LLMResult,
        escalated: bool,
        duration_seconds: float,
        error_text: str = "",
    ) -> None:
        if self.logger is None:
            return

        prompt_preview = user_prompt[:500].replace("\n", " ").strip()
        response_preview = result.text[:500].replace("\n", " ").strip()
        action = "llm_api_call"

        output_summary = f"provider=openai; escalated={escalated}; response_preview={response_preview}"
        if error_text:
            output_summary += f"; note={error_text[:180]}"

        self.logger.record_action(
            stage=stage,
            action=action,
            duration_seconds=duration_seconds,
            input_summary=(
                f"provider=openai; requested_reasoning_effort={result.requested_reasoning_effort}; "
                f"prompt_preview={prompt_preview}"
            ),
            output_summary=output_summary,
            llm_call=True,
            model=result.model,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            requested_reasoning_effort=result.requested_reasoning_effort,
            effective_reasoning_effort=result.effective_reasoning_effort,
        )

    def _call_openai(
        self,
        *,
        model: str,
        requested_effort: str,
        system_prompt: str,
        user_prompt: str,
    ) -> LLMResult:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, timeout=self.timeout_seconds)

        prompt_tokens = 0
        completion_tokens = 0

        normalized_requested = self._normalize_requested_effort(requested_effort)
        effort_candidates = self._effort_candidates(normalized_requested)
        last_error: Exception | None = None

        for effort in effort_candidates:
            try:
                response = client.responses.create(  # type: ignore[call-overload]
                    model=model,
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    reasoning={"effort": effort},  # type: ignore[arg-type]
                    temperature=self.temperature,
                )
                text = getattr(response, "output_text", "") or ""
                usage = getattr(response, "usage", None)
                if usage is not None:
                    prompt_tokens = int(getattr(usage, "input_tokens", 0) or 0)
                    completion_tokens = int(getattr(usage, "output_tokens", 0) or 0)
                return LLMResult(
                    text=text.strip() or "No response text returned.",
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    requested_reasoning_effort=normalized_requested,
                    effective_reasoning_effort=effort,
                )
            except Exception as exc:
                last_error = exc

        try:
            chat = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
            )
            content = chat.choices[0].message.content or ""
            usage = getattr(chat, "usage", None)
            if usage is not None:
                prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
                completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
            return LLMResult(
                text=content.strip() or "No response text returned.",
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                requested_reasoning_effort=normalized_requested,
                effective_reasoning_effort="",
            )
        except Exception as exc:
            last_error = exc

        if last_error is not None:
            raise last_error

        raise RuntimeError("OpenAI API call failed with unknown error")

    def _normalize_requested_effort(self, effort: str) -> str:
        normalized = effort.lower().strip()
        if normalized == "xhigh":
            return "xhigh"
        return "xhigh"

    def _effort_candidates(self, requested_effort: str) -> list[str]:
        return [requested_effort]

    def _judge(self, *, stage: str, prompt: str, candidate: str) -> int:
        if self.stats.total_calls >= self.max_total_calls:
            return 0

        judge_system = (
            "You are a verification-engineering quality judge. "
            "Score output quality from 0 to 100 for completeness, correctness, and actionability. "
            "Return strictly: score=<int>; reason=<short text>."
        )
        judge_user = (
            f"Stage: {stage}\n"
            f"Prompt:\n{prompt[:4000]}\n\n"
            f"Candidate output:\n{candidate[:6000]}\n"
        )

        try:
            judge_result = self.generate(
                stage=f"{stage}_judge",
                system_prompt=judge_system,
                user_prompt=judge_user,
                escalated=False,
            )
            match = re.search(
                r"score\s*=\s*(\d{1,3})", judge_result.text, flags=re.IGNORECASE
            )
            if not match:
                return 0
            parsed = int(match.group(1))
            return max(0, min(100, parsed))
        except Exception:
            return 0
