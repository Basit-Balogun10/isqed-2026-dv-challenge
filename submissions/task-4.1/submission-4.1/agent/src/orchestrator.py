from __future__ import annotations

import json
import os
import random
import re
import shutil
import subprocess
import sys
import textwrap
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from agent_logger import AgentLogger
from analyzer import analyze
from io_utils import (
    discover_rtl_files,
    ensure_dir,
    read_text,
    total_file_size,
    write_json,
    write_text,
)
from llm_provider import LLMProvider


class AutoVerifierOrchestrator:
    """Seven-stage autonomous verification pipeline for Task 4.1."""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.agent_cfg = config.get("agent", {}) if isinstance(config, dict) else {}
        self.max_minutes = int(self.agent_cfg.get("max_minutes", 60))
        self.max_iterations_cap = int(self.agent_cfg.get("max_iterations_cap", 12))
        configured_iterations = int(self.agent_cfg.get("max_iterations", 4))
        self.max_iterations = max(1, min(configured_iterations, self.max_iterations_cap))
        self.iteration_mode = str(self.agent_cfg.get("iteration_mode", "fixed")).strip().lower()
        if self.iteration_mode not in {"fixed", "auto"}:
            self.iteration_mode = "fixed"
        self.min_iterations = max(
            1, int(self.agent_cfg.get("min_iterations", 4))
        )
        self.auto_extension_step = max(
            1, int(self.agent_cfg.get("auto_extension_step", 2))
        )
        self.max_repair_generations_per_iteration = int(
            self.agent_cfg.get("max_repair_generations_per_iteration", 1)
        )
        configured_timeout = self.agent_cfg.get("timeout_minutes", self.max_minutes)
        self.timeout_minutes = float(configured_timeout)
        if self.timeout_minutes <= 0:
            self.timeout_minutes = float(self.max_minutes)
        self.plateau_delta_epsilon = float(
            self.agent_cfg.get("plateau_delta_epsilon", 0.5)
        )
        self.plateau_far_from_goal_margin = float(
            self.agent_cfg.get("plateau_far_from_goal_margin", 15.0)
        )
        self.plateau_escalation_enabled = bool(
            self.agent_cfg.get("plateau_escalation_enabled", True)
        )
        self.simulator_mode = str(self.agent_cfg.get("simulator_mode", "auto"))
        self.require_dual_simulator = bool(
            self.agent_cfg.get("require_dual_simulator", False)
        )

        self.logger = AgentLogger()
        self.llm = LLMProvider(config=config, logger=self.logger)
        self.logger.set_llm_identity(
            provider=self.llm.provider_name, model=self.llm.primary_model
        )

        self._run_start = time.monotonic()
        self._deadline_monotonic: float | None = None
        self._llm_timeout_lock = False
        self._timeout_reason = ""

    def run(
        self,
        *,
        rtl_path: Path,
        spec_path: Path,
        csr_map_path: Path,
        output_dir: Path,
        simulator_mode: str | None = None,
        max_iterations: int | None = None,
        max_repair_generations_per_iteration: int | None = None,
        iteration_mode: str | None = None,
        min_iterations: int | None = None,
        timeout_minutes: float | None = None,
    ) -> None:
        rtl_path = rtl_path.resolve()
        spec_path = spec_path.resolve()
        csr_map_path = csr_map_path.resolve()
        output_dir = output_dir.resolve()
        if simulator_mode:
            self.simulator_mode = str(simulator_mode)
        if max_iterations is not None:
            requested = int(max_iterations)
            self.max_iterations = max(1, min(requested, self.max_iterations_cap))
        if max_repair_generations_per_iteration is not None:
            self.max_repair_generations_per_iteration = max(
                0, int(max_repair_generations_per_iteration)
            )
        if iteration_mode:
            mode = str(iteration_mode).strip().lower()
            if mode in {"fixed", "auto"}:
                self.iteration_mode = mode
        if min_iterations is not None:
            self.min_iterations = max(1, int(min_iterations))
        if timeout_minutes is not None:
            self.timeout_minutes = max(0.0, float(timeout_minutes))

        self._run_start = time.monotonic()
        self._deadline_monotonic = (
            self._run_start + self.timeout_minutes * 60.0
            if self.timeout_minutes > 0
            else None
        )
        self._llm_timeout_lock = False
        self._timeout_reason = ""

        ensure_dir(output_dir)
        self._prepare_output_layout(output_dir)

        analysis = self._stage_analyze(
            rtl_path=rtl_path,
            spec_path=spec_path,
            csr_map_path=csr_map_path,
            output_dir=output_dir,
        )
        plan = self._stage_plan(
            analysis=analysis, spec_path=spec_path, output_dir=output_dir
        )

        build_result = self._stage_build(
            analysis=analysis,
            plan=plan,
            csr_map_path=csr_map_path,
            output_dir=output_dir,
        )

        test_result = self._stage_test(
            output_dir=output_dir, build_result=build_result, analysis=analysis
        )
        if self.require_dual_simulator and not bool(
            test_result.get("dual_simulator_compliant", False)
        ):
            raise RuntimeError(
                "Dual-simulator compliance gate failed: expected passing runs on both icarus and verilator."
            )
        coverage_result = self._stage_measure(
            output_dir=output_dir, test_result=test_result, analysis=analysis
        )

        iteration_result, coverage_result = self._stage_iterate(
            output_dir=output_dir,
            coverage_result=coverage_result,
            plan=plan,
            analysis=analysis,
            build_result=build_result,
        )

        bug_result = self._detect_potential_bugs(
            rtl_path=rtl_path, output_dir=output_dir
        )
        self._stage_report(
            output_dir=output_dir,
            analysis=analysis,
            plan=plan,
            test_result=test_result,
            coverage_result=coverage_result,
            iteration_result=iteration_result,
            bug_result=bug_result,
        )

        self.logger.finalize(
            output_path=output_dir / "agent_log.json", stats=self.llm.stats
        )

    def _deadline_reached(self) -> bool:
        if self._deadline_monotonic is None:
            return False
        return time.monotonic() >= self._deadline_monotonic

    def _remaining_seconds(self) -> float:
        if self._deadline_monotonic is None:
            return float("inf")
        return self._deadline_monotonic - time.monotonic()

    def _llm_allowed(self) -> bool:
        if self._llm_timeout_lock:
            return False
        if self._deadline_reached():
            self._llm_timeout_lock = True
            if not self._timeout_reason:
                self._timeout_reason = (
                    "Global timeout reached: no further LLM calls were permitted; "
                    "agent concluded with available artifacts."
                )
            return False
        return True

    def _prepare_output_layout(self, output_dir: Path) -> None:
        required_dirs = [
            output_dir / "testbench",
            output_dir / "testbench" / "agents",
            output_dir / "testbench" / "ref_model",
            output_dir / "testbench" / "scoreboard",
            output_dir / "testbench" / "coverage",
            output_dir / "tests",
            output_dir / "tests" / "directed",
            output_dir / "tests" / "random",
            output_dir / "coverage",
            output_dir / "coverage" / "code_coverage",
            output_dir / "coverage" / "func_coverage",
            output_dir / "assertions",
            output_dir / "bug_reports",
        ]
        for directory in required_dirs:
            ensure_dir(directory)

    def _stage_analyze(
        self, *, rtl_path: Path, spec_path: Path, csr_map_path: Path, output_dir: Path
    ) -> dict:
        stage = "ANALYZE"
        stage_start = time.monotonic()

        analysis = analyze(
            rtl_path=rtl_path, spec_path=spec_path, csr_map_path=csr_map_path
        )
        analysis["rtl_bytes"] = total_file_size(
            [Path(p) for p in analysis.get("rtl_files", [])]
        )

        write_json(output_dir / "analysis.json", analysis)

        self.logger.record_action(
            stage=stage,
            action="extract_dut_structure",
            duration_seconds=time.monotonic() - stage_start,
            input_summary=(
                f"rtl={rtl_path}; spec={spec_path.name}; csr={csr_map_path.name}"
            ),
            output_summary=(
                f"modules={len(analysis.get('modules', []))}, ports={analysis.get('port_count', 0)}, "
                f"tlul={analysis.get('tlul_detected', False)}, top={analysis.get('selected_top', '')}, "
                f"fsm_candidates={len(analysis.get('fsm_candidates', []))}"
            ),
        )
        return analysis

    def _stage_plan(self, *, analysis: dict, spec_path: Path, output_dir: Path) -> dict:
        stage = "PLAN"
        stage_start = time.monotonic()

        if not self._llm_allowed():
            plan = self._build_fallback_plan(analysis=analysis)
            write_json(output_dir / "verification_plan.json", plan)
            write_text(
                output_dir / "verification_plan.md", self._render_plan_markdown(plan)
            )
            self.logger.record_action(
                stage=stage,
                action="synthesize_verification_plan_timeout_fallback",
                duration_seconds=time.monotonic() - stage_start,
                input_summary=f"analysis modules={len(analysis.get('modules', []))}",
                output_summary=(
                    f"features={len(plan.get('features', []))}; directed={len(plan.get('directed_tests', []))}; "
                    f"risk_areas={len(plan.get('risk_areas', []))}; timeout_guard=True"
                ),
            )
            return plan

        spec_text = read_text(spec_path, max_chars=24_000)
        prompt = self._build_plan_prompt(analysis=analysis, spec_text=spec_text)

        llm_result, judge_score, escalated = self.llm.generate_with_quality_gate(
            stage=stage,
            system_prompt=(
                "You are a senior ASIC verification architect. "
                "Produce a practical and runnable verification plan in JSON only."
            ),
            user_prompt=prompt,
            min_score=int(self.config.get("llm", {}).get("judge_min_score", 80)),
        )

        plan_candidate = self._extract_json_dict(llm_result.text)
        if not plan_candidate:
            repair_prompt = textwrap.dedent(
                f"""\
                The prior output was not valid JSON for the required schema.
                Convert it into strict JSON only with this schema:
                {{
                  "features": ["..."],
                  "coverage_goals": {{
                    "line_percent": 85,
                    "branch_percent": 75,
                    "functional_percent": 85
                  }},
                  "directed_tests": [{{"name": "...", "intent": "..."}}],
                  "random_tests": [{{"name": "...", "intent": "..."}}],
                  "risk_areas": [{{"area": "...", "reason": "...", "priority": "high|medium|low"}}]
                }}

                Prior output:
                {llm_result.text[:12000]}
                """
            )
            if self._llm_allowed():
                repaired = self.llm.generate(
                    stage="PLAN_REPAIR",
                    system_prompt="Return strict JSON only. No markdown, no prose.",
                    user_prompt=repair_prompt,
                    escalated=True,
                )
                plan_candidate = self._extract_json_dict(repaired.text)

        plan = plan_candidate or self._build_fallback_plan(analysis=analysis)

        write_json(output_dir / "verification_plan.json", plan)
        write_text(
            output_dir / "verification_plan.md", self._render_plan_markdown(plan)
        )

        self.logger.record_action(
            stage=stage,
            action="synthesize_verification_plan",
            duration_seconds=time.monotonic() - stage_start,
            input_summary=f"analysis modules={len(analysis.get('modules', []))}; spec_excerpt_chars={len(spec_text)}",
            output_summary=(
                f"features={len(plan.get('features', []))}; directed={len(plan.get('directed_tests', []))}; "
                f"risk_areas={len(plan.get('risk_areas', []))}; judge_score={judge_score}; escalated={escalated}"
            ),
        )
        return plan

    def _stage_build(
        self, *, analysis: dict, plan: dict, csr_map_path: Path, output_dir: Path
    ) -> dict:
        stage = "BUILD"
        stage_start = time.monotonic()

        registers = self._parse_csr_registers(csr_map_path)
        clock_name = self._pick_signal(
            analysis.get("clock_candidates", []), default="clk_i"
        )
        reset_name = self._pick_signal(
            analysis.get("reset_candidates", []), default="rst_ni"
        )
        protocol_hint = self._pick_protocol_hint(analysis.get("protocol_hints", []))

        self._write_testbench_files(
            output_dir=output_dir,
            clock_name=clock_name,
            reset_name=reset_name,
            protocol_hint=protocol_hint,
            registers=registers,
        )
        test_generation = self._write_tests(
            output_dir=output_dir,
            plan=plan,
            registers=registers,
            clock_name=clock_name,
            reset_name=reset_name,
            analysis=analysis,
        )
        self._write_assertions(output_dir=output_dir, reset_name=reset_name)

        generated_files = self._collect_generated_python_files(output_dir)

        result = {
            "generated_python_files": [str(p) for p in sorted(generated_files)],
            "register_count": len(registers),
            "clock_name": clock_name,
            "reset_name": reset_name,
            "protocol_hint": protocol_hint,
            "directed_test_case_count": int(
                test_generation.get("directed_test_case_count", 0)
            ),
            "random_test_case_count": int(
                test_generation.get("random_test_case_count", 0)
            ),
            "directed_test_file_count": int(
                test_generation.get("directed_test_file_count", 0)
            ),
            "random_test_file_count": int(
                test_generation.get("random_test_file_count", 0)
            ),
        }
        write_json(output_dir / "build_manifest.json", result)

        self.logger.record_action(
            stage=stage,
            action="generate_verification_environment",
            duration_seconds=time.monotonic() - stage_start,
            input_summary=f"registers={len(registers)}; plan_tests={len(plan.get('directed_tests', []))}",
            output_summary=f"generated_python_files={len(generated_files)}",
        )
        return result

    def _stage_test(
        self, *, output_dir: Path, build_result: dict, analysis: dict
    ) -> dict:
        stage = "TEST"
        stage_start = time.monotonic()

        py_files = [Path(p) for p in build_result.get("generated_python_files", [])]
        syntax_errors: list[dict] = []

        for py_file in py_files:
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
                compile(source, str(py_file), "exec")
            except Exception as exc:  # pragma: no cover - defensive path
                syntax_errors.append({"file": str(py_file), "error": str(exc)})

        directed_tests = sorted((output_dir / "tests" / "directed").glob("test_*.py"))
        random_tests = sorted((output_dir / "tests" / "random").glob("test_*.py"))
        cocotb_tests = [*directed_tests, *random_tests]

        simulation_runs: list[dict] = []
        selected_top = str(analysis.get("selected_top", ""))
        coverage_dat_files: list[str] = []
        simulation_passed = False
        dual_simulator_compliant = False
        simulators_requested: list[str] = []

        if not syntax_errors and cocotb_tests:
            sim_result = self._run_cocotb_simulations(
                output_dir=output_dir,
                analysis=analysis,
                test_files=cocotb_tests,
            )
            simulation_runs = sim_result.get("runs", [])
            simulation_passed = bool(sim_result.get("simulation_passed", False))
            coverage_dat_files = sim_result.get("coverage_dat_files", [])
            selected_top = str(sim_result.get("selected_top", selected_top))
            dual_simulator_compliant = bool(
                sim_result.get("dual_simulator_compliant", False)
            )
            simulators_requested = [
                str(s)
                for s in sim_result.get("simulators_requested", [])
                if str(s).strip()
            ]

        directed_file_count = len(directed_tests)
        random_file_count = len(random_tests)
        directed_case_target = int(
            build_result.get("directed_test_case_count", directed_file_count)
        )
        random_case_target = int(
            build_result.get("random_test_case_count", random_file_count)
        )

        result = {
            "python_file_count": len(py_files),
            "syntax_passed": len(syntax_errors) == 0,
            "syntax_errors": syntax_errors,
            "directed_test_count": directed_case_target,
            "random_test_count": random_case_target,
            "directed_test_file_count": directed_file_count,
            "random_test_file_count": random_file_count,
            "simulation_runs": simulation_runs,
            "simulation_passed": simulation_passed,
            "simulators_tested": sorted(
                {
                    str(r.get("simulator", ""))
                    for r in simulation_runs
                    if r.get("simulator")
                }
            ),
            "simulators_requested": simulators_requested,
            "dual_simulator_compliant": dual_simulator_compliant,
            "selected_top": selected_top,
            "coverage_dat_files": coverage_dat_files,
        }

        write_json(output_dir / "test_results.json", result)

        passed_runs = len([r for r in simulation_runs if bool(r.get("passed", False))])
        self.logger.record_action(
            stage=stage,
            action="execute_generated_tests",
            duration_seconds=time.monotonic() - stage_start,
            input_summary=f"generated_files={len(py_files)}",
            output_summary=(
                f"syntax_passed={result['syntax_passed']}; errors={len(syntax_errors)}; "
                f"directed_cases={result['directed_test_count']} (files={result['directed_test_file_count']}); "
                f"random_cases={result['random_test_count']} (files={result['random_test_file_count']}); "
                f"sim_runs={len(simulation_runs)}; sim_passed={passed_runs}; "
                f"dual_simulator={result['dual_simulator_compliant']}"
            ),
        )
        return result

    def _stage_measure(
        self, *, output_dir: Path, test_result: dict, analysis: dict
    ) -> dict:
        stage = "MEASURE"
        stage_start = time.monotonic()

        simulation_runs = test_result.get("simulation_runs", [])
        total_sim_runs = len(simulation_runs)
        passed_sim_runs = len(
            [r for r in simulation_runs if bool(r.get("passed", False))]
        )

        code_cov = self._extract_verilator_coverage(
            output_dir=output_dir,
            coverage_dat_files=[
                str(p) for p in test_result.get("coverage_dat_files", [])
            ],
        )
        if not code_cov:
            # If coverage databases are unavailable, surface explicit zeros rather than synthetic scores.
            code_cov = {
                "line_percent": 0.0,
                "branch_percent": 0.0,
                "toggle_percent": 0.0,
                "fsm_percent": 0.0,
                "source": "no_coverage_database",
            }

        func_cov = self._extract_functional_coverage(output_dir=output_dir)

        metrics = {
            "code_coverage": {
                "line_percent": float(code_cov.get("line_percent", 0.0)),
                "branch_percent": float(code_cov.get("branch_percent", 0.0)),
                "toggle_percent": float(code_cov.get("toggle_percent", 0.0)),
                "fsm_percent": float(code_cov.get("fsm_percent", 0.0)),
                "source": str(code_cov.get("source", "unknown")),
                "toggle_source": str(code_cov.get("toggle_source", "unknown")),
                "fsm_source": str(code_cov.get("fsm_source", "unknown")),
            },
            "functional_coverage": {
                "percent": float(func_cov.get("percent", 0.0)),
                "bins_hit": int(func_cov.get("bins_hit", 0)),
                "bins_total": int(func_cov.get("bins_total", 0)),
                "source": str(func_cov.get("source", "unknown")),
            },
            "assertions": {
                "passed": bool(test_result.get("simulation_passed", False)),
                "failed": max(0, total_sim_runs - passed_sim_runs),
            },
            "simulation": {
                "total_runs": total_sim_runs,
                "passed_runs": passed_sim_runs,
                "failed_runs": max(0, total_sim_runs - passed_sim_runs),
            },
        }

        write_json(output_dir / "coverage" / "coverage_summary.json", metrics)

        code_cov_metric = metrics.get("code_coverage", {})
        if not isinstance(code_cov_metric, dict):
            code_cov_metric = {}
        func_cov_metric = metrics.get("functional_coverage", {})
        if not isinstance(func_cov_metric, dict):
            func_cov_metric = {}

        line_cov = float(code_cov_metric.get("line_percent", 0.0))
        branch_cov = float(code_cov_metric.get("branch_percent", 0.0))
        toggle_cov = float(code_cov_metric.get("toggle_percent", 0.0))
        fsm_cov = float(code_cov_metric.get("fsm_percent", 0.0))
        func_cov_percent = float(func_cov_metric.get("percent", 0.0))
        bins_hit = int(func_cov_metric.get("bins_hit", 0))
        bins_total = int(func_cov_metric.get("bins_total", 0))

        code_cov_text = textwrap.dedent(
            f"""\
            code_coverage_summary
            line_percent: {line_cov}
            branch_percent: {branch_cov}
            toggle_percent: {toggle_cov}
            fsm_percent: {fsm_cov}
            source: {code_cov_metric.get('source', 'unknown')}
            toggle_source: {code_cov_metric.get('toggle_source', 'unknown')}
            fsm_source: {code_cov_metric.get('fsm_source', 'unknown')}
            """
        )
        func_cov_text = textwrap.dedent(
            f"""\
            functional_coverage_summary
            percent: {func_cov_percent}
            bins_hit: {bins_hit}
            bins_total: {bins_total}
            source: {func_cov_metric.get('source', 'unknown')}
            """
        )

        write_text(
            output_dir / "coverage" / "code_coverage" / "summary.txt", code_cov_text
        )
        write_text(
            output_dir / "coverage" / "func_coverage" / "summary.txt", func_cov_text
        )

        self.logger.record_action(
            stage=stage,
            action="collect_coverage",
            duration_seconds=time.monotonic() - stage_start,
            input_summary=(
                f"sim_runs={total_sim_runs}; passed={passed_sim_runs}; "
                f"top={test_result.get('selected_top', '')}"
            ),
            output_summary=f"line={line_cov}%; branch={branch_cov}%; func={func_cov_percent}%",
        )
        return metrics

    def _stage_iterate(
        self,
        *,
        output_dir: Path,
        coverage_result: dict,
        plan: dict,
        analysis: dict,
        build_result: dict,
    ) -> tuple[dict, dict]:
        stage = "ITERATE"
        stage_start = time.monotonic()

        initial_func = float(
            coverage_result.get("functional_coverage", {}).get("percent", 0.0)
        )
        current_func = float(initial_func)
        target = float(plan.get("coverage_goals", {}).get("functional_percent", 85))
        plateau_streak = 0

        iteration_budget = max(1, int(self.max_iterations))
        hard_cap = max(1, int(self.max_iterations_cap))
        if self.iteration_mode == "auto":
            iteration_budget = max(iteration_budget, int(self.min_iterations))
        iteration_budget = min(iteration_budget, hard_cap)

        iterations: list[dict] = []
        extension_events: list[dict] = []
        stop_reason = ""
        last_test_result: dict = {
            "simulation_passed": True,
            "simulation_runs": [],
        }

        iteration_num = 1
        while iteration_num <= iteration_budget and iteration_num <= hard_cap:
            if self._deadline_reached():
                stop_reason = self._timeout_reason or "global_timeout_reached"
                break

            iteration_start_func = float(current_func)

            scenario_name = self._suggest_gap_scenario(plan=plan, index=iteration_num)
            file_path = (
                output_dir / "tests" / "random" / f"test_gap_iter_{iteration_num}.py"
            )
            write_text(
                file_path,
                self._render_gap_test_file(
                    iteration=iteration_num, scenario_name=scenario_name
                ),
            )

            build_result["generated_python_files"] = [
                str(p) for p in self._collect_generated_python_files(output_dir)
            ]
            test_result_iter = self._stage_test(
                output_dir=output_dir, build_result=build_result, analysis=analysis
            )
            coverage_result = self._stage_measure(
                output_dir=output_dir, test_result=test_result_iter, analysis=analysis
            )
            last_test_result = test_result_iter
            current_func = float(
                coverage_result.get("functional_coverage", {}).get("percent", 0.0)
            )

            repair_attempts: list[dict] = []
            for repair_idx in range(self.max_repair_generations_per_iteration):
                if self._deadline_reached():
                    if not self._timeout_reason:
                        self._timeout_reason = (
                            "Global timeout reached during iterate-repair stage; "
                            "no further LLM calls were permitted."
                        )
                    break

                coverage_gain = float(current_func - iteration_start_func)
                simulation_ok = bool(test_result_iter.get("simulation_passed", False))
                if simulation_ok and coverage_gain > self.plateau_delta_epsilon:
                    break

                rewritten = self._rewrite_failing_tests_with_llm(
                    output_dir=output_dir,
                    plan=plan,
                    analysis=analysis,
                    test_result=test_result_iter,
                    iteration=iteration_num,
                    min_iterations=(
                        int(self.min_iterations)
                        if self.iteration_mode == "auto"
                        else int(self.max_iterations)
                    ),
                    max_iterations=hard_cap,
                )
                if not rewritten:
                    break

                coverage_before = float(current_func)
                build_result["generated_python_files"] = [
                    str(p) for p in self._collect_generated_python_files(output_dir)
                ]
                test_result_iter = self._stage_test(
                    output_dir=output_dir,
                    build_result=build_result,
                    analysis=analysis,
                )
                coverage_result = self._stage_measure(
                    output_dir=output_dir,
                    test_result=test_result_iter,
                    analysis=analysis,
                )
                last_test_result = test_result_iter
                current_func = float(
                    coverage_result.get("functional_coverage", {}).get("percent", 0.0)
                )

                repair_attempts.append(
                    {
                        "repair_attempt": repair_idx + 1,
                        "rewritten_modules": len(rewritten),
                        "rewritten_paths": [str(r.get("path", "")) for r in rewritten],
                        "coverage_before": coverage_before,
                        "coverage_after": current_func,
                        "simulation_passed": bool(
                            test_result_iter.get("simulation_passed", False)
                        ),
                        "failing_runs": len(
                            [
                                r
                                for r in test_result_iter.get("simulation_runs", [])
                                if not bool(r.get("passed", False))
                            ]
                        ),
                    }
                )

            coverage_delta = float(current_func - iteration_start_func)
            if abs(coverage_delta) <= self.plateau_delta_epsilon:
                plateau_streak += 1
            else:
                plateau_streak = 0

            goal_gap = float(target - current_func)
            plateau_escalation: dict[str, object] = {
                "triggered": False,
                "plateau_streak": plateau_streak,
                "epsilon": self.plateau_delta_epsilon,
                "goal_gap": goal_gap,
                "far_from_goal_margin": self.plateau_far_from_goal_margin,
            }

            should_escalate = (
                self.plateau_escalation_enabled
                and plateau_streak >= 2
                and goal_gap > 0.0
                and (
                    goal_gap >= self.plateau_far_from_goal_margin
                    or not bool(test_result_iter.get("simulation_passed", False))
                )
            )
            if should_escalate:
                plateau_file = (
                    output_dir
                    / "tests"
                    / "random"
                    / f"test_plateau_escalation_{iteration_num}.py"
                )
                try:
                    plateau_code = self._generate_plateau_escalation_test(
                        iteration=iteration_num,
                        plan=plan,
                        analysis=analysis,
                        current_func=current_func,
                        target_func=target,
                    )
                except Exception:
                    plateau_code = self._render_plateau_escalation_test_file(
                        iteration=iteration_num,
                        clock_name=str(build_result.get("clock_name", "clk_i")),
                        reset_name=str(build_result.get("reset_name", "rst_ni")),
                        scenario_name=scenario_name,
                    )

                plateau_code = self._sanitize_generated_plateau_test(
                    plateau_code=plateau_code,
                    iteration=iteration_num,
                )
                if not self._repair_test_compatible(plateau_code):
                    plateau_code = self._render_plateau_escalation_test_file(
                        iteration=iteration_num,
                        clock_name=str(build_result.get("clock_name", "clk_i")),
                        reset_name=str(build_result.get("reset_name", "rst_ni")),
                        scenario_name=scenario_name,
                    )

                try:
                    compile(plateau_code, str(plateau_file), "exec")
                except Exception:
                    plateau_code = self._render_plateau_escalation_test_file(
                        iteration=iteration_num,
                        clock_name=str(build_result.get("clock_name", "clk_i")),
                        reset_name=str(build_result.get("reset_name", "rst_ni")),
                        scenario_name=scenario_name,
                    )

                write_text(plateau_file, plateau_code)

                build_result["generated_python_files"] = [
                    str(p) for p in self._collect_generated_python_files(output_dir)
                ]
                test_result_iter = self._stage_test(
                    output_dir=output_dir,
                    build_result=build_result,
                    analysis=analysis,
                )
                coverage_result = self._stage_measure(
                    output_dir=output_dir,
                    test_result=test_result_iter,
                    analysis=analysis,
                )
                last_test_result = test_result_iter
                before_plateau = float(current_func)
                current_func = float(
                    coverage_result.get("functional_coverage", {}).get("percent", 0.0)
                )

                plateau_escalation.update(
                    {
                        "triggered": True,
                        "plateau_test": str(plateau_file),
                        "coverage_before": before_plateau,
                        "coverage_after": current_func,
                        "simulation_passed": bool(
                            test_result_iter.get("simulation_passed", False)
                        ),
                    }
                )

            iteration_failing_runs = len(
                [
                    r
                    for r in test_result_iter.get("simulation_runs", [])
                    if not bool(r.get("passed", False))
                ]
            )

            iterations.append(
                {
                    "iteration": iteration_num,
                    "added_test": str(file_path),
                    "scenario": scenario_name,
                    "functional_before": iteration_start_func,
                    "updated_functional_coverage": current_func,
                    "coverage_delta": float(current_func - iteration_start_func),
                    "simulation_passed": bool(
                        test_result_iter.get("simulation_passed", False)
                    ),
                    "failing_runs": iteration_failing_runs,
                    "repairs_used": len(repair_attempts),
                    "repair_attempts": repair_attempts,
                    "plateau_escalation": plateau_escalation,
                }
            )

            reached_goal = bool(current_func >= target)
            all_tests_passing = bool(test_result_iter.get("simulation_passed", False))
            needs_more = (not reached_goal) or (not all_tests_passing)
            if not needs_more:
                stop_reason = "coverage_target_and_simulation_goal_met"
                break

            if (
                self.iteration_mode == "auto"
                and iteration_num >= iteration_budget
                and iteration_budget < hard_cap
                and not self._deadline_reached()
            ):
                previous_budget = iteration_budget
                iteration_budget = min(hard_cap, iteration_budget + self.auto_extension_step)
                extension_events.append(
                    {
                        "after_iteration": iteration_num,
                        "previous_budget": previous_budget,
                        "new_budget": iteration_budget,
                        "reason": "still_failing_or_under_target",
                    }
                )

            iteration_num += 1

        if not stop_reason:
            if self._deadline_reached():
                stop_reason = self._timeout_reason or "global_timeout_reached"
            elif current_func >= target and bool(last_test_result.get("simulation_passed", False)):
                stop_reason = "coverage_target_and_simulation_goal_met"
            elif len(iterations) >= hard_cap:
                stop_reason = "max_iteration_cap_reached"
            else:
                stop_reason = "iteration_budget_exhausted"

        write_json(
            output_dir / "iteration_log.json",
            {
                "iterations": iterations,
                "iteration_mode": self.iteration_mode,
                "final_budget": iteration_budget,
                "hard_cap": hard_cap,
                "extension_events": extension_events,
                "stop_reason": stop_reason,
                "timeout_reason": self._timeout_reason,
            },
        )

        self.logger.record_action(
            stage=stage,
            action="close_coverage_gaps",
            duration_seconds=time.monotonic() - stage_start,
            input_summary=f"initial_functional={initial_func}",
            output_summary=(
                f"iterations={len(iterations)}; final_functional={round(current_func, 2)}; "
                f"stop_reason={stop_reason}; extensions={len(extension_events)}"
            ),
        )

        return (
            {
                "iterations": iterations,
                "final_functional_percent": float(
                    coverage_result.get("functional_coverage", {}).get(
                        "percent", round(current_func, 2)
                    )
                ),
                "target_functional_percent": target,
                "iteration_mode": self.iteration_mode,
                "stop_reason": stop_reason,
                "extension_events": extension_events,
                "timeout_reason": self._timeout_reason,
                "final_simulation_passed": bool(
                    last_test_result.get("simulation_passed", False)
                ),
            },
            coverage_result,
        )

    def _detect_potential_bugs(self, *, rtl_path: Path, output_dir: Path) -> dict:
        stage = "REPORT"
        stage_start = time.monotonic()

        findings: list[dict] = []
        rtl_files = discover_rtl_files(rtl_path)

        for file_path in rtl_files:
            text = read_text(file_path, max_chars=400_000)
            if not text:
                continue

            if "case" in text and "default" not in text:
                findings.append(
                    {
                        "severity": "medium",
                        "title": "Potential incomplete case statement",
                        "file": str(file_path),
                        "description": "Detected case statements without an obvious default branch.",
                        "reproduction": "Review all case blocks and run lint/formal checks for completeness.",
                    }
                )

            if (
                re.search(r"always_ff[\s\S]{0,300}?\n\s*if\s*\(", text)
                and "rst" not in text.lower()
            ):
                findings.append(
                    {
                        "severity": "low",
                        "title": "Sequential logic may miss explicit reset",
                        "file": str(file_path),
                        "description": "Found sequential blocks that may not include explicit reset behavior.",
                        "reproduction": "Force reset at power-up and inspect known-state requirements.",
                    }
                )

            if "TODO" in text or "FIXME" in text:
                findings.append(
                    {
                        "severity": "low",
                        "title": "Unresolved design TODO/FIXME marker",
                        "file": str(file_path),
                        "description": "Design source includes TODO/FIXME markers that may indicate incomplete behavior.",
                        "reproduction": "Audit the referenced code block and confirm implemented behavior.",
                    }
                )

            if len(findings) >= 5:
                break

        if not findings:
            no_findings = {
                "status": "no_findings",
                "summary": "No static high-confidence bug signatures were detected in the available RTL sample.",
            }
            write_text(
                output_dir / "bug_reports" / "no_findings.yaml",
                yaml.safe_dump(no_findings, sort_keys=False),
            )
            write_text(
                output_dir / "bug_reports" / "no_findings.md",
                "# No Findings\n\nNo static high-confidence bug signatures were detected in the available RTL sample.\n",
            )
        else:
            for idx, finding in enumerate(findings, start=1):
                bug_yaml = {
                    "bug_id": f"BUG-{idx:03d}",
                    "title": finding["title"],
                    "severity": finding["severity"],
                    "location": finding["file"],
                    "description": finding["description"],
                    "reproduction": finding["reproduction"],
                    "confidence": "medium",
                }
                write_text(
                    output_dir / "bug_reports" / f"bug_{idx:03d}.yaml",
                    yaml.safe_dump(bug_yaml, sort_keys=False),
                )
                bug_md = textwrap.dedent(
                    f"""\
                    # {bug_yaml['bug_id']}: {bug_yaml['title']}

                    - severity: {bug_yaml['severity']}
                    - location: {bug_yaml['location']}
                    - confidence: {bug_yaml['confidence']}

                    ## Description
                    {bug_yaml['description']}

                    ## Reproduction
                    {bug_yaml['reproduction']}
                    """
                )
                write_text(
                    output_dir / "bug_reports" / f"bug_{idx:03d}.md",
                    bug_md,
                )

        self.logger.record_action(
            stage=stage,
            action="static_bug_hypothesis",
            duration_seconds=time.monotonic() - stage_start,
            input_summary=f"rtl_files={len(rtl_files)}",
            output_summary=f"bug_hypotheses={len(findings)}",
        )

        return {"findings": findings}

    def _stage_report(
        self,
        *,
        output_dir: Path,
        analysis: dict,
        plan: dict,
        test_result: dict,
        coverage_result: dict,
        iteration_result: dict,
        bug_result: dict,
    ) -> None:
        stage = "REPORT"
        stage_start = time.monotonic()

        exec_summary = self._generate_exec_summary(
            analysis=analysis,
            plan=plan,
            test_result=test_result,
            coverage_result=coverage_result,
            iteration_result=iteration_result,
            bug_result=bug_result,
        )

        report = textwrap.dedent(
            f"""\
            # AutoVerifier Report

            ## DUT Analysis Findings
            - Modules discovered: {", ".join(analysis.get('modules', [])[:10]) or "none"}
            - Total RTL files: {len(analysis.get('rtl_files', []))}
            - Total RTL lines: {analysis.get('total_rtl_lines', 0)}
            - TL-UL detected: {analysis.get('tlul_detected', False)}
            - Protocol hints: {", ".join(analysis.get('protocol_hints', [])) or "none"}
            - Estimated FSM blocks: {analysis.get('estimated_fsm_blocks', 0)}

            ## Verification Plan
            - Planned features: {len(plan.get('features', []))}
            - Directed tests: {len(plan.get('directed_tests', []))}
            - Random tests: {len(plan.get('random_tests', []))}
            - Risk areas: {len(plan.get('risk_areas', []))}

            ## Test Results
            - Generated Python files: {test_result.get('python_file_count', 0)}
            - Syntax validation pass: {test_result.get('syntax_passed', False)}
            - Directed tests generated: {test_result.get('directed_test_count', 0)}
            - Random tests generated: {test_result.get('random_test_count', 0)}
            - Simulation run count: {len(test_result.get('simulation_runs', []))}
            - Simulation pass: {test_result.get('simulation_passed', False)}
            - Selected top module: {test_result.get('selected_top', 'unknown')}

            ## Coverage Achieved
            - Line coverage: {coverage_result.get('code_coverage', {}).get('line_percent', 0)}%
            - Branch coverage: {coverage_result.get('code_coverage', {}).get('branch_percent', 0)}%
            - Toggle coverage: {coverage_result.get('code_coverage', {}).get('toggle_percent', 0)}%
            - FSM coverage: {coverage_result.get('code_coverage', {}).get('fsm_percent', 0)}%
            - Functional coverage: {iteration_result.get('final_functional_percent', coverage_result.get('functional_coverage', {}).get('percent', 0))}%
            - Code coverage source: {coverage_result.get('code_coverage', {}).get('source', 'unknown')}
            - Functional coverage source: {coverage_result.get('functional_coverage', {}).get('source', 'unknown')}

            ## Bugs Found
            - Static bug hypotheses: {len(bug_result.get('findings', []))}
            - Detailed records are located in `bug_reports/`.

            ## Agent Methodology
            - Iterations performed: {len(iteration_result.get('iterations', []))}
            - Iteration mode: {iteration_result.get('iteration_mode', self.iteration_mode)}
            - Iteration stop reason: {iteration_result.get('stop_reason', 'unknown')}
            - Auto-extension events: {len(iteration_result.get('extension_events', []))}
            - Timeout guard reason: {iteration_result.get('timeout_reason', self._timeout_reason) or 'none'}
            - LLM provider: {self.llm.provider_name}
            - LLM mode observed: {self.llm.mode}
            - LLM calls: {self.llm.stats.total_calls}
            - Estimated tokens: {self.llm.stats.prompt_tokens + self.llm.stats.completion_tokens}

            ## Executive Summary
            {exec_summary}
            """
        )
        write_text(output_dir / "report.md", report)

        elapsed_minutes = (time.monotonic() - self._run_start) / 60.0
        self.logger.record_action(
            stage=stage,
            action="compose_final_report",
            duration_seconds=time.monotonic() - stage_start,
            input_summary=f"elapsed_minutes={elapsed_minutes:.2f}",
            output_summary=f"report_generated=True; within_budget={elapsed_minutes <= self.max_minutes}",
        )

    def _build_plan_prompt(self, *, analysis: dict, spec_text: str) -> str:
        analysis_brief = {
            "modules": analysis.get("modules", []),
            "port_count": analysis.get("port_count", 0),
            "tlul_detected": analysis.get("tlul_detected", False),
            "protocol_hints": analysis.get("protocol_hints", []),
            "csr_summary": analysis.get("csr_summary", {}),
            "estimated_fsm_blocks": analysis.get("estimated_fsm_blocks", 0),
        }
        return textwrap.dedent(
            f"""\
            Build a verification plan JSON for an unseen DUT.

            Constraints:
            - Assume cocotb + TL-UL bus verification strategy.
            - Keep the plan executable within a 60-minute autonomous budget.
            - Include risk-driven priorities.

            RTL/SPEC analysis summary:
            {json.dumps(analysis_brief, indent=2)}

            Specification excerpt:
            {spec_text[:8000]}

            Return strict JSON with this schema:
            {{
              "features": ["..."],
              "coverage_goals": {{
                "line_percent": 85,
                "branch_percent": 75,
                "functional_percent": 85
              }},
              "directed_tests": [{{"name": "...", "intent": "..."}}],
              "random_tests": [{{"name": "...", "intent": "..."}}],
              "risk_areas": [{{"area": "...", "reason": "...", "priority": "high|medium|low"}}]
            }}
            """
        )

    def _build_fallback_plan(self, *, analysis: dict) -> dict:
        protocol_hints = analysis.get("protocol_hints", [])
        proto = protocol_hints[0] if protocol_hints else "csr"
        return {
            "features": [
                "TL-UL CSR access correctness",
                "Reset and default register behavior",
                "Control-path and status-path consistency",
                "Datapath sanity for protocol-facing registers",
                "Interrupt and error handling characterization",
            ],
            "coverage_goals": {
                "line_percent": 85,
                "branch_percent": 75,
                "functional_percent": 85,
            },
            "directed_tests": [
                {
                    "name": "tlul_csr_smoke",
                    "intent": "Verify mapped CSR read/write semantics and reset defaults.",
                },
                {
                    "name": "ctrl_programming_modes",
                    "intent": "Program control registers and validate stable status transitions.",
                },
                {
                    "name": "datapath_basic_flow",
                    "intent": f"Exercise {proto}-related datapath register flow and boundary behavior.",
                },
                {
                    "name": "interrupt_error_paths",
                    "intent": "Exercise interrupt state/enable/test paths and error signaling.",
                },
            ],
            "random_tests": [
                {
                    "name": "csr_random_access_regression",
                    "intent": "Constrained-random CSR read/write traffic across mapped and unmapped ranges.",
                },
                {
                    "name": "datapath_random_stress",
                    "intent": f"Constrained-random {proto} datapath/control stress with deterministic seeds.",
                },
                {
                    "name": "reset_during_activity_random",
                    "intent": "Inject resets during active traffic and verify clean recovery.",
                },
            ],
            "risk_areas": [
                {
                    "area": "CSR access semantics",
                    "reason": "Read/write, RO/WO, and unmapped behavior frequently diverge from assumptions.",
                    "priority": "high",
                },
                {
                    "area": "Control and status coupling",
                    "reason": "Control writes may not map one-to-one to observable status behavior.",
                    "priority": "high",
                },
                {
                    "area": "Interrupt/error behavior",
                    "reason": "Interrupt and sticky error semantics are common integration bug sources.",
                    "priority": "medium",
                },
            ],
        }

    def _render_plan_markdown(self, plan: dict) -> str:
        lines = ["# Verification Plan", ""]

        lines.append("## Features")
        for item in plan.get("features", []):
            lines.append(f"- {item}")

        goals = plan.get("coverage_goals", {})
        lines.append("")
        lines.append("## Coverage Goals")
        lines.append(f"- Line: {goals.get('line_percent', 0)}%")
        lines.append(f"- Branch: {goals.get('branch_percent', 0)}%")
        lines.append(f"- Functional: {goals.get('functional_percent', 0)}%")

        lines.append("")
        lines.append("## Directed Tests")
        for test in plan.get("directed_tests", []):
            lines.append(f"- {test.get('name', 'unnamed')}: {test.get('intent', '')}")

        lines.append("")
        lines.append("## Random Tests")
        for test in plan.get("random_tests", []):
            lines.append(f"- {test.get('name', 'unnamed')}: {test.get('intent', '')}")

        lines.append("")
        lines.append("## Risk Areas")
        for risk in plan.get("risk_areas", []):
            lines.append(
                f"- {risk.get('area', 'unknown')} ({risk.get('priority', 'medium')}): {risk.get('reason', '')}"
            )

        return "\n".join(lines) + "\n"

    def _extract_json_dict(self, text: str) -> dict | None:
        try:
            maybe = json.loads(text)
            if isinstance(maybe, dict):
                return maybe
        except Exception:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            candidate = text[start : end + 1]
            try:
                maybe = json.loads(candidate)
                if isinstance(maybe, dict):
                    return maybe
            except Exception:
                return None
        return None

    def _parse_csr_registers(self, csr_map_path: Path) -> list[dict]:
        text = read_text(csr_map_path, max_chars=600_000)
        if not text:
            return []

        data: dict = {}
        try:
            import hjson  # type: ignore[import-untyped]

            loaded = hjson.loads(text)
            if isinstance(loaded, dict):
                data = loaded
        except Exception as exc:
            raise RuntimeError(f"Failed to parse CSR map as Hjson: {exc}") from exc

        regs_raw = data.get("registers") if isinstance(data, dict) else None
        if not isinstance(regs_raw, list):
            regs_raw = []

        registers: list[dict] = []
        for entry in regs_raw:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name", "unnamed")).strip() or "unnamed"
            offset = self._parse_int(entry.get("offset"), default=0)
            resval = self._parse_int(entry.get("resval"), default=0)
            swaccess = str(entry.get("swaccess", "rw")).strip().lower() or "rw"

            fields_raw = entry.get("fields") if isinstance(entry, dict) else None
            valid_mask = 0
            writable_mask = 0
            if isinstance(fields_raw, list):
                for field in fields_raw:
                    if not isinstance(field, dict):
                        continue
                    mask = self._parse_field_mask(field.get("bits"))
                    if mask == 0:
                        continue
                    valid_mask |= mask
                    field_sw = (
                        str(field.get("swaccess", swaccess)).strip().lower()
                        or swaccess
                    )
                    if "w" in field_sw:
                        writable_mask |= mask

            if valid_mask == 0:
                valid_mask = 0xFFFFFFFF
            if writable_mask == 0 and "w" in swaccess:
                writable_mask = valid_mask

            registers.append(
                {
                    "name": name,
                    "address": offset,
                    "resval": resval,
                    "swaccess": swaccess,
                    "valid_mask": valid_mask & 0xFFFFFFFF,
                    "writable_mask": writable_mask & 0xFFFFFFFF,
                }
            )

        if registers:
            return registers

        raise RuntimeError(
            "CSR map contains no register entries under the registers key."
        )

    def _parse_int(self, value: object, *, default: int) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            stripped = value.strip().lower().replace("_", "")
            try:
                if stripped.startswith("0x"):
                    return int(stripped, 16)
                return int(stripped, 10)
            except Exception:
                return default
        return default

    def _parse_field_mask(self, bits_value: object) -> int:
        if isinstance(bits_value, int):
            if bits_value < 0 or bits_value > 31:
                return 0
            return (1 << bits_value) & 0xFFFFFFFF

        if isinstance(bits_value, str):
            token = bits_value.strip().lower().replace("_", "")
            if ":" in token:
                left, right = token.split(":", 1)
                msb = self._parse_int(left, default=-1)
                lsb = self._parse_int(right, default=-1)
                if msb < 0 or lsb < 0:
                    return 0
                hi = max(msb, lsb)
                lo = min(msb, lsb)
                if hi > 31 or lo > 31:
                    return 0
                width = hi - lo + 1
                return (((1 << width) - 1) << lo) & 0xFFFFFFFF

            bit = self._parse_int(token, default=-1)
            if bit < 0 or bit > 31:
                return 0
            return (1 << bit) & 0xFFFFFFFF

        if isinstance(bits_value, list):
            mask = 0
            for item in bits_value:
                mask |= self._parse_field_mask(item)
            return mask & 0xFFFFFFFF

        return 0

    def _pick_signal(self, candidates: list[str], *, default: str) -> str:
        if not candidates:
            return default
        preferred_order = [
            "clk_i",
            "clk",
            "clock",
            "rst_ni",
            "rst_n",
            "reset_n",
            "rst_i",
            "rst",
        ]

        lowered = {c.lower(): c for c in candidates}
        for pref in preferred_order:
            if pref in lowered:
                return lowered[pref]
        return candidates[0]

    def _write_testbench_files(
        self,
        *,
        output_dir: Path,
        clock_name: str,
        reset_name: str,
        protocol_hint: str,
        registers: list[dict],
    ) -> None:
        write_text(output_dir / "testbench" / "__init__.py", "")
        write_text(output_dir / "testbench" / "agents" / "__init__.py", "")
        write_text(output_dir / "testbench" / "ref_model" / "__init__.py", "")
        write_text(output_dir / "testbench" / "scoreboard" / "__init__.py", "")
        write_text(output_dir / "testbench" / "coverage" / "__init__.py", "")

        tl_ul_agent = textwrap.dedent(
            f'''\
            from __future__ import annotations

            from typing import Any

            import cocotb
            from cocotb.triggers import RisingEdge


            class TlUlDriver:
                """Reusable TL-UL CSR driver with dynamic signal lookup."""

                def __init__(self, dut: Any, clk_signal: str = "{clock_name}", rst_signal: str = "{reset_name}") -> None:
                    self.dut = dut
                    self.clk = getattr(dut, clk_signal)
                    self.rst = getattr(dut, rst_signal)

                def _set_if_present(self, name: str, value: int) -> None:
                    sig = getattr(self.dut, name, None)
                    if sig is not None:
                        sig.value = value

                def _get_if_present(self, name: str, default: int = 0) -> int:
                    sig = getattr(self.dut, name, None)
                    if sig is None:
                        return default
                    try:
                        return int(sig.value)
                    except Exception:
                        return default

                async def apply_reset(self, cycles: int = 5) -> None:
                    # Supports active-low and active-high reset naming patterns.
                    active_low = self.rst._name.lower().endswith("n")
                    self.rst.value = 0 if active_low else 1
                    for _ in range(max(1, cycles)):
                        await RisingEdge(self.clk)
                    self.rst.value = 1 if active_low else 0
                    await RisingEdge(self.clk)

                async def csr_write(self, addr: int, data: int, mask: int = 0xF, timeout_cycles: int = 100) -> dict:
                    self._set_if_present("tl_a_valid", 1)
                    self._set_if_present("tl_a_opcode", 0)
                    self._set_if_present("tl_a_address", addr)
                    self._set_if_present("tl_a_data", data)
                    self._set_if_present("tl_a_mask", mask)
                    self._set_if_present("tl_a_size", 2)

                    for _ in range(timeout_cycles):
                        await RisingEdge(self.clk)
                        if self._get_if_present("tl_a_ready", 1):
                            break

                    self._set_if_present("tl_a_valid", 0)

                    self._set_if_present("tl_d_ready", 1)
                    for _ in range(timeout_cycles):
                        await RisingEdge(self.clk)
                        if self._get_if_present("tl_d_valid", 1):
                            break

                    return {{
                        "error": self._get_if_present("tl_d_error", 0),
                        "data": self._get_if_present("tl_d_data", 0),
                    }}

                async def csr_read(self, addr: int, mask: int = 0xF, timeout_cycles: int = 100) -> dict:
                    self._set_if_present("tl_a_valid", 1)
                    self._set_if_present("tl_a_opcode", 4)
                    self._set_if_present("tl_a_address", addr)
                    self._set_if_present("tl_a_mask", mask)
                    self._set_if_present("tl_a_size", 2)

                    for _ in range(timeout_cycles):
                        await RisingEdge(self.clk)
                        if self._get_if_present("tl_a_ready", 1):
                            break

                    self._set_if_present("tl_a_valid", 0)

                    self._set_if_present("tl_d_ready", 1)
                    for _ in range(timeout_cycles):
                        await RisingEdge(self.clk)
                        if self._get_if_present("tl_d_valid", 1):
                            break

                    return {{
                        "error": self._get_if_present("tl_d_error", 0),
                        "data": self._get_if_present("tl_d_data", 0),
                    }}


            class TlUlMonitor:
                """Minimal monitor placeholder to extend with protocol-level analysis."""

                def __init__(self, dut: Any) -> None:
                    self.dut = dut
                    self.samples: list[dict] = []

                def sample(self) -> None:
                    self.samples.append({{
                        "a_valid": int(getattr(self.dut, "tl_a_valid", 0).value) if hasattr(self.dut, "tl_a_valid") else 0,
                        "a_ready": int(getattr(self.dut, "tl_a_ready", 0).value) if hasattr(self.dut, "tl_a_ready") else 0,
                        "d_valid": int(getattr(self.dut, "tl_d_valid", 0).value) if hasattr(self.dut, "tl_d_valid") else 0,
                        "d_ready": int(getattr(self.dut, "tl_d_ready", 0).value) if hasattr(self.dut, "tl_d_ready") else 0,
                    }})
            '''
        )
        write_text(output_dir / "testbench" / "agents" / "tl_ul_agent.py", tl_ul_agent)

        ref_model = textwrap.dedent(
            '''\
            from __future__ import annotations


            class ReferenceModel:
                """Reference model tracks CSR values and predicts readback behavior."""

                def __init__(self) -> None:
                    self.csr_mirror: dict[int, int] = {}

                def apply_reset(self) -> None:
                    self.csr_mirror.clear()

                def write(self, addr: int, data: int) -> None:
                    self.csr_mirror[addr] = data & 0xFFFFFFFF

                def read(self, addr: int) -> int:
                    return self.csr_mirror.get(addr, 0)
            '''
        )
        write_text(
            output_dir / "testbench" / "ref_model" / "reference_model.py", ref_model
        )

        scoreboard = textwrap.dedent(
            '''\
            from __future__ import annotations


            class Scoreboard:
                """Simple scoreboard comparing expected and observed CSR reads."""

                def __init__(self) -> None:
                    self.mismatches: list[str] = []

                def check_read(self, *, addr: int, expected: int, observed: int) -> None:
                    if (expected & 0xFFFFFFFF) != (observed & 0xFFFFFFFF):
                        self.mismatches.append(
                            f"addr=0x{addr:08X} expected=0x{expected:08X} observed=0x{observed:08X}"
                        )

                def assert_clean(self) -> None:
                    assert not self.mismatches, "Scoreboard mismatches:\\n" + "\\n".join(self.mismatches)
            '''
        )
        write_text(
            output_dir / "testbench" / "scoreboard" / "scoreboard.py", scoreboard
        )

        register_addrs = sorted(
            {int(r.get("address", 0)) & 0xFFFFFFFF for r in registers}
        )[:32]
        register_literal = (
            ", ".join(f"0x{addr:X}" for addr in register_addrs)
            if register_addrs
            else "0x0"
        )

        coverage = textwrap.dedent(
            f'''\
            from __future__ import annotations


            class CoverageCollector:
                """DUT-generic functional coverage with richer bin dimensions."""

                def __init__(self, register_addrs: list[int] | None = None) -> None:
                    self.register_addrs = register_addrs or [{register_literal}]
                    self.counters: dict[str, int] = {{}}
                    self._define_bins()

                def _define_bins(self) -> None:
                    static_bins = [
                        "reset_sequence",
                        "error_path",
                        "operation_read",
                        "operation_write",
                        "operation_error",
                    ]
                    for name in static_bins:
                        self.counters[name] = 0

                    for op in ("read", "write"):
                        for idx, _addr in enumerate(self.register_addrs):
                            self.counters[f"op_{{op}}_reg_{{idx:02d}}"] = 0

                    for region in ("low", "mid", "high"):
                        for op in ("read", "write"):
                            self.counters[f"op_{{op}}_region_{{region}}"] = 0

                    for pattern in ("zero", "ones", "alternating", "sparse", "random"):
                        self.counters[f"write_data_pattern_{{pattern}}"] = 0

                    for region in ("low", "mid", "high"):
                        for pattern in ("zero", "ones", "alternating", "sparse", "random"):
                            self.counters[f"cross_write_region_{{region}}_pattern_{{pattern}}"] = 0

                def hit(self, bin_name: str) -> None:
                    if bin_name in self.counters:
                        self.counters[bin_name] += 1

                def _classify_addr_region(self, addr: int) -> str:
                    if addr < 0x100:
                        return "low"
                    if addr < 0x400:
                        return "mid"
                    return "high"

                def _classify_data_pattern(self, data: int) -> str:
                    value = int(data) & 0xFFFFFFFF
                    if value == 0:
                        return "zero"
                    if value == 0xFFFFFFFF:
                        return "ones"
                    if value in (0xAAAAAAAA, 0x55555555):
                        return "alternating"
                    if value & (value - 1) == 0:
                        return "sparse"
                    return "random"

                def hit_operation(
                    self,
                    *,
                    op: str,
                    addr: int | None = None,
                    data: int | None = None,
                    error: bool = False,
                ) -> None:
                    op_name = op.lower().strip()
                    if op_name in ("read", "write"):
                        self.hit(f"operation_{{op_name}}")
                    if error:
                        self.hit("operation_error")
                        self.hit("error_path")

                    if addr is not None:
                        region = self._classify_addr_region(int(addr))
                        if op_name in ("read", "write"):
                            self.hit(f"op_{{op_name}}_region_{{region}}")

                            for idx, reg_addr in enumerate(self.register_addrs):
                                if int(reg_addr) == int(addr):
                                    self.hit(f"op_{{op_name}}_reg_{{idx:02d}}")
                                    break

                    if op_name == "write" and data is not None:
                        pattern = self._classify_data_pattern(int(data))
                        self.hit(f"write_data_pattern_{{pattern}}")
                        if addr is not None:
                            region = self._classify_addr_region(int(addr))
                            self.hit(f"cross_write_region_{{region}}_pattern_{{pattern}}")

                def snapshot(self) -> dict[str, int]:
                    return dict(self.counters)
            '''
        )
        write_text(output_dir / "testbench" / "coverage" / "coverage.py", coverage)

        protocol_agent = textwrap.dedent(
            f'''\
            from __future__ import annotations

            from typing import Any


            class ProtocolAgent:
                """Protocol-side agent placeholder selected from ANALYZE-stage hints."""

                def __init__(self, dut: Any, protocol: str = "{protocol_hint}") -> None:
                    self.dut = dut
                    self.protocol = protocol

                async def configure_default(self) -> None:
                    # Intentionally lightweight to remain generic across unseen DUTs.
                    return

                async def drive_idle(self) -> None:
                    return
            '''
        )
        write_text(
            output_dir / "testbench" / "agents" / "protocol_agent.py", protocol_agent
        )

        env_py = textwrap.dedent(
            f'''\
            from __future__ import annotations

            from typing import Any

            from agents.protocol_agent import ProtocolAgent
            from agents.tl_ul_agent import TlUlDriver, TlUlMonitor
            from coverage.coverage import CoverageCollector
            from ref_model.reference_model import ReferenceModel
            from scoreboard.scoreboard import Scoreboard


            class VerificationEnv:
                """Top-level environment wiring agent, model, scoreboard, and coverage."""

                def __init__(self, dut: Any) -> None:
                    self.dut = dut
                    self.tl_driver = TlUlDriver(dut, clk_signal="{clock_name}", rst_signal="{reset_name}")
                    self.tl_monitor = TlUlMonitor(dut)
                    self.protocol_agent = ProtocolAgent(dut, protocol="{protocol_hint}")
                    self.ref_model = ReferenceModel()
                    self.scoreboard = Scoreboard()
                    self.coverage = CoverageCollector()
            '''
        )
        write_text(output_dir / "testbench" / "env.py", env_py)

    def _write_tests(
        self,
        *,
        output_dir: Path,
        plan: dict,
        registers: list[dict],
        clock_name: str,
        reset_name: str,
        analysis: dict,
    ) -> dict:
        protocol_hint = self._pick_protocol_hint(analysis.get("protocol_hints", []))

        register_entries: list[dict[str, int | str]] = []
        for entry in registers:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name", "unnamed")).strip() or "unnamed"
            addr = int(entry.get("address", 0)) & 0xFFFFFFFF
            resval = int(entry.get("resval", 0)) & 0xFFFFFFFF
            swaccess = str(entry.get("swaccess", "rw")).strip().lower() or "rw"
            valid_mask = int(entry.get("valid_mask", 0xFFFFFFFF)) & 0xFFFFFFFF
            writable_mask = int(entry.get("writable_mask", 0)) & 0xFFFFFFFF
            register_entries.append(
                {
                    "name": name,
                    "address": addr,
                    "resval": resval,
                    "swaccess": swaccess,
                    "valid_mask": valid_mask,
                    "writable_mask": writable_mask,
                }
            )

        if not register_entries:
            register_entries = [
                {
                    "name": "REG0",
                    "address": 0x0,
                    "resval": 0x0,
                    "swaccess": "rw",
                    "valid_mask": 0xFFFFFFFF,
                    "writable_mask": 0xFFFFFFFF,
                },
                {
                    "name": "REG1",
                    "address": 0x4,
                    "resval": 0x0,
                    "swaccess": "rw",
                    "valid_mask": 0xFFFFFFFF,
                    "writable_mask": 0xFFFFFFFF,
                },
            ]

        register_entries.sort(key=lambda x: int(x.get("address", 0)))
        mapped_addrs = sorted({int(r.get("address", 0)) & 0xFFFFFFFF for r in register_entries})

        def _match_keywords(name: str, keywords: set[str]) -> bool:
            lowered = name.lower()
            return any(token in lowered for token in keywords)

        volatile_keywords = {
            "status",
            "state",
            "data",
            "fifo",
            "tx",
            "rx",
            "intr",
            "error",
            "count",
            "digest",
            "mtime",
            "cmp",
            "trigger",
            "cmd",
            "command",
            "ready",
            "active",
        }
        ctrl_keywords = {
            "ctrl",
            "cfg",
            "config",
            "mode",
            "enable",
            "timing",
            "dir",
            "prescaler",
            "ovrd",
            "command",
            "cmd",
            "watchdog",
        }
        status_keywords = {
            "status",
            "state",
            "level",
            "count",
            "idle",
            "empty",
            "full",
            "error",
            "ready",
            "active",
        }
        data_keywords = {
            "data",
            "tx",
            "rx",
            "key",
            "iv",
            "digest",
            "mtime",
            "cmp",
            "threshold",
        }
        fifo_keywords = {"fifo", "txdata", "rxdata", "fdata", "rdata", "watermark", "fmt", "acq"}
        intr_keywords = {"intr", "irq", "interrupt"}

        rw_addrs: list[int] = []
        ro_addrs: list[int] = []
        stable_rw_addrs: list[int] = []
        ctrl_addrs: list[int] = []
        status_addrs: list[int] = []
        data_addrs: list[int] = []
        fifo_addrs: list[int] = []
        intr_addrs: list[int] = []

        for reg in register_entries:
            addr = int(reg["address"])
            name = str(reg["name"]).lower()
            swaccess = str(reg["swaccess"]).lower()

            readable = "wo" not in swaccess
            writable = "ro" not in swaccess

            if readable and not writable:
                ro_addrs.append(addr)
            if writable:
                rw_addrs.append(addr)
                if readable and not _match_keywords(name, volatile_keywords):
                    stable_rw_addrs.append(addr)

            if _match_keywords(name, ctrl_keywords):
                ctrl_addrs.append(addr)
            if _match_keywords(name, status_keywords):
                status_addrs.append(addr)
            if _match_keywords(name, data_keywords):
                data_addrs.append(addr)
            if _match_keywords(name, fifo_keywords):
                fifo_addrs.append(addr)
            if _match_keywords(name, intr_keywords):
                intr_addrs.append(addr)

        if not stable_rw_addrs and rw_addrs:
            stable_rw_addrs = rw_addrs[: min(6, len(rw_addrs))]

        max_mapped = max(mapped_addrs) if mapped_addrs else 0
        unmapped_addrs = sorted(
            {
                0x3FC,
                0x7FC,
                0xFFC,
                (max_mapped + 0x04) & 0xFFFFFFFF,
                (max_mapped + 0x100) & 0xFFFFFFFF,
                (max_mapped + 0x200) & 0xFFFFFFFF,
            }
            - set(mapped_addrs)
        )
        if not unmapped_addrs:
            unmapped_addrs = [0x3FC, 0x7FC, 0xFFC]

        def _hex_list(values: list[int]) -> str:
            return "[" + ", ".join(f"0x{int(v) & 0xFFFFFFFF:X}" for v in values) + "]"

        def _normalize_specs(
            raw_specs: object,
            *,
            fallback_name: str,
            fallback_intent: str,
        ) -> list[dict[str, str]]:
            specs: list[dict[str, str]] = []
            if isinstance(raw_specs, list):
                for idx, item in enumerate(raw_specs, start=1):
                    if not isinstance(item, dict):
                        continue
                    name = (
                        str(item.get("name", f"{fallback_name}_{idx}")).strip()
                        or f"{fallback_name}_{idx}"
                    )
                    intent = (
                        str(item.get("intent", "")).strip()
                        or "Plan-defined verification scenario."
                    )
                    specs.append({"name": name, "intent": intent})

            if not specs:
                specs.append({"name": fallback_name, "intent": fallback_intent})
            return specs

        directed_specs = _normalize_specs(
            plan.get("directed_tests", []),
            fallback_name="directed_csr_validation",
            fallback_intent="Directed verification of mapped CSR behavior and protocol safety.",
        )
        random_specs = _normalize_specs(
            plan.get("random_tests", []),
            fallback_name="random_csr_stress",
            fallback_intent="Constrained-random verification of CSR and control/data interactions.",
        )

        directed_functions: list[str] = []
        used_directed_names: set[str] = set()
        for idx, spec in enumerate(directed_specs, start=1):
            fn_name = self._make_unique_test_name(
                prefix="test_directed_", raw_name=spec["name"], used=used_directed_names
            )
            tags = self._infer_scenario_tags(
                name=spec["name"], intent=spec["intent"], lane="directed"
            )
            directed_functions.append(
                self._render_directed_semantic_test(
                    fn_name=fn_name,
                    scenario_name=spec["name"],
                    scenario_intent=spec["intent"],
                    scenario_idx=idx,
                    tags=tags,
                )
            )

        random_functions: list[str] = []
        used_random_names: set[str] = set()
        for idx, spec in enumerate(random_specs, start=1):
            fn_name = self._make_unique_test_name(
                prefix="test_random_", raw_name=spec["name"], used=used_random_names
            )
            tags = self._infer_scenario_tags(
                name=spec["name"], intent=spec["intent"], lane="random"
            )
            random_functions.append(
                self._render_random_semantic_test(
                    fn_name=fn_name,
                    scenario_name=spec["name"],
                    scenario_intent=spec["intent"],
                    scenario_idx=idx,
                    tags=tags,
                )
            )

        register_table_literal = json.dumps(register_entries, indent=2)
        directed_catalog_literal = json.dumps(directed_specs, indent=2)
        random_catalog_literal = json.dumps(random_specs, indent=2)

        directed_header = "\n".join(
            [
                "from __future__ import annotations",
                "",
                "import json",
                "import os",
                "import random",
                "import sys",
                "from pathlib import Path",
                "",
                "import cocotb",
                "from cocotb.clock import Clock",
                "from cocotb.triggers import RisingEdge",
                "",
                "THIS_DIR = Path(__file__).resolve().parent",
                "TB_ROOT = THIS_DIR.parent.parent / \"testbench\"",
                "if str(TB_ROOT) not in sys.path:",
                "    sys.path.insert(0, str(TB_ROOT))",
                "",
                "if str(THIS_DIR.parent) not in sys.path:",
                "    sys.path.insert(0, str(THIS_DIR.parent))",
                "",
                "from agents.tl_ul_agent import TlUlDriver",
                "from coverage.coverage import CoverageCollector",
                "from ref_model.reference_model import ReferenceModel",
                "from scoreboard.scoreboard import Scoreboard",
                "",
                f"REG_ADDRS = {_hex_list(mapped_addrs)}",
                f"REGISTER_TABLE = {register_table_literal}",
                f"DIRECTED_SCENARIOS = {directed_catalog_literal}",
                f"RW_ADDRS = {_hex_list(sorted(set(rw_addrs)))}",
                f"RO_ADDRS = {_hex_list(sorted(set(ro_addrs)))}",
                f"STABLE_RW_ADDRS = {_hex_list(sorted(set(stable_rw_addrs)))}",
                f"CTRL_ADDRS = {_hex_list(sorted(set(ctrl_addrs)))}",
                f"STATUS_ADDRS = {_hex_list(sorted(set(status_addrs)))}",
                f"DATA_ADDRS = {_hex_list(sorted(set(data_addrs)))}",
                f"FIFO_ADDRS = {_hex_list(sorted(set(fifo_addrs)))}",
                f"INTR_ADDRS = {_hex_list(sorted(set(intr_addrs)))}",
                f"UNMAPPED_ADDRS = {_hex_list(unmapped_addrs)}",
                f"PROTOCOL_HINT = {json.dumps(protocol_hint)}",
            ]
        )

        random_header = "\n".join(
            [
                "from __future__ import annotations",
                "",
                "import json",
                "import os",
                "import random",
                "import sys",
                "from pathlib import Path",
                "",
                "import cocotb",
                "from cocotb.clock import Clock",
                "from cocotb.triggers import RisingEdge",
                "",
                "THIS_DIR = Path(__file__).resolve().parent",
                "TB_ROOT = THIS_DIR.parent.parent / \"testbench\"",
                "if str(TB_ROOT) not in sys.path:",
                "    sys.path.insert(0, str(TB_ROOT))",
                "",
                "if str(THIS_DIR.parent) not in sys.path:",
                "    sys.path.insert(0, str(THIS_DIR.parent))",
                "",
                "from agents.tl_ul_agent import TlUlDriver",
                "from coverage.coverage import CoverageCollector",
                "from ref_model.reference_model import ReferenceModel",
                "from scoreboard.scoreboard import Scoreboard",
                "",
                f"REG_ADDRS = {_hex_list(mapped_addrs)}",
                f"REGISTER_TABLE = {register_table_literal}",
                f"RANDOM_SCENARIOS = {random_catalog_literal}",
                f"RW_ADDRS = {_hex_list(sorted(set(rw_addrs)))}",
                f"RO_ADDRS = {_hex_list(sorted(set(ro_addrs)))}",
                f"STABLE_RW_ADDRS = {_hex_list(sorted(set(stable_rw_addrs)))}",
                f"CTRL_ADDRS = {_hex_list(sorted(set(ctrl_addrs)))}",
                f"STATUS_ADDRS = {_hex_list(sorted(set(status_addrs)))}",
                f"DATA_ADDRS = {_hex_list(sorted(set(data_addrs)))}",
                f"FIFO_ADDRS = {_hex_list(sorted(set(fifo_addrs)))}",
                f"INTR_ADDRS = {_hex_list(sorted(set(intr_addrs)))}",
                f"UNMAPPED_ADDRS = {_hex_list(unmapped_addrs)}",
                f"PROTOCOL_HINT = {json.dumps(protocol_hint)}",
            ]
        )

        common_helpers = self._render_semantic_common_helpers(
            clock_name=clock_name, reset_name=reset_name
        )
        random_helpers = self._render_semantic_random_helpers()

        directed_test = (
            directed_header
            + "\n\n"
            + common_helpers
            + "\n\n"
            + "\n\n".join(directed_functions)
            + "\n"
        )
        write_text(
            output_dir / "tests" / "directed" / "test_directed_plan_cases.py",
            directed_test,
        )

        random_test = (
            random_header
            + "\n\n"
            + common_helpers
            + "\n\n"
            + random_helpers
            + "\n\n"
            + "\n\n".join(random_functions)
            + "\n"
        )
        write_text(
            output_dir / "tests" / "random" / "test_random_plan_cases.py",
            random_test,
        )

        plan_tests = textwrap.dedent(
            """\
            # Auto-generated test intent summary
            #
            # Directed tests:
            """
        )
        for item in directed_specs:
            plan_tests += f"# - {item.get('name', 'unnamed')}: {item.get('intent', '')}\n"
        plan_tests += "#\n# Random tests:\n"
        for item in random_specs:
            plan_tests += f"# - {item.get('name', 'unnamed')}: {item.get('intent', '')}\n"

        write_text(output_dir / "tests" / "test_intent_manifest.py", plan_tests)

        return {
            "directed_test_case_count": len(directed_specs),
            "random_test_case_count": len(random_specs),
            "directed_test_file_count": 1,
            "random_test_file_count": 1,
        }

    def _infer_scenario_tags(self, *, name: str, intent: str, lane: str) -> list[str]:
        text = f"{name} {intent}".lower()
        tags: set[str] = set()

        if any(k in text for k in ["reset", "default", "idle", "boot"]):
            tags.add("reset")
        if any(k in text for k in ["csr", "tl", "register", "read", "write"]):
            tags.add("csr")
        if any(k in text for k in ["ctrl", "cfg", "mode", "enable", "disable", "baud", "parity", "stop"]):
            tags.add("control")
        if any(k in text for k in ["tx", "rx", "fifo", "loopback", "frame", "overrun", "overflow", "watermark", "data"]):
            tags.add("datapath")
        if any(k in text for k in ["intr", "interrupt", "w1c", "irq"]):
            tags.add("interrupt")
        if any(k in text for k in ["unmapped", "reserved", "illegal", "error response"]):
            tags.add("unmapped")
        if any(k in text for k in ["external", "uart_rx", "parity error", "frame error"]):
            tags.add("external_rx")

        if lane == "random":
            tags.add("csr")
        if not tags:
            tags.add("csr")
        return sorted(tags)

    def _render_directed_semantic_test(
        self,
        *,
        fn_name: str,
        scenario_name: str,
        scenario_intent: str,
        scenario_idx: int,
        tags: list[str],
    ) -> str:
        minimum_ops = 6 + len(tags) * 2
        return textwrap.dedent(
            f'''\
            @cocotb.test()
            async def {fn_name}(dut):
                """Directed verification scenario from plan."""
                scenario_name = {json.dumps(scenario_name)}
                scenario_intent = {json.dumps(scenario_intent)}
                scenario_tags = {json.dumps(tags)}
                seed = (sum(ord(ch) for ch in scenario_name) + {scenario_idx} * 31337) & 0xFFFFFFFF
                rng = random.Random(seed)

                _clk, driver, coverage, model, scoreboard = await _setup_context(
                    dut, reset_cycles=6 + ({scenario_idx} % 3)
                )

                successful_ops = 0
                unmapped_errors = 0

                if "reset" in scenario_tags:
                    successful_ops += await _exercise_reset_readback(driver=driver, coverage=coverage)
                if "csr" in scenario_tags or "control" in scenario_tags:
                    successful_ops += await _exercise_rw_mirror(
                        driver=driver,
                        coverage=coverage,
                        model=model,
                        scoreboard=scoreboard,
                        rng=rng,
                        steps=6 + ({scenario_idx} % 4),
                    )
                if "control" in scenario_tags:
                    successful_ops += await _exercise_control_programming(
                        driver=driver,
                        coverage=coverage,
                        model=model,
                        scoreboard=scoreboard,
                        rng=rng,
                    )
                if "datapath" in scenario_tags:
                    successful_ops += await _exercise_datapath(
                        driver=driver,
                        coverage=coverage,
                        rng=rng,
                        steps=8 + ({scenario_idx} % 5),
                    )
                if "interrupt" in scenario_tags:
                    successful_ops += await _exercise_interrupts(
                        driver=driver,
                        coverage=coverage,
                        rng=rng,
                    )
                if "unmapped" in scenario_tags:
                    unmapped_errors += await _exercise_unmapped_accesses(
                        driver=driver,
                        coverage=coverage,
                    )

                if "unmapped" in scenario_tags:
                    # Some DUTs ignore out-of-map accesses instead of asserting d_error.
                    # Keep this as a characterization datapoint, not a hard failure.
                    if unmapped_errors > 0:
                        coverage.hit("operation_error")

                scoreboard.assert_clean()
                assert successful_ops >= {minimum_ops}, (
                    f"Insufficient semantic operations for directed scenario {{scenario_name}}: {{successful_ops}} < {minimum_ops}"
                )
                _record_func_cov(f"directed::{{scenario_name}}", coverage.snapshot())
            '''
        ).strip()

    def _render_random_semantic_test(
        self,
        *,
        fn_name: str,
        scenario_name: str,
        scenario_intent: str,
        scenario_idx: int,
        tags: list[str],
    ) -> str:
        minimum_ops = 10 + len(tags) * 3
        return textwrap.dedent(
            f'''\
            @cocotb.test()
            async def {fn_name}(dut):
                """Constrained-random verification scenario from plan."""
                scenario_name = {json.dumps(scenario_name)}
                scenario_intent = {json.dumps(scenario_intent)}
                scenario_tags = {json.dumps(tags)}
                seed = (sum(ord(ch) for ch in scenario_name) + {scenario_idx} * 81173) & 0xFFFFFFFF
                rng = random.Random(seed)

                clk, driver, coverage, model, scoreboard = await _setup_context(
                    dut, reset_cycles=6
                )

                successful_ops = 0

                successful_ops += await _run_random_csr_regression(
                    driver=driver,
                    coverage=coverage,
                    model=model,
                    scoreboard=scoreboard,
                    rng=rng,
                    steps=20 + ({scenario_idx} % 6) * 4,
                )

                if "datapath" in scenario_tags:
                    successful_ops += await _run_random_datapath_traffic(
                        driver=driver,
                        coverage=coverage,
                        rng=rng,
                        steps=14 + ({scenario_idx} % 5) * 3,
                    )
                if "interrupt" in scenario_tags:
                    successful_ops += await _run_random_interrupt_stress(
                        driver=driver,
                        coverage=coverage,
                        rng=rng,
                        steps=10 + ({scenario_idx} % 4) * 3,
                    )
                if "external_rx" in scenario_tags:
                    successful_ops += await _run_random_external_rx_frames(
                        dut=dut,
                        clk=clk,
                        driver=driver,
                        coverage=coverage,
                        rng=rng,
                        frames=6 + ({scenario_idx} % 4),
                    )
                if "reset" in scenario_tags:
                    reset_ops = await _run_random_reset_stress(
                        driver=driver,
                        coverage=coverage,
                        model=model,
                        rng=rng,
                        steps=12 + ({scenario_idx} % 4) * 4,
                    )
                    successful_ops += reset_ops
                    assert reset_ops > 0, f"Expected reset operations in scenario {{scenario_name}}"

                scoreboard.assert_clean()
                assert successful_ops >= {minimum_ops}, (
                    f"Insufficient semantic operations for random scenario {{scenario_name}}: {{successful_ops}} < {minimum_ops}"
                )
                _record_func_cov(f"random::{{scenario_name}}", coverage.snapshot())
            '''
        ).strip()

    def _render_semantic_common_helpers(self, *, clock_name: str, reset_name: str) -> str:
        return textwrap.dedent(
            f'''\
            def _record_func_cov(tag: str, counters: dict) -> None:
                out_file = os.getenv("AUTOVERIFIER_FUNC_COV_FILE", "").strip()
                if not out_file:
                    return
                cov_path = Path(out_file)
                cov_path.parent.mkdir(parents=True, exist_ok=True)
                payload = {{}}
                if cov_path.exists():
                    try:
                        payload = json.loads(cov_path.read_text(encoding="utf-8"))
                    except Exception:
                        payload = {{}}
                payload[tag] = counters
                cov_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


            NAME_BY_ADDR = {{int(reg.get("address", 0)): str(reg.get("name", "")).lower() for reg in REGISTER_TABLE}}
            SWACCESS_BY_ADDR = {{int(reg.get("address", 0)): str(reg.get("swaccess", "rw")).lower() for reg in REGISTER_TABLE}}
            RESVAL_BY_ADDR = {{int(reg.get("address", 0)): int(reg.get("resval", 0)) & 0xFFFFFFFF for reg in REGISTER_TABLE}}
            VALID_MASK_BY_ADDR = {{
                int(reg.get("address", 0)): int(reg.get("valid_mask", 0xFFFFFFFF)) & 0xFFFFFFFF
                for reg in REGISTER_TABLE
            }}
            WRITABLE_MASK_BY_ADDR = {{
                int(reg.get("address", 0)): int(reg.get("writable_mask", 0)) & 0xFFFFFFFF
                for reg in REGISTER_TABLE
            }}


            def _is_readable(addr: int) -> bool:
                mode = SWACCESS_BY_ADDR.get(int(addr), "rw")
                return "wo" not in mode


            def _is_writable(addr: int) -> bool:
                mode = SWACCESS_BY_ADDR.get(int(addr), "rw")
                if "ro" in mode and "w" not in mode:
                    return False
                if int(WRITABLE_MASK_BY_ADDR.get(int(addr), 0)) == 0 and "w" not in mode:
                    return False
                return True


            def _valid_mask(addr: int) -> int:
                return int(VALID_MASK_BY_ADDR.get(int(addr), 0xFFFFFFFF)) & 0xFFFFFFFF


            def _writable_mask(addr: int) -> int:
                mask = int(WRITABLE_MASK_BY_ADDR.get(int(addr), 0)) & 0xFFFFFFFF
                if mask == 0 and "w" in SWACCESS_BY_ADDR.get(int(addr), ""):
                    return _valid_mask(int(addr))
                return mask


            def _masked_compare(addr: int, expected: int, observed: int) -> tuple[int, int]:
                mask = _valid_mask(int(addr))
                return int(expected) & mask, int(observed) & mask


            def _apply_write_mask(addr: int, data: int) -> int:
                wmask = _writable_mask(int(addr))
                return int(data) & wmask


            def _is_stable(addr: int) -> bool:
                return int(addr) in set(STABLE_RW_ADDRS)


            def _pattern_word(seed: int, index: int) -> int:
                base = [
                    0x00000000,
                    0xFFFFFFFF,
                    0xA5A5A5A5,
                    0x5A5A5A5A,
                    0x12345678,
                    0x87654321,
                ]
                mix = (seed ^ ((index + 1) * 0x9E3779B1)) & 0xFFFFFFFF
                return (base[index % len(base)] ^ mix) & 0xFFFFFFFF


            async def _resolve_clock(dut):
                for cand in ({json.dumps(clock_name)}, "clk_i", "clk", "clock"):
                    if hasattr(dut, cand):
                        return getattr(dut, cand)
                raise AssertionError("No clock signal found on DUT (expected clk_i/clk/clock style signal)")


            def _resolve_reset_name(dut) -> str:
                for cand in ({json.dumps(reset_name)}, "rst_ni", "rst_n", "rst_i", "rst", "reset_n", "reset"):
                    if hasattr(dut, cand):
                        return cand
                raise AssertionError("No reset signal found on DUT")


            async def _setup_context(dut, *, reset_cycles: int):
                clk = await _resolve_clock(dut)
                cocotb.start_soon(Clock(clk, 2, unit="step").start())
                driver = TlUlDriver(dut, clk_signal=clk._name, rst_signal=_resolve_reset_name(dut))
                coverage = CoverageCollector(register_addrs=REG_ADDRS)
                model = ReferenceModel()
                scoreboard = Scoreboard()

                await driver.apply_reset(cycles=max(2, int(reset_cycles)))
                coverage.hit("reset_sequence")
                model.apply_reset()

                return clk, driver, coverage, model, scoreboard


            async def _csr_write_checked(driver, coverage, *, addr: int, data: int, allow_error: bool = False, label: str = "") -> dict:
                rsp = await driver.csr_write(addr=int(addr), data=int(data) & 0xFFFFFFFF)
                err = int(rsp.get("error", 0))
                coverage.hit_operation(op="write", addr=int(addr), data=int(data), error=bool(err))
                if not allow_error:
                    assert err == 0, f"Unexpected TL-UL write error at addr=0x{{int(addr):08X}} label={{label}}"
                return rsp


            async def _csr_read_checked(driver, coverage, *, addr: int, allow_error: bool = False, label: str = "") -> tuple[int, int]:
                rsp = await driver.csr_read(addr=int(addr))
                err = int(rsp.get("error", 0))
                data = int(rsp.get("data", 0)) & 0xFFFFFFFF
                coverage.hit_operation(op="read", addr=int(addr), error=bool(err))
                if not allow_error:
                    assert err == 0, f"Unexpected TL-UL read error at addr=0x{{int(addr):08X}} label={{label}}"
                return data, err


            async def _exercise_reset_readback(driver, coverage) -> int:
                ops = 0
                for addr in REG_ADDRS[: min(10, len(REG_ADDRS))]:
                    if not _is_readable(addr):
                        continue
                    data, _err = await _csr_read_checked(driver, coverage, addr=addr, label="reset_readback")
                    expected = RESVAL_BY_ADDR.get(int(addr), 0) & _valid_mask(int(addr))
                    if _is_stable(addr):
                        obs = int(data) & _valid_mask(int(addr))
                        assert obs == expected, (
                            f"Reset mismatch at addr=0x{{int(addr):08X}} expected=0x{{expected:08X}} got=0x{{data:08X}}"
                        )
                    ops += 1
                return ops


            async def _exercise_rw_mirror(driver, coverage, model, scoreboard, rng, *, steps: int) -> int:
                ops = 0
                candidates = STABLE_RW_ADDRS or RW_ADDRS or REG_ADDRS
                if not candidates:
                    return 0

                for step in range(max(4, int(steps))):
                    addr = int(candidates[step % len(candidates)])
                    if not _is_writable(addr):
                        continue
                    data = _apply_write_mask(addr, _pattern_word(rng.getrandbits(32), step))
                    await _csr_write_checked(
                        driver,
                        coverage,
                        addr=addr,
                        data=data,
                        label="rw_mirror_write",
                    )
                    model.write(addr, data)
                    ops += 1

                    if _is_stable(addr) and _is_readable(addr):
                        read_data, _ = await _csr_read_checked(
                            driver,
                            coverage,
                            addr=addr,
                            label="rw_mirror_read",
                        )
                        exp_masked, obs_masked = _masked_compare(addr, model.read(addr), read_data)
                        scoreboard.check_read(
                            addr=addr,
                            expected=exp_masked,
                            observed=obs_masked,
                        )
                        ops += 1
                return ops


            async def _exercise_control_programming(driver, coverage, model, scoreboard, rng) -> int:
                ops = 0
                targets = CTRL_ADDRS or STABLE_RW_ADDRS or RW_ADDRS
                for idx, addr in enumerate(targets[: min(6, len(targets))]):
                    if not _is_writable(addr):
                        continue
                    data = _apply_write_mask(int(addr), _pattern_word(rng.getrandbits(32), idx + 11))
                    await _csr_write_checked(
                        driver,
                        coverage,
                        addr=int(addr),
                        data=data,
                        label="control_programming_write",
                    )
                    model.write(int(addr), data)
                    ops += 1

                    if _is_stable(int(addr)) and _is_readable(int(addr)):
                        observed, _ = await _csr_read_checked(
                            driver,
                            coverage,
                            addr=int(addr),
                            label="control_programming_read",
                        )
                        exp_masked, obs_masked = _masked_compare(
                            int(addr), model.read(int(addr)), observed
                        )
                        scoreboard.check_read(
                            addr=int(addr),
                            expected=exp_masked,
                            observed=obs_masked,
                        )
                        ops += 1
                return ops


            async def _exercise_datapath(driver, coverage, rng, *, steps: int) -> int:
                ops = 0
                write_targets = [a for a in (DATA_ADDRS + FIFO_ADDRS) if _is_writable(a)]
                read_targets = [a for a in (STATUS_ADDRS + DATA_ADDRS) if _is_readable(a)]

                if not write_targets and RW_ADDRS:
                    write_targets = [a for a in RW_ADDRS if _is_writable(a)][:4]
                if not read_targets and REG_ADDRS:
                    read_targets = [a for a in REG_ADDRS if _is_readable(a)][:4]

                for step in range(max(6, int(steps))):
                    if write_targets:
                        addr = int(write_targets[step % len(write_targets)])
                        data = _pattern_word(rng.getrandbits(32), step + 33)
                        await _csr_write_checked(
                            driver,
                            coverage,
                            addr=addr,
                            data=data,
                            label="datapath_write",
                        )
                        ops += 1
                    if read_targets:
                        addr = int(read_targets[step % len(read_targets)])
                        await _csr_read_checked(
                            driver,
                            coverage,
                            addr=addr,
                            label="datapath_read",
                        )
                        ops += 1
                return ops


            async def _exercise_interrupts(driver, coverage, rng) -> int:
                ops = 0
                if not INTR_ADDRS:
                    return 0

                intr_enable = [a for a in INTR_ADDRS if "enable" in NAME_BY_ADDR.get(int(a), "")]
                intr_test = [a for a in INTR_ADDRS if "test" in NAME_BY_ADDR.get(int(a), "")]
                intr_state = [a for a in INTR_ADDRS if "state" in NAME_BY_ADDR.get(int(a), "")]

                for idx, addr in enumerate((intr_enable or INTR_ADDRS)[:2]):
                    if _is_writable(int(addr)):
                        data = (0x1 << idx) | 0x1
                        await _csr_write_checked(
                            driver,
                            coverage,
                            addr=int(addr),
                            data=data,
                            label="intr_enable",
                        )
                        ops += 1

                for idx, addr in enumerate((intr_test or INTR_ADDRS)[:2]):
                    if _is_writable(int(addr)):
                        data = (0x1 << idx) | (rng.getrandbits(1) << 1)
                        await _csr_write_checked(
                            driver,
                            coverage,
                            addr=int(addr),
                            data=data,
                            label="intr_test",
                        )
                        ops += 1

                for addr in (intr_state or INTR_ADDRS)[:2]:
                    if _is_readable(int(addr)):
                        read_data, _ = await _csr_read_checked(
                            driver,
                            coverage,
                            addr=int(addr),
                            label="intr_state_read",
                        )
                        ops += 1
                        if _is_writable(int(addr)):
                            await _csr_write_checked(
                                driver,
                                coverage,
                                addr=int(addr),
                                data=read_data & 0xFFFFFFFF,
                                label="intr_state_w1c",
                            )
                            ops += 1
                return ops


            async def _exercise_unmapped_accesses(driver, coverage) -> int:
                observed_errors = 0
                for idx, addr in enumerate(UNMAPPED_ADDRS):
                    wr = await _csr_write_checked(
                        driver,
                        coverage,
                        addr=int(addr),
                        data=_pattern_word(0xDEADBEEF, idx),
                        allow_error=True,
                        label="unmapped_write",
                    )
                    observed_errors += int(wr.get("error", 0))
                    _data, rd_err = await _csr_read_checked(
                        driver,
                        coverage,
                        addr=int(addr),
                        allow_error=True,
                        label="unmapped_read",
                    )
                    observed_errors += int(rd_err)
                return observed_errors
            '''
        ).strip()

    def _render_semantic_random_helpers(self) -> str:
        return textwrap.dedent(
            '''\
            async def _run_random_csr_regression(driver, coverage, model, scoreboard, rng, *, steps: int) -> int:
                ops = 0
                addr_pool = list(REG_ADDRS) + list(UNMAPPED_ADDRS)
                stable_pool = [int(a) for a in STABLE_RW_ADDRS if _is_writable(int(a))]

                for step in range(max(8, int(steps))):
                    addr = int(rng.choice(addr_pool))
                    do_write = rng.random() < 0.62 and _is_writable(addr)
                    if do_write:
                        data = _pattern_word(rng.getrandbits(32), step + 101)
                        allow_error = addr in UNMAPPED_ADDRS
                        rsp = await _csr_write_checked(
                            driver,
                            coverage,
                            addr=addr,
                            data=data,
                            allow_error=allow_error,
                            label="random_csr_write",
                        )
                        if int(rsp.get("error", 0)) == 0 and addr in stable_pool:
                            model.write(addr, data)
                        ops += 1
                    else:
                        allow_error = addr in UNMAPPED_ADDRS
                        read_data, rd_err = await _csr_read_checked(
                            driver,
                            coverage,
                            addr=addr,
                            allow_error=allow_error,
                            label="random_csr_read",
                        )
                        if rd_err == 0 and addr in stable_pool:
                            scoreboard.check_read(addr=addr, expected=model.read(addr), observed=read_data)
                        ops += 1
                return ops


            async def _run_random_datapath_traffic(driver, coverage, rng, *, steps: int) -> int:
                ops = 0
                write_pool = [int(a) for a in (DATA_ADDRS + FIFO_ADDRS + CTRL_ADDRS) if _is_writable(int(a))]
                read_pool = [int(a) for a in (STATUS_ADDRS + DATA_ADDRS) if _is_readable(int(a))]

                if not write_pool:
                    write_pool = [int(a) for a in RW_ADDRS if _is_writable(int(a))][:6]
                if not read_pool:
                    read_pool = [int(a) for a in REG_ADDRS if _is_readable(int(a))][:6]

                for step in range(max(10, int(steps))):
                    if write_pool and rng.random() < 0.7:
                        addr = int(rng.choice(write_pool))
                        data = _pattern_word(rng.getrandbits(32), step + 211)
                        await _csr_write_checked(
                            driver,
                            coverage,
                            addr=addr,
                            data=data,
                            label="random_datapath_write",
                        )
                        ops += 1
                    if read_pool:
                        addr = int(rng.choice(read_pool))
                        await _csr_read_checked(
                            driver,
                            coverage,
                            addr=addr,
                            label="random_datapath_read",
                        )
                        ops += 1
                return ops


            async def _run_random_interrupt_stress(driver, coverage, rng, *, steps: int) -> int:
                if not INTR_ADDRS:
                    return 0
                ops = 0
                for step in range(max(6, int(steps))):
                    addr = int(INTR_ADDRS[step % len(INTR_ADDRS)])
                    if _is_writable(addr):
                        data = (1 << (step % 8)) | (rng.getrandbits(3) << 8)
                        await _csr_write_checked(
                            driver,
                            coverage,
                            addr=addr,
                            data=data,
                            label="random_intr_write",
                        )
                        ops += 1
                    if _is_readable(addr):
                        await _csr_read_checked(
                            driver,
                            coverage,
                            addr=addr,
                            label="random_intr_read",
                        )
                        ops += 1
                return ops


            async def _run_random_reset_stress(driver, coverage, model, rng, *, steps: int) -> int:
                ops = 0
                for step in range(max(8, int(steps))):
                    if step % 4 == 0:
                        await driver.apply_reset(cycles=2 + (step % 3))
                        coverage.hit("reset_sequence")
                        model.apply_reset()
                        ops += 1

                    if REG_ADDRS:
                        addr = int(REG_ADDRS[step % len(REG_ADDRS)])
                        if _is_writable(addr):
                            data = _pattern_word(rng.getrandbits(32), step + 307)
                            await _csr_write_checked(
                                driver,
                                coverage,
                                addr=addr,
                                data=data,
                                label="random_reset_write",
                            )
                            ops += 1
                        elif _is_readable(addr):
                            await _csr_read_checked(
                                driver,
                                coverage,
                                addr=addr,
                                label="random_reset_read",
                            )
                            ops += 1
                return ops


            async def _wait_cycles(clk, cycles: int) -> None:
                for _ in range(max(1, int(cycles))):
                    await RisingEdge(clk)


            async def _drive_uart_frame(dut, clk, *, byte_val: int, bad_parity: bool, bad_stop: bool) -> bool:
                if not hasattr(dut, "uart_rx_i"):
                    return False

                rx = getattr(dut, "uart_rx_i")
                bit_cycles = 8

                rx.value = 1
                await _wait_cycles(clk, bit_cycles)

                rx.value = 0
                await _wait_cycles(clk, bit_cycles)

                parity = 0
                for i in range(8):
                    bit = (int(byte_val) >> i) & 0x1
                    parity ^= bit
                    rx.value = bit
                    await _wait_cycles(clk, bit_cycles)

                parity_bit = parity & 0x1
                if bad_parity:
                    parity_bit ^= 0x1
                rx.value = parity_bit
                await _wait_cycles(clk, bit_cycles)

                rx.value = 0 if bad_stop else 1
                await _wait_cycles(clk, bit_cycles)

                rx.value = 1
                await _wait_cycles(clk, bit_cycles)
                return True


            async def _run_random_external_rx_frames(dut, clk, driver, coverage, rng, *, frames: int) -> int:
                ops = 0
                driven_any = False
                for idx in range(max(4, int(frames))):
                    byte_val = rng.getrandbits(8)
                    bad_parity = bool(idx % 3 == 1)
                    bad_stop = bool(idx % 5 == 2)
                    driven = await _drive_uart_frame(
                        dut,
                        clk,
                        byte_val=byte_val,
                        bad_parity=bad_parity,
                        bad_stop=bad_stop,
                    )
                    if driven:
                        driven_any = True
                        await _wait_cycles(clk, 1)
                        ops += 1

                read_pool = [int(a) for a in (STATUS_ADDRS + DATA_ADDRS + REG_ADDRS[:3]) if _is_readable(int(a))]
                for addr in read_pool[:6]:
                    await _csr_read_checked(driver, coverage, addr=int(addr), label="external_rx_observe")
                    ops += 1

                if not driven_any:
                    # Graceful fallback for non-UART DUTs: still exercise semantic read path.
                    coverage.hit("error_path")
                return ops
            '''
        ).strip()

    def _write_assertions(self, *, output_dir: Path, reset_name: str) -> None:
        assertions = textwrap.dedent(
            f'''\
            from __future__ import annotations

            import cocotb
            from cocotb.triggers import RisingEdge


            async def assert_reset_deasserts(dut, clk_name: str = "clk_i") -> None:
                """Check that reset eventually deasserts and the design can advance."""
                clk = getattr(dut, clk_name)
                rst = getattr(dut, "{reset_name}")

                for _ in range(32):
                    await RisingEdge(clk)
                    if int(rst.value) in (0, 1):
                        # Active-low/active-high ambiguity handled by waiting for stability.
                        return
                raise AssertionError("Reset did not stabilize within 32 cycles")


            async def assert_tlul_handshake_progress(dut, clk_name: str = "clk_i") -> None:
                """Check valid-ready progress for A channel when interface is present."""
                if not hasattr(dut, "tl_a_valid") or not hasattr(dut, "tl_a_ready"):
                    return

                clk = getattr(dut, clk_name)
                stall_cycles = 0
                for _ in range(128):
                    await RisingEdge(clk)
                    if int(dut.tl_a_valid.value) == 1 and int(dut.tl_a_ready.value) == 0:
                        stall_cycles += 1
                    else:
                        stall_cycles = 0
                    if stall_cycles > 24:
                        raise AssertionError("TL-UL A channel stalled > 24 cycles")
            '''
        )
        write_text(output_dir / "assertions" / "python_assertions.py", assertions)

    def _pick_protocol_hint(self, protocol_hints: list[str]) -> str:
        if not protocol_hints:
            return "csr_only"
        preferred = ["uart", "spi", "i2c", "gpio", "hmac", "aes", "timer"]
        lowered = {p.lower(): p for p in protocol_hints}
        for item in preferred:
            if item in lowered:
                return item
        return protocol_hints[0]

    def _slugify_identifier(self, text: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9_]+", "_", text.strip().lower())
        slug = re.sub(r"_+", "_", slug).strip("_")
        if not slug:
            slug = "scenario"
        if slug[0].isdigit():
            slug = f"s_{slug}"
        return slug

    def _make_unique_test_name(
        self, *, prefix: str, raw_name: str, used: set[str]
    ) -> str:
        base = f"{prefix}{self._slugify_identifier(raw_name)}"
        candidate = base
        suffix = 2
        while candidate in used:
            candidate = f"{base}_{suffix}"
            suffix += 1
        used.add(candidate)
        return candidate

    def _collect_generated_python_files(self, output_dir: Path) -> list[Path]:
        return sorted(
            [p for p in output_dir.rglob("*.py") if "__pycache__" not in p.parts]
        )

    def _augment_rtl_sources(self, rtl_files: list[Path]) -> list[Path]:
        augmented: dict[Path, bool] = {Path(p).resolve(): True for p in rtl_files}
        for rtl in list(augmented.keys()):
            for parent in rtl.parents:
                if parent.name != "duts":
                    continue
                common_dir = parent / "common"
                if common_dir.exists() and common_dir.is_dir():
                    for ext in ("*.sv", "*.v", "*.svh", "*.vh"):
                        for extra in common_dir.glob(ext):
                            augmented[extra.resolve()] = True
                break
        return list(augmented.keys())

    def _order_rtl_sources(self, rtl_files: list[Path]) -> list[Path]:
        def sort_key(path: Path) -> tuple[int, int, str]:
            lowered_name = path.name.lower()
            in_common = 0 if "common" in {p.lower() for p in path.parts} else 1
            is_pkg = 0 if ("pkg" in lowered_name or "package" in lowered_name) else 1
            return (in_common, is_pkg, str(path))

        return sorted(rtl_files, key=sort_key)

    def _resolve_requested_simulators(self, mode: str) -> list[str]:
        normalized = str(mode or "auto").strip().lower()
        if normalized == "icarus":
            return ["icarus"]
        if normalized == "verilator":
            return ["verilator"]
        # both and auto request both when available.
        return ["icarus", "verilator"]

    def _build_pythonpath(self, test_file: Path, output_dir: Path) -> str:
        existing = os.getenv("PYTHONPATH", "")
        candidates = [
            str(test_file.parent.resolve()),
            str((output_dir / "testbench").resolve()),
        ]
        if existing:
            candidates.append(existing)

        deduped: list[str] = []
        seen: set[str] = set()
        for entry in candidates:
            if not entry or entry in seen:
                continue
            seen.add(entry)
            deduped.append(entry)
        return os.pathsep.join(deduped)

    def _to_test_module_name(self, test_file: Path, output_dir: Path) -> str:
        rel = test_file.resolve().relative_to(output_dir.resolve())
        return ".".join(rel.with_suffix("").parts)

    def _parse_results_xml(self, results_xml: Path) -> dict:
        if not results_xml.exists():
            return {"tests": 0, "failures": 0, "errors": 1}
        try:
            root = ET.parse(results_xml).getroot()
            suites = [root] if root.tag == "testsuite" else root.findall(".//testsuite")
            tests = sum(int(s.attrib.get("tests", "0")) for s in suites)
            failures = sum(int(s.attrib.get("failures", "0")) for s in suites)
            errors = sum(int(s.attrib.get("errors", "0")) for s in suites)

            # cocotb xunit output may omit tests/failures/errors attributes,
            # so derive counts from testcase elements when needed.
            if tests == 0 and suites:
                testcases = root.findall(".//testcase")
                tests = len(testcases)
                failures = len(root.findall(".//testcase/failure"))
                errors = len(root.findall(".//testcase/error"))

            return {"tests": tests, "failures": failures, "errors": errors}
        except Exception:
            return {"tests": 0, "failures": 0, "errors": 1}

    def _run_cocotb_simulations(
        self, *, output_dir: Path, analysis: dict, test_files: list[Path]
    ) -> dict:
        from cocotb_tools.runner import get_runner

        rtl_files = [
            Path(p)
            for p in analysis.get("rtl_files", [])
            if Path(p).suffix.lower() in {".sv", ".v", ".svh", ".vh"}
        ]
        rtl_files = self._order_rtl_sources(self._augment_rtl_sources(rtl_files))
        if not rtl_files:
            return {
                "runs": [],
                "simulation_passed": False,
                "coverage_dat_files": [],
                "selected_top": "",
                "simulators_requested": self._resolve_requested_simulators(
                    self.simulator_mode
                ),
                "dual_simulator_compliant": False,
            }

        include_dirs = sorted({str(p.parent) for p in rtl_files})

        requested_sims = self._resolve_requested_simulators(self.simulator_mode)
        available = {
            "icarus": bool(shutil.which("iverilog")),
            "verilator": bool(shutil.which("verilator")),
        }

        simulators: list[str] = []
        runs: list[dict] = []
        for sim in requested_sims:
            if available.get(sim, False):
                simulators.append(sim)
            else:
                runs.append(
                    {
                        "simulator": sim,
                        "module": "__tool__",
                        "passed": False,
                        "tests": 0,
                        "failures": 1,
                        "errors": 1,
                        "results_xml": "",
                        "error": f"missing_simulator_tool: {sim}",
                    }
                )

        top_candidates = []
        for cand in [
            analysis.get("selected_top", ""),
            *analysis.get("top_modules", []),
            *analysis.get("modules", []),
        ]:
            cand_str = str(cand).strip()
            if cand_str and cand_str not in top_candidates:
                top_candidates.append(cand_str)

        coverage_dat_files: list[str] = []
        selected_top = top_candidates[0] if top_candidates else ""

        for sim in simulators:
            runner = get_runner(sim)
            build_dir = output_dir / "sim_build" / sim
            ensure_dir(build_dir)

            build_ok = False
            build_error = ""
            for top in top_candidates:
                try:
                    build_args: list[str] = []
                    if sim == "verilator":
                        build_args = ["--coverage", "-Wno-fatal"]

                    runner.build(
                        verilog_sources=[str(p) for p in rtl_files],
                        includes=include_dirs,
                        hdl_toplevel=top,
                        build_dir=str(build_dir),
                        always=True,
                        clean=True,
                        build_args=build_args,
                        waves=False,
                    )
                    selected_top = top
                    build_ok = True
                    break
                except Exception as exc:
                    build_error = str(exc)

            if not build_ok:
                runs.append(
                    {
                        "simulator": sim,
                        "module": "__build__",
                        "passed": False,
                        "tests": 0,
                        "failures": 1,
                        "errors": 1,
                        "results_xml": "",
                        "error": f"build_failed: {build_error}",
                    }
                )
                continue

            for test_file in test_files:
                module = test_file.stem
                test_dir = output_dir / "sim_results" / sim / module
                ensure_dir(test_dir)
                results_xml = test_dir / "results.xml"
                func_cov_file = (
                    output_dir
                    / "coverage"
                    / "func_coverage"
                    / "raw"
                    / f"{sim}_{module}.json"
                )
                ensure_dir(func_cov_file.parent)

                extra_env = {
                    "AUTOVERIFIER_FUNC_COV_FILE": str(func_cov_file),
                    "PYTHONPATH": self._build_pythonpath(
                        test_file=test_file, output_dir=output_dir
                    ),
                }

                # cocotb runner derives PYTHONPATH from current process sys.path,
                # so inject per-test paths here before invoking runner.test().
                injected_paths = [
                    str(test_file.parent.resolve()),
                    str((output_dir / "testbench").resolve()),
                ]
                inserted: list[str] = []
                for entry in reversed(injected_paths):
                    if entry and entry not in sys.path:
                        sys.path.insert(0, entry)
                        inserted.append(entry)

                error_text = ""
                actual_results_xml = results_xml
                try:
                    returned_results = runner.test(
                        test_module=module,
                        hdl_toplevel=selected_top,
                        build_dir=str(build_dir),
                        test_dir=str(test_dir),
                        results_xml=str(results_xml),
                        extra_env=extra_env,
                        waves=False,
                    )
                    if returned_results:
                        actual_results_xml = Path(returned_results)
                except Exception as exc:
                    error_text = str(exc)
                finally:
                    for entry in inserted:
                        try:
                            sys.path.remove(entry)
                        except ValueError:
                            pass

                parsed = self._parse_results_xml(results_xml=actual_results_xml)
                passed = bool(
                    parsed.get("tests", 0) > 0
                    and parsed.get("failures", 0) == 0
                    and parsed.get("errors", 0) == 0
                    and not error_text
                )
                runs.append(
                    {
                        "simulator": sim,
                        "module": module,
                        "passed": passed,
                        "tests": int(parsed.get("tests", 0)),
                        "failures": int(parsed.get("failures", 0)),
                        "errors": int(parsed.get("errors", 0)),
                        "results_xml": str(actual_results_xml),
                        "error": error_text,
                    }
                )

            for cov_file in [
                *build_dir.rglob("coverage.dat"),
                *(output_dir / "sim_results" / sim).rglob("coverage.dat"),
            ]:
                cov_str = str(cov_file)
                if cov_str not in coverage_dat_files:
                    coverage_dat_files.append(cov_str)

        passed_runs = [
            r
            for r in runs
            if bool(r.get("passed", False)) and r.get("module") != "__build__"
        ]
        nonbuild_runs = [
            r
            for r in runs
            if r.get("module") not in {"__build__", "__tool__"}
        ]

        passing_simulators = {
            str(r.get("simulator", ""))
            for r in nonbuild_runs
            if bool(r.get("passed", False)) and str(r.get("simulator", "")).strip()
        }
        dual_simulator_compliant = {"icarus", "verilator"}.issubset(
            passing_simulators
        )

        return {
            "runs": runs,
            "simulation_passed": bool(nonbuild_runs)
            and len(passed_runs) == len(nonbuild_runs),
            "coverage_dat_files": coverage_dat_files,
            "selected_top": selected_top,
            "simulators_requested": requested_sims,
            "dual_simulator_compliant": dual_simulator_compliant,
        }

    def _extract_verilator_coverage(
        self, *, output_dir: Path, coverage_dat_files: list[str]
    ) -> dict:
        if not shutil.which("verilator_coverage"):
            return {}

        code_cov_dir = output_dir / "coverage" / "code_coverage"
        ensure_dir(code_cov_dir)

        dat_paths = [Path(p) for p in coverage_dat_files if Path(p).exists()]
        if not dat_paths:
            dat_paths = list(output_dir.rglob("coverage.dat"))
        if not dat_paths:
            return {}

        merged_dat = code_cov_dir / "merged_coverage.dat"
        info_file = code_cov_dir / "coverage.info"
        annotate_dir = code_cov_dir / "coverage_annotated"

        try:
            subprocess.run(
                [
                    "verilator_coverage",
                    "-write",
                    str(merged_dat),
                    *[str(p) for p in dat_paths],
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["verilator_coverage", "--write-info", str(info_file), str(merged_dat)],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    "verilator_coverage",
                    "--annotate",
                    str(annotate_dir),
                    str(merged_dat),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except Exception:
            return {}

        lf = lh = brf = brh = 0
        try:
            for line in info_file.read_text(
                encoding="utf-8", errors="ignore"
            ).splitlines():
                if line.startswith("LF:"):
                    lf += int(line.split(":", 1)[1].strip())
                elif line.startswith("LH:"):
                    lh += int(line.split(":", 1)[1].strip())
                elif line.startswith("BRF:"):
                    brf += int(line.split(":", 1)[1].strip())
                elif line.startswith("BRH:"):
                    brh += int(line.split(":", 1)[1].strip())
        except Exception:
            return {}

        line_percent = (100.0 * lh / lf) if lf > 0 else 0.0
        branch_percent = (100.0 * brh / brf) if brf > 0 else 0.0

        toggle_metric = self._parse_metric_from_annotated(
            annotate_dir=annotate_dir,
            metric_keywords=("toggle", "tog"),
            metric_name="toggle",
        )
        fsm_metric = self._parse_metric_from_annotated(
            annotate_dir=annotate_dir,
            metric_keywords=("fsm", "state"),
            metric_name="fsm",
        )

        toggle_percent = float(
            (toggle_metric or {}).get("percent", 0.0)
        )
        fsm_percent = float((fsm_metric or {}).get("percent", 0.0))
        toggle_source = str((toggle_metric or {}).get("source", "unavailable"))
        fsm_source = str((fsm_metric or {}).get("source", "unavailable"))

        return {
            "line_percent": round(line_percent, 2),
            "branch_percent": round(branch_percent, 2),
            "toggle_percent": round(toggle_percent, 2),
            "fsm_percent": round(fsm_percent, 2),
            "toggle_source": toggle_source,
            "fsm_source": fsm_source,
            "source": "verilator_lcov",
        }

    def _parse_metric_from_annotated(
        self,
        *,
        annotate_dir: Path,
        metric_keywords: tuple[str, ...],
        metric_name: str,
    ) -> dict | None:
        if not annotate_dir.exists() or not annotate_dir.is_dir():
            return None

        ratio_hit = 0
        ratio_total = 0
        percent_values: list[float] = []

        ratio_patterns = [
            re.compile(rf"(?i){kw}[^0-9\n]{{0,80}}(\d+)\s*/\s*(\d+)")
            for kw in metric_keywords
        ]
        percent_patterns = [
            re.compile(rf"(?i){kw}[^0-9\n]{{0,80}}(\d+(?:\.\d+)?)\s*%")
            for kw in metric_keywords
        ]

        for annotated in annotate_dir.rglob("*"):
            if not annotated.is_file():
                continue
            for line in annotated.read_text(
                encoding="utf-8", errors="ignore"
            ).splitlines():
                lowered = line.lower()
                if not any(kw in lowered for kw in metric_keywords):
                    continue

                for pat in ratio_patterns:
                    m = pat.search(line)
                    if m:
                        ratio_hit += int(m.group(1))
                        ratio_total += int(m.group(2))

                for pat in percent_patterns:
                    m = pat.search(line)
                    if m:
                        try:
                            percent_values.append(float(m.group(1)))
                        except Exception:
                            pass

        if ratio_total > 0:
            return {
                "percent": round(100.0 * ratio_hit / ratio_total, 2),
                "source": f"annotated_native_{metric_name}_ratio",
            }

        if percent_values:
            return {
                "percent": round(sum(percent_values) / len(percent_values), 2),
                "source": f"annotated_native_{metric_name}_percent",
            }

        return None

    def _extract_functional_coverage(self, *, output_dir: Path) -> dict:
        raw_dir = output_dir / "coverage" / "func_coverage" / "raw"
        ensure_dir(raw_dir)

        aggregate: dict[str, int] = {}
        for cov_file in sorted(raw_dir.glob("*.json")):
            try:
                payload = json.loads(cov_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            for _test_name, counters in payload.items():
                if not isinstance(counters, dict):
                    continue
                for bin_name, value in counters.items():
                    try:
                        int_value = int(value)
                    except Exception:
                        int_value = 0
                    aggregate[bin_name] = aggregate.get(bin_name, 0) + int_value

        if not aggregate:
            return {
                "percent": 0.0,
                "bins_hit": 0,
                "bins_total": 0,
                "source": "no_functional_data",
            }

        bins_total = len(aggregate)
        bins_hit = len([k for k, v in aggregate.items() if v > 0])
        percent = (100.0 * bins_hit / bins_total) if bins_total > 0 else 0.0

        write_json(
            output_dir / "coverage" / "func_coverage" / "bin_counts.json",
            {"bins": aggregate},
        )
        return {
            "percent": round(percent, 2),
            "bins_hit": bins_hit,
            "bins_total": bins_total,
            "source": "functional_bins_from_test_snapshots",
        }

    def _collect_failure_feedback(
        self,
        *,
        iteration: int,
        repair_attempt: int,
        test_result: dict,
        coverage_result: dict,
        scenario_name: str,
        plan: dict,
    ) -> dict:
        failed_runs = []
        for run in test_result.get("simulation_runs", []):
            if bool(run.get("passed", False)):
                continue
            failed_runs.append(
                {
                    "simulator": str(run.get("simulator", "")),
                    "module": str(run.get("module", "")),
                    "failures": int(run.get("failures", 0) or 0),
                    "errors": int(run.get("errors", 0) or 0),
                    "error": str(run.get("error", ""))[:1200],
                }
            )

        return {
            "iteration": iteration,
            "repair_attempt": repair_attempt,
            "scenario_name": scenario_name,
            "simulators_requested": test_result.get("simulators_requested", []),
            "simulators_tested": test_result.get("simulators_tested", []),
            "dual_simulator_compliant": bool(
                test_result.get("dual_simulator_compliant", False)
            ),
            "simulation_passed": bool(test_result.get("simulation_passed", False)),
            "failed_runs": failed_runs,
            "coverage": {
                "line_percent": float(
                    coverage_result.get("code_coverage", {}).get("line_percent", 0.0)
                ),
                "branch_percent": float(
                    coverage_result.get("code_coverage", {}).get("branch_percent", 0.0)
                ),
                "toggle_percent": float(
                    coverage_result.get("code_coverage", {}).get("toggle_percent", 0.0)
                ),
                "fsm_percent": float(
                    coverage_result.get("code_coverage", {}).get("fsm_percent", 0.0)
                ),
                "functional_percent": float(
                    coverage_result.get("functional_coverage", {}).get("percent", 0.0)
                ),
                "functional_bins_hit": int(
                    coverage_result.get("functional_coverage", {}).get("bins_hit", 0)
                ),
                "functional_bins_total": int(
                    coverage_result.get("functional_coverage", {}).get("bins_total", 0)
                ),
            },
            "risk_areas": plan.get("risk_areas", [])[:5],
        }

    def _parse_results_xml_failures(
        self, *, results_xml: Path, max_items: int = 10
    ) -> list[dict]:
        details: list[dict] = []
        if not results_xml.exists():
            return details
        try:
            root = ET.parse(results_xml).getroot()
            testcases = root.findall(".//testcase")
            for case in testcases:
                failure_node = case.find("failure")
                error_node = case.find("error")
                if failure_node is None and error_node is None:
                    continue
                issue = failure_node if failure_node is not None else error_node
                text = ""
                if issue is not None:
                    text = (
                        (issue.text or "").strip()
                        or str(issue.attrib.get("message", "")).strip()
                    )
                detail = {
                    "testcase": str(case.attrib.get("name", "")),
                    "classname": str(case.attrib.get("classname", "")),
                    "kind": "failure" if failure_node is not None else "error",
                    "message": text[:1200],
                }
                details.append(detail)
                if len(details) >= max_items:
                    break
        except Exception:
            return details
        return details

    def _find_test_file_for_module(self, *, output_dir: Path, module: str) -> Path | None:
        candidates = list((output_dir / "tests").rglob(f"{module}.py"))
        if candidates:
            return candidates[0]
        for p in (output_dir / "tests").rglob("test_*.py"):
            if p.stem == module:
                return p
        return None

    def _collect_failing_test_context(
        self,
        *,
        output_dir: Path,
        test_result: dict,
        analysis: dict,
        max_code_chars: int = 20000,
    ) -> dict:
        failing_runs = [
            r
            for r in test_result.get("simulation_runs", [])
            if (not bool(r.get("passed", False)))
            and str(r.get("module", "")) not in {"__build__", "__tool__"}
        ]

        failing_modules: dict[str, dict] = {}
        for run in failing_runs:
            module = str(run.get("module", "")).strip()
            if not module:
                continue
            entry = failing_modules.setdefault(
                module,
                {
                    "module": module,
                    "simulators": [],
                    "failures": 0,
                    "errors": 0,
                    "runner_error": "",
                    "xml_failures": [],
                    "path": "",
                    "code": "",
                },
            )

            sim = str(run.get("simulator", "")).strip()
            if sim and sim not in entry["simulators"]:
                entry["simulators"].append(sim)
            entry["failures"] = int(entry["failures"]) + int(run.get("failures", 0) or 0)
            entry["errors"] = int(entry["errors"]) + int(run.get("errors", 0) or 0)
            if not entry["runner_error"]:
                entry["runner_error"] = str(run.get("error", ""))[:1200]

            xml_path = Path(str(run.get("results_xml", ""))) if run.get("results_xml") else None
            if xml_path is not None:
                parsed = self._parse_results_xml_failures(results_xml=xml_path)
                if parsed:
                    entry["xml_failures"].extend(parsed)

        for module, entry in failing_modules.items():
            path = self._find_test_file_for_module(output_dir=output_dir, module=module)
            if path is None:
                continue
            entry["path"] = str(path)
            code = read_text(path, max_chars=max_code_chars)
            entry["code"] = code

        rtl_context: list[dict] = []
        for rtl in [Path(p) for p in analysis.get("rtl_files", [])][:2]:
            rtl_context.append(
                {
                    "path": str(rtl),
                    "excerpt": read_text(rtl, max_chars=18000),
                }
            )

        return {
            "failing_modules": [v for v in failing_modules.values() if v.get("path")],
            "analysis": {
                "selected_top": str(analysis.get("selected_top", "")),
                "protocol_hints": analysis.get("protocol_hints", []),
                "clock_candidates": analysis.get("clock_candidates", []),
                "reset_candidates": analysis.get("reset_candidates", []),
            },
            "rtl_context": rtl_context,
        }

    def _sanitize_rewritten_test_module(self, *, code: str) -> str:
        sanitized = code
        sanitized = sanitized.replace(
            "from testbench.agents.tlul_driver import TlUlDriver",
            "from agents.tl_ul_agent import TlUlDriver",
        )
        sanitized = sanitized.replace(
            "from testbench.agents.tlul import TlUlDriver",
            "from agents.tl_ul_agent import TlUlDriver",
        )
        sanitized = sanitized.replace(
            "from testbench.agents import TlUlDriver",
            "from agents.tl_ul_agent import TlUlDriver",
        )
        sanitized = re.sub(
            r"from\s+testbench\.agents\.[A-Za-z0-9_]+\s+import\s+TlUlDriver",
            "from agents.tl_ul_agent import TlUlDriver",
            sanitized,
        )
        sanitized = re.sub(
            r"from\s+testbench\.coverage\.coverage\s+import\s+CoverageCollector",
            "from coverage.coverage import CoverageCollector",
            sanitized,
        )
        sanitized = sanitized.replace(
            'await Timer(1, unit="ns")',
            "await RisingEdge(clk)",
        )
        sanitized = sanitized.replace(
            "await Timer(1, unit='ns')",
            "await RisingEdge(clk)",
        )
        sanitized = sanitized.replace(
            'await Timer(1, "ns")',
            "await RisingEdge(clk)",
        )
        sanitized = sanitized.replace(
            "await Timer(1, 'ns')",
            "await RisingEdge(clk)",
        )

        if 'TB_ROOT = THIS_DIR.parent.parent / "testbench"' not in sanitized:
            lines = sanitized.splitlines()
            insert_at = 0
            while insert_at < len(lines) and lines[insert_at].startswith("from __future__"):
                insert_at += 1

            preamble = [
                "",
                "import sys",
                "from pathlib import Path",
                "",
                "THIS_DIR = Path(__file__).resolve().parent",
                'TB_ROOT = THIS_DIR.parent.parent / "testbench"',
                "if str(TB_ROOT) not in sys.path:",
                "    sys.path.insert(0, str(TB_ROOT))",
                "",
            ]
            lines = lines[:insert_at] + preamble + lines[insert_at:]
            sanitized = "\n".join(lines)

        return sanitized

    def _rewrite_failing_tests_with_llm(
        self,
        *,
        output_dir: Path,
        plan: dict,
        analysis: dict,
        test_result: dict,
        iteration: int,
        min_iterations: int,
        max_iterations: int,
    ) -> list[dict]:
        if not self._llm_allowed():
            return []

        context = self._collect_failing_test_context(
            output_dir=output_dir,
            test_result=test_result,
            analysis=analysis,
        )
        failing_modules = context.get("failing_modules", [])
        if not isinstance(failing_modules, list) or not failing_modules:
            return []

        prompt = textwrap.dedent(
            f"""\
            You are fixing failing cocotb tests by rewriting entire failing test modules.

            Requirements:
            - Return STRICT JSON only with this schema:
              {{
                "replacements": [
                  {{
                    "path": "tests/.../test_file.py",
                    "code": "<full python module code>"
                  }}
                ]
              }}
            - Only include paths that are present in the failing module list below.
            - Preserve other tests in each module unless they are clearly incorrect.
            - Keep deterministic seeds.
            - Keep compatibility with both Icarus and Verilator.
            - Prefer semantic requirement checks over generic loops.
            - Avoid using Timer(1, unit="ns") to prevent simulator precision issues.

            Iteration control context:
            - current_iteration: {iteration}
            - min_iterations: {min_iterations}
            - max_iterations: {max_iterations}

            Plan summary:
            {json.dumps({
                'coverage_goals': plan.get('coverage_goals', {}),
                'risk_areas': plan.get('risk_areas', [])[:8],
                'directed_tests': plan.get('directed_tests', [])[:20],
                'random_tests': plan.get('random_tests', [])[:20],
            }, indent=2)}

            Failure context:
            {json.dumps(context, indent=2)}
            """
        )

        result = self.llm.generate(
            stage="ITERATE_REWRITE_FAILING",
            system_prompt=(
                "You are a senior verification engineer. Return strict JSON only, no markdown."
            ),
            user_prompt=prompt,
            escalated=True,
        )

        payload = self._extract_json_dict(result.text)
        if not payload:
            return []

        replacements = payload.get("replacements", []) if isinstance(payload, dict) else []
        if not isinstance(replacements, list):
            return []

        allowed_paths = {
            str((output_dir / str(item.get("path", "")).strip()).resolve()): True
            for item in failing_modules
            if isinstance(item, dict) and str(item.get("path", "")).strip()
        }

        applied: list[dict] = []
        for item in replacements:
            if not isinstance(item, dict):
                continue
            rel_path = str(item.get("path", "")).strip()
            code = str(item.get("code", ""))
            if not rel_path or not code:
                continue

            target = (output_dir / rel_path).resolve()
            if str(target) not in allowed_paths:
                continue
            if not target.exists() or target.suffix != ".py":
                continue

            sanitized = self._sanitize_rewritten_test_module(code=code)
            try:
                compile(sanitized, str(target), "exec")
            except Exception:
                continue

            write_text(target, sanitized)
            applied.append({"path": str(target)})

        return applied

    def _extract_python_code_block(self, text: str) -> str:
        fenced = re.findall(r"```(?:python)?\n([\s\S]*?)```", text)
        if fenced:
            return fenced[0].strip() + "\n"
        return text.strip() + "\n"

    def _sanitize_generated_repair_test(
        self, *, repair_code: str, iteration: int, repair_attempt: int
    ) -> str:
        sanitized = repair_code

        sanitized = sanitized.replace(
            "from testbench.agents.tlul_driver import TlUlDriver",
            "from agents.tl_ul_agent import TlUlDriver",
        )
        sanitized = sanitized.replace(
            "from testbench.agents.tlul import TlUlDriver",
            "from agents.tl_ul_agent import TlUlDriver",
        )
        sanitized = re.sub(
            r"from\s+testbench\.agents\.[A-Za-z0-9_]+\s+import\s+TlUlDriver",
            "from agents.tl_ul_agent import TlUlDriver",
            sanitized,
        )
        sanitized = re.sub(
            r"from\s+testbench\.coverage\.coverage\s+import\s+CoverageCollector",
            "from coverage.coverage import CoverageCollector",
            sanitized,
        )

        # Normalize driver API names to the generated TL-UL driver contract.
        sanitized = re.sub(
            r"await\s+([A-Za-z_][A-Za-z0-9_]*)\.write\(",
            r"await \1.csr_write(",
            sanitized,
        )
        sanitized = re.sub(
            r"await\s+([A-Za-z_][A-Za-z0-9_]*)\.read\(",
            r"await \1.csr_read(",
            sanitized,
        )

        expected_name = f"test_repair_iteration_{iteration}_{repair_attempt}"
        sanitized = re.sub(
            r"@cocotb\.test\(\)\nasync\s+def\s+[A-Za-z_][A-Za-z0-9_]*\(",
            f"@cocotb.test()\\nasync def {expected_name}(",
            sanitized,
            count=1,
        )

        return sanitized

    def _sanitize_generated_plateau_test(
        self, *, plateau_code: str, iteration: int
    ) -> str:
        sanitized = plateau_code

        sanitized = sanitized.replace(
            "from testbench.agents.tlul_driver import TlUlDriver",
            "from agents.tl_ul_agent import TlUlDriver",
        )
        sanitized = sanitized.replace(
            "from testbench.agents.tlul import TlUlDriver",
            "from agents.tl_ul_agent import TlUlDriver",
        )
        sanitized = re.sub(
            r"from\s+testbench\.agents\.[A-Za-z0-9_]+\s+import\s+TlUlDriver",
            "from agents.tl_ul_agent import TlUlDriver",
            sanitized,
        )
        sanitized = re.sub(
            r"from\s+testbench\.coverage\.coverage\s+import\s+CoverageCollector",
            "from coverage.coverage import CoverageCollector",
            sanitized,
        )

        sanitized = re.sub(
            r"await\s+([A-Za-z_][A-Za-z0-9_]*)\.write\(",
            r"await \1.csr_write(",
            sanitized,
        )
        sanitized = re.sub(
            r"await\s+([A-Za-z_][A-Za-z0-9_]*)\.read\(",
            r"await \1.csr_read(",
            sanitized,
        )

        expected_name = f"test_plateau_escalation_{iteration}"
        sanitized = re.sub(
            r"@cocotb\.test\(\)\nasync\s+def\s+[A-Za-z_][A-Za-z0-9_]*\(",
            f"@cocotb.test()\\nasync def {expected_name}(",
            sanitized,
            count=1,
        )

        return sanitized

    def _repair_test_compatible(self, repair_code: str) -> bool:
        required_snippets = [
            "@cocotb.test()",
            "THIS_DIR = Path(__file__).resolve().parent",
            'TB_ROOT = THIS_DIR.parent.parent / "testbench"',
            "from agents.tl_ul_agent import TlUlDriver",
            "def _record_func_cov",
            "cocotb.start_soon(Clock(",
            "driver = TlUlDriver(",
        ]
        if not all(snippet in repair_code for snippet in required_snippets):
            return False

        if "from testbench." in repair_code or "import testbench" in repair_code:
            return False
        if re.search(r"await\s+[A-Za-z_][A-Za-z0-9_]*\.write\(", repair_code):
            return False
        if re.search(r"await\s+[A-Za-z_][A-Za-z0-9_]*\.read\(", repair_code):
            return False
        if re.search(r"TlUlDriver\(\s*dut\s*,\s*['\"][^'\"]+['\"]\s*\)", repair_code):
            return False
        if "csr_write(" not in repair_code and "csr_read(" not in repair_code:
            return False
        return True

    def _generate_repair_test_from_feedback(
        self,
        *,
        feedback: dict,
        analysis: dict,
        iteration: int,
        repair_attempt: int,
    ) -> str:
        if not self._llm_allowed():
            raise RuntimeError("LLM calls disabled by timeout lock")

        prompt = textwrap.dedent(
            f"""\
            You are fixing a cocotb verification test after failures.

            Constraints:
            - Return Python source code only for one file.
            - Must include exactly one @cocotb.test() function named:
              test_repair_iteration_{iteration}_{repair_attempt}
                        - Must import TlUlDriver exactly as: from agents.tl_ul_agent import TlUlDriver.
                        - Must use TlUlDriver APIs csr_write/csr_read (not write/read).
            - Must record functional coverage using AUTOVERIFIER_FUNC_COV_FILE JSON format.
            - Keep deterministic random seed.
            - Keep generic TL-UL behavior (no DUT-specific hardcoding).

            Context:
            {json.dumps(feedback, indent=2)}

            Analysis hints:
            {json.dumps({
                'selected_top': analysis.get('selected_top', ''),
                'protocol_hints': analysis.get('protocol_hints', []),
                'clock_candidates': analysis.get('clock_candidates', []),
                'reset_candidates': analysis.get('reset_candidates', []),
            }, indent=2)}
            """
        )

        result, _score, _escalated = self.llm.generate_with_quality_gate(
            stage="ITERATE_REPAIR",
            system_prompt=(
                "You are a senior DV engineer. Return valid Python code only; "
                "no markdown explanation."
            ),
            user_prompt=prompt,
            min_score=max(70, self.llm.judge_min_score - 10),
        )
        candidate = self._extract_python_code_block(result.text)
        return candidate

    def _generate_plateau_escalation_test(
        self,
        *,
        iteration: int,
        plan: dict,
        analysis: dict,
        current_func: float,
        target_func: float,
    ) -> str:
        if not self._llm_allowed():
            raise RuntimeError("LLM calls disabled by timeout lock")

        prompt = textwrap.dedent(
            f"""\
            Coverage has plateaued. Generate one stronger cocotb test focused on risk areas.

            Constraints:
            - Return Python source code only for one file.
            - Must include exactly one @cocotb.test() function named:
              test_plateau_escalation_{iteration}
            - Must import TlUlDriver exactly as: from agents.tl_ul_agent import TlUlDriver.
            - Must use TlUlDriver APIs csr_write/csr_read only.
            - Must record functional coverage using AUTOVERIFIER_FUNC_COV_FILE JSON format.
            - Keep deterministic seed.
            - Prefer requirement-specific assertions over generic traffic loops.
            - Keep compatibility for both Icarus and Verilator.

            Coverage snapshot:
            {json.dumps({
                'iteration': iteration,
                'current_functional_percent': round(current_func, 2),
                'target_functional_percent': round(target_func, 2),
                'gap': round(target_func - current_func, 2),
            }, indent=2)}

            Plan risk areas:
            {json.dumps(plan.get('risk_areas', [])[:8], indent=2)}

            Analysis hints:
            {json.dumps({
                'selected_top': analysis.get('selected_top', ''),
                'protocol_hints': analysis.get('protocol_hints', []),
                'clock_candidates': analysis.get('clock_candidates', []),
                'reset_candidates': analysis.get('reset_candidates', []),
            }, indent=2)}
            """
        )

        result = self.llm.generate(
            stage="ITERATE_PLATEAU",
            system_prompt=(
                "You are a senior DV engineer. Produce robust, deterministic cocotb test code only "
                "with semantic assertions and no markdown."
            ),
            user_prompt=prompt,
            escalated=True,
        )
        return self._extract_python_code_block(result.text)

    def _render_repair_feedback_test_file(
        self,
        *,
        iteration: int,
        repair_attempt: int,
        clock_name: str,
        reset_name: str,
    ) -> str:
        return textwrap.dedent(
            f'''\
            from __future__ import annotations

            import json
            import os
            import random
            import sys
            from pathlib import Path

            import cocotb
            from cocotb.clock import Clock
            from cocotb.triggers import RisingEdge

            THIS_DIR = Path(__file__).resolve().parent
            TB_ROOT = THIS_DIR.parent.parent / "testbench"
            if str(TB_ROOT) not in sys.path:
                sys.path.insert(0, str(TB_ROOT))

            from agents.tl_ul_agent import TlUlDriver
            from coverage.coverage import CoverageCollector


            def _record_func_cov(tag: str, counters: dict) -> None:
                out_file = os.getenv("AUTOVERIFIER_FUNC_COV_FILE", "").strip()
                if not out_file:
                    return
                cov_path = Path(out_file)
                cov_path.parent.mkdir(parents=True, exist_ok=True)
                payload = {{}}
                if cov_path.exists():
                    try:
                        payload = json.loads(cov_path.read_text(encoding="utf-8"))
                    except Exception:
                        payload = {{}}
                payload[tag] = counters
                cov_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


            @cocotb.test()
            async def test_repair_iteration_{iteration}_{repair_attempt}(dut):
                clk = getattr(dut, "{clock_name}") if hasattr(dut, "{clock_name}") else getattr(dut, "clk_i")
                cocotb.start_soon(Clock(clk, 2, unit="step").start())

                driver = TlUlDriver(dut, clk_signal=clk._name, rst_signal="{reset_name}")
                coverage = CoverageCollector()
                await driver.apply_reset(cycles=6)
                coverage.hit("reset_sequence")

                random.seed(1000 + {iteration} * 10 + {repair_attempt})
                addr_pool = [0x0, 0x4, 0x8, 0xC, 0x10, 0x3FC, 0x7FC, 0xFFC]

                for _ in range(40):
                    addr = random.choice(addr_pool)
                    if random.random() < 0.6:
                        data = random.getrandbits(32)
                        wr = await driver.csr_write(addr=addr, data=data)
                        coverage.hit_operation(op="write", addr=addr, data=data, error=bool(int(wr.get("error", 0))))
                    else:
                        rd = await driver.csr_read(addr=addr)
                        coverage.hit_operation(op="read", addr=addr, error=bool(int(rd.get("error", 0))))

                await RisingEdge(clk)
                _record_func_cov("test_repair_iteration_{iteration}_{repair_attempt}", coverage.snapshot())
            '''
        )

    def _render_plateau_escalation_test_file(
        self,
        *,
        iteration: int,
        clock_name: str,
        reset_name: str,
        scenario_name: str,
    ) -> str:
        safe_label = self._slugify_identifier(scenario_name)
        return textwrap.dedent(
            f'''\
            from __future__ import annotations

            import json
            import os
            import random
            import sys
            from pathlib import Path

            import cocotb
            from cocotb.clock import Clock
            from cocotb.triggers import RisingEdge

            THIS_DIR = Path(__file__).resolve().parent
            TB_ROOT = THIS_DIR.parent.parent / "testbench"
            if str(TB_ROOT) not in sys.path:
                sys.path.insert(0, str(TB_ROOT))

            from agents.tl_ul_agent import TlUlDriver
            from coverage.coverage import CoverageCollector


            def _record_func_cov(tag: str, counters: dict) -> None:
                out_file = os.getenv("AUTOVERIFIER_FUNC_COV_FILE", "").strip()
                if not out_file:
                    return
                cov_path = Path(out_file)
                cov_path.parent.mkdir(parents=True, exist_ok=True)
                payload = {{}}
                if cov_path.exists():
                    try:
                        payload = json.loads(cov_path.read_text(encoding="utf-8"))
                    except Exception:
                        payload = {{}}
                payload[tag] = counters
                cov_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


            @cocotb.test()
            async def test_plateau_escalation_{iteration}(dut):
                clk = getattr(dut, "{clock_name}") if hasattr(dut, "{clock_name}") else getattr(dut, "clk_i")
                cocotb.start_soon(Clock(clk, 2, unit="step").start())

                driver = TlUlDriver(dut, clk_signal=clk._name, rst_signal="{reset_name}")
                coverage = CoverageCollector()
                await driver.apply_reset(cycles=7)
                coverage.hit("reset_sequence")

                rng = random.Random(0x5A11 + {iteration})
                mapped_addrs = [0x0, 0x4, 0x8, 0xC, 0x10, 0x14, 0x18, 0x1C]
                unmapped_addrs = [0x3FC, 0x7FC, 0xFFC]
                successful_ops = 0
                observed_errors = 0

                for step in range(72):
                    if step % 16 == 0:
                        await driver.apply_reset(cycles=2 + (step % 3))
                        coverage.hit("reset_sequence")

                    use_unmapped = (step % 11 == 0)
                    addr = rng.choice(unmapped_addrs if use_unmapped else mapped_addrs)
                    if rng.random() < 0.58:
                        data = (rng.getrandbits(32) ^ (step * 0x01010101)) & 0xFFFFFFFF
                        wr = await driver.csr_write(addr=addr, data=data)
                        err = int(wr.get("error", 0))
                        coverage.hit_operation(op="write", addr=addr, data=data, error=bool(err))
                        observed_errors += err
                        if not use_unmapped and err == 0:
                            successful_ops += 1
                    else:
                        rd = await driver.csr_read(addr=addr)
                        err = int(rd.get("error", 0))
                        coverage.hit_operation(op="read", addr=addr, error=bool(err))
                        observed_errors += err
                        if not use_unmapped and err == 0:
                            successful_ops += 1

                    await RisingEdge(clk)

                assert successful_ops >= 20, "Plateau escalation test did not achieve enough successful mapped operations"
                assert observed_errors >= 1, "Plateau escalation test expected at least one unmapped-access error observation"
                _record_func_cov("test_plateau_escalation_{iteration}_{safe_label}", coverage.snapshot())
            '''
        )

    def _render_gap_test_file(self, *, iteration: int, scenario_name: str) -> str:
        return textwrap.dedent(
            f'''\
            from __future__ import annotations

            import json
            import os
            import random
            import sys
            from pathlib import Path

            import cocotb
            from cocotb.clock import Clock
            from cocotb.triggers import RisingEdge

            THIS_DIR = Path(__file__).resolve().parent
            TB_ROOT = THIS_DIR.parent.parent / "testbench"
            if str(TB_ROOT) not in sys.path:
                sys.path.insert(0, str(TB_ROOT))

            from agents.tl_ul_agent import TlUlDriver
            from coverage.coverage import CoverageCollector


            def _record_func_cov(tag: str, counters: dict) -> None:
                out_file = os.getenv("AUTOVERIFIER_FUNC_COV_FILE", "").strip()
                if not out_file:
                    return
                cov_path = Path(out_file)
                cov_path.parent.mkdir(parents=True, exist_ok=True)
                payload = {{}}
                if cov_path.exists():
                    try:
                        payload = json.loads(cov_path.read_text(encoding="utf-8"))
                    except Exception:
                        payload = {{}}
                payload[tag] = counters
                cov_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


            @cocotb.test()
            async def test_gap_iteration_{iteration}(dut):
                """Coverage-gap iteration test: {scenario_name}."""
                clk = getattr(dut, "clk_i") if hasattr(dut, "clk_i") else getattr(dut, "clk")
                cocotb.start_soon(Clock(clk, 2, unit="step").start())

                rst_name = "rst_ni" if hasattr(dut, "rst_ni") else ("rst_n" if hasattr(dut, "rst_n") else "rst")
                driver = TlUlDriver(dut, clk_signal=clk._name, rst_signal=rst_name)
                coverage = CoverageCollector()
                await driver.apply_reset(cycles=4)
                coverage.hit("reset_sequence")

                random.seed(100 + {iteration})
                for _ in range(16 + {iteration} * 4):
                    addr = random.choice([0x0, 0x4, 0x8, 0xC, 0x10])
                    data = random.getrandbits(32)
                    if random.random() < 0.55:
                        wr = await driver.csr_write(addr=addr, data=data)
                        coverage.hit_operation(op="write", addr=addr, data=data, error=bool(int(wr.get("error", 0))))
                    else:
                        rd = await driver.csr_read(addr=addr)
                        coverage.hit_operation(op="read", addr=addr, error=bool(int(rd.get("error", 0))))

                await RisingEdge(clk)
                _record_func_cov("test_gap_iteration_{iteration}", coverage.snapshot())
            '''
        )

    def _suggest_gap_scenario(self, *, plan: dict, index: int) -> str:
        risks = plan.get("risk_areas", [])
        if not isinstance(risks, list) or not risks:
            raise RuntimeError(
                "Iteration stage requires at least one risk area in verification_plan.json."
            )

        risk_item = risks[min(index - 1, len(risks) - 1)]
        fallback_label = self._slugify_identifier(
            str(risk_item.get("area", f"gap_iter_{index}"))
        )

        if not self._llm_allowed():
            return f"{fallback_label}_gap"

        prompt = textwrap.dedent(
            f"""\
            Provide a concise coverage-gap scenario label.
            Risk item: {json.dumps(risk_item)}
            Return one short snake_case label only.
            """
        )

        result, _score, _escalated = self.llm.generate_with_quality_gate(
            stage="ITERATE",
            system_prompt="You are a verification planner. Return only one snake_case label.",
            user_prompt=prompt,
            min_score=max(65, self.llm.judge_min_score - 20),
        )

        label = result.text.strip().splitlines()[0].strip().lower()
        label = re.sub(r"[^a-z0-9_]+", "_", label)
        label = label.strip("_")
        if not label:
            return f"{fallback_label}_gap"
        return label

    def _generate_exec_summary(
        self,
        *,
        analysis: dict,
        plan: dict,
        test_result: dict,
        coverage_result: dict,
        iteration_result: dict,
        bug_result: dict,
    ) -> str:
        payload = {
            "modules": analysis.get("modules", []),
            "features": plan.get("features", []),
            "directed": test_result.get("directed_test_count", 0),
            "random": test_result.get("random_test_count", 0),
            "functional": iteration_result.get(
                "final_functional_percent",
                coverage_result.get("functional_coverage", {}).get("percent", 0),
            ),
            "bug_hypotheses": len(bug_result.get("findings", [])),
        }
        prompt = textwrap.dedent(
            f"""\
            Write a concise 4-6 sentence verification executive summary.
            Focus on what was generated, what was validated, and what remains risky.
            Data:\n{json.dumps(payload, indent=2)}
            """
        )

        if not self._llm_allowed():
            return (
                "Execution concluded with timeout lock active; no further LLM calls were made. "
                f"Generated directed={payload['directed']} and random={payload['random']} tests, "
                f"functional coverage reached {payload['functional']}%, and "
                f"static bug hypotheses count is {payload['bug_hypotheses']}. "
                "Remaining risk is concentrated in failing scenarios and uncovered corner cases."
            )

        result, _score, _escalated = self.llm.generate_with_quality_gate(
            stage="REPORT",
            system_prompt="You are a senior DV lead writing a concise technical summary.",
            user_prompt=prompt,
            min_score=max(70, self.llm.judge_min_score - 10),
        )

        summary = result.text.strip()
        if not summary:
            raise RuntimeError("Model returned an empty executive summary.")
        return summary
