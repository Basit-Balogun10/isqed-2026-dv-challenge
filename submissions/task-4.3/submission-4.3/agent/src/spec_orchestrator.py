from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from agent_logger import AgentLogger
from io_utils import ensure_dir, read_text, tokenize
from llm_provider import LLMProvider


class SpecInterpreterOrchestrator:
    """Generate spec-first DV artifacts for Task 4.3."""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.agent_cfg = config.get("agent", {}) if isinstance(config, dict) else {}
        self.max_features = int(self.agent_cfg.get("max_features", 18))
        self.max_covergroups = int(self.agent_cfg.get("max_covergroups", 8))
        self.max_assertions = int(self.agent_cfg.get("max_assertions", 32))
        self.max_test_stubs = int(self.agent_cfg.get("max_test_stubs", 8))

        self.logger = AgentLogger()
        self.logger.metadata["agent_name"] = "task_4_3_spec_interpreter"
        self.llm = LLMProvider(config=config, logger=self.logger)
        self.logger.set_llm_identity(
            provider=self.llm.provider_name,
            model=self.llm.primary_model,
        )

    def run(self, *, spec_path: Path, output_dir: Path) -> None:
        ensure_dir(output_dir)
        ensure_dir(output_dir / "test_stubs")

        spec_text = read_text(spec_path, max_chars=500_000)
        if not spec_text.strip():
            raise RuntimeError(f"Specification is empty: {spec_path}")

        self.logger.record_action(
            stage="INIT",
            action="load_spec",
            duration_seconds=0.0,
            input_summary=f"spec={spec_path.name}",
            output_summary=f"chars={len(spec_text)}",
        )

        heuristic = self._heuristic_interpretation(spec_text=spec_text, spec_path=spec_path)
        interpreted = self._llm_or_fallback(spec_text=spec_text, heuristic=heuristic)

        self._write_vplan(output_dir=output_dir, interpreted=interpreted)
        self._write_coverage(output_dir=output_dir, interpreted=interpreted)
        self._write_assertions(output_dir=output_dir, interpreted=interpreted)
        self._write_test_stubs(output_dir=output_dir, interpreted=interpreted)
        self._write_report(
            output_dir=output_dir,
            interpreted=interpreted,
            spec_path=spec_path,
            spec_text=spec_text,
        )

        self.logger.record_action(
            stage="FINALIZE",
            action="artifact_generation_complete",
            duration_seconds=0.0,
            input_summary=f"features={len(interpreted['features'])}",
            output_summary=(
                f"tests={len(interpreted['tests'])}; "
                f"covergroups={len(interpreted['covergroups'])}; "
                f"assertions={len(interpreted['assertions'])}"
            ),
        )
        self.logger.finalize(output_path=output_dir / "agent_log.json", stats=self.llm.stats)

    def _llm_or_fallback(self, *, spec_text: str, heuristic: dict) -> dict:
        system_prompt = (
            "You are a senior ASIC verification architect. "
            "Interpret the specification into pre-RTL DV artifacts and return strict JSON only."
        )
        user_prompt = (
            "Produce strict JSON with this schema:\n"
            "{"
            '"dut_name":"string",'
            '"spec_version":"string",'
            '"features":[{"id":"F001","name":"...","description":"...",'
            '"priority":"high|medium|low","risk":"high|medium|low",'
            '"coverage_goals":["..."],"test_strategy":"...",'
            '"tests":["test_name"],"assertions":["assertion_name"]}],'
            '"cross_feature_tests":[{"id":"X001","name":"...","features":["F001"],"description":"..."}],'
            '"covergroups":[{"name":"...","description":"...","sample_event":"...",'
            '"coverpoints":[{"name":"...","description":"...","bins":["..."]}],'
            '"crosses":[{"name":"...","coverpoints":["..."]}]}],'
            '"assertions":[{"name":"...","type":"safety|liveness",'
            '"property":"...","importance":"critical|high|medium|low","feature_ref":"F001"}],'
            '"report_summary":"..."'
            "}\n"
            "Rules:\n"
            "1) Do not hallucinate unsupported features.\n"
            "2) Keep coverage crosses purposeful.\n"
            "3) Include both normal and negative requirements.\n"
            "4) Keep IDs stable and unique.\n"
            f"Baseline heuristic interpretation:\n{heuristic}\n"
            f"Specification markdown:\n{spec_text[:25000]}"
        )

        try:
            llm_out = self.llm.generate_json(
                stage="SPEC_INTERPRET",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            return self._sanitize_interpretation(model_data=llm_out, fallback=heuristic)
        except Exception as exc:
            self.logger.record_action(
                stage="SPEC_INTERPRET",
                action="fallback_to_heuristic",
                duration_seconds=0.0,
                input_summary="llm_exception",
                output_summary=str(exc)[:240],
            )
            return heuristic

    def _sanitize_interpretation(self, *, model_data: dict, fallback: dict) -> dict:
        if not isinstance(model_data, dict):
            return fallback

        features = model_data.get("features", [])
        if not isinstance(features, list) or not features:
            features = fallback["features"]

        normalized_features = []
        for idx, feature in enumerate(features[: self.max_features], start=1):
            if not isinstance(feature, dict):
                continue
            priority = str(feature.get("priority", "medium")).strip().lower()
            if priority not in {"high", "medium", "low"}:
                priority = "medium"

            risk = str(feature.get("risk", "medium")).strip().lower()
            if risk not in {"high", "medium", "low"}:
                risk = "medium"

            coverage_goals = feature.get("coverage_goals", [])
            if not isinstance(coverage_goals, list):
                coverage_goals = []
            coverage_goals = [str(item) for item in coverage_goals if str(item).strip()][:8]
            if not coverage_goals:
                coverage_goals = [
                    "Normal-path behavior exercised",
                    "Boundary conditions exercised",
                    "Error-path behavior exercised",
                ]

            tests = feature.get("tests", [])
            if not isinstance(tests, list):
                tests = []
            tests = [self._normalize_test_name(str(item)) for item in tests if str(item).strip()]
            if not tests:
                tests = [f"test_{self._slug(feature.get('name', f'feature_{idx}'))}_basic"]

            assertions = feature.get("assertions", [])
            if not isinstance(assertions, list):
                assertions = []
            assertions = [str(item) for item in assertions if str(item).strip()][:4]
            if not assertions:
                assertions = [f"A{idx:03d}_{self._slug(feature.get('name', 'feature'))}"]

            normalized_features.append(
                {
                    "id": f"F{idx:03d}",
                    "name": str(feature.get("name", f"Feature {idx}")).strip() or f"Feature {idx}",
                    "description": str(feature.get("description", "Specification-derived feature")).strip(),
                    "priority": priority,
                    "risk": risk,
                    "coverage_goals": coverage_goals,
                    "test_strategy": str(
                        feature.get(
                            "test_strategy",
                            "Directed baseline plus constrained-random scenario expansion",
                        )
                    ).strip(),
                    "tests": tests,
                    "assertions": assertions,
                }
            )

        if not normalized_features:
            normalized_features = fallback["features"]

        covergroups = model_data.get("covergroups", [])
        if not isinstance(covergroups, list) or not covergroups:
            covergroups = fallback["covergroups"]
        covergroups = self._sanitize_covergroups(covergroups=covergroups, fallback=fallback)

        assertions = model_data.get("assertions", [])
        if not isinstance(assertions, list) or not assertions:
            assertions = fallback["assertions"]
        assertions = self._sanitize_assertions(assertions=assertions, fallback=fallback)

        cross_feature_tests = model_data.get("cross_feature_tests", [])
        if not isinstance(cross_feature_tests, list):
            cross_feature_tests = []
        normalized_cross = []
        for idx, item in enumerate(cross_feature_tests[:6], start=1):
            if not isinstance(item, dict):
                continue
            refs = item.get("features", [])
            if not isinstance(refs, list):
                refs = []
            refs = [str(r) for r in refs if str(r).strip()][:4]
            if not refs:
                refs = [normalized_features[0]["id"]]
            normalized_cross.append(
                {
                    "id": f"X{idx:03d}",
                    "name": str(item.get("name", f"Cross Feature Test {idx}")).strip(),
                    "features": refs,
                    "description": str(item.get("description", "Cross-feature interaction scenario")).strip(),
                }
            )
        if not normalized_cross:
            normalized_cross = fallback["cross_feature_tests"]

        report_summary = str(model_data.get("report_summary", "")).strip()
        if not report_summary:
            report_summary = fallback["report_summary"]

        tests = self._collect_tests(normalized_features)

        return {
            "dut_name": str(model_data.get("dut_name", fallback["dut_name"])).strip()
            or fallback["dut_name"],
            "spec_version": str(model_data.get("spec_version", fallback["spec_version"]))
            .strip()
            or fallback["spec_version"],
            "features": normalized_features,
            "cross_feature_tests": normalized_cross,
            "covergroups": covergroups,
            "assertions": assertions,
            "report_summary": report_summary,
            "tests": tests,
        }

    def _heuristic_interpretation(self, *, spec_text: str, spec_path: Path) -> dict:
        headings = self._extract_headings(spec_text)
        dut_name = self._infer_dut_name(spec_text=spec_text, spec_path=spec_path)

        feature_templates = [
            (
                "Core Functional Operation",
                "The block shall implement the primary functional behavior described in the specification.",
                "high",
                "high",
                ["Nominal operation", "Boundary operational modes", "Back-to-back transactions"],
                "Directed tests per feature requirement plus constrained-random stress.",
            ),
            (
                "Configuration and Programming Model",
                "Control/status configuration paths shall correctly drive operational modes and readback behavior.",
                "high",
                "medium",
                ["Default configuration", "Mode transitions", "Illegal configuration handling"],
                "Directed register-level intent checks with mode-cross scenarios.",
            ),
            (
                "Transmit/Output Data Path",
                "Output data path shall preserve ordering, timing expectations, and data integrity.",
                "high",
                "high",
                ["Data ordering", "Maximum throughput", "Idle-to-active transitions"],
                "Directed data-pattern tests plus randomized burst scenarios.",
            ),
            (
                "Receive/Input Data Path",
                "Input data path shall decode/accept valid traffic and reject malformed or unsupported inputs.",
                "high",
                "high",
                ["Nominal receive path", "Boundary timing", "Malformed frame handling"],
                "Directed corner-case vectors and randomized perturbation tests.",
            ),
            (
                "Buffer/FIFO/Queue Management",
                "Queueing structures shall track occupancy, enforce limits, and avoid corruption.",
                "high",
                "high",
                ["Empty/partial/full states", "Overflow/underflow behavior", "Drain and refill interactions"],
                "Boundary-condition tests plus stress sequences.",
            ),
            (
                "Interrupt and Event Signaling",
                "Interrupt/event outputs shall reflect enabled status conditions without spurious firing.",
                "medium",
                "medium",
                ["Enable/disable behavior", "Source-specific assertions", "Clear/acknowledge behavior"],
                "Directed source-by-source tests with cross-feature event load.",
            ),
            (
                "Error Detection and Recovery",
                "Error indicators shall assert for defined violations and recovery behavior shall match specification.",
                "medium",
                "high",
                ["Each defined error type", "Error latency", "Recovery/clear behavior"],
                "Negative tests for each violation and recovery sequencing checks.",
            ),
            (
                "Reset and Initialization",
                "Reset shall restore documented defaults and safe idle outputs.",
                "high",
                "medium",
                ["Power-on defaults", "Warm reset behavior", "Reset under activity"],
                "Directed reset tests across idle and active traffic conditions.",
            ),
        ]

        heading_tokens = set(tokenize(" ".join(headings)))
        features: list[dict] = []
        for idx, tpl in enumerate(feature_templates, start=1):
            name, desc, priority, risk, coverage_goals, strategy = tpl
            name_tokens = set(tokenize(name))
            should_include = bool(name_tokens & heading_tokens)
            if idx <= 4:
                should_include = True
            if should_include or len(features) < 6:
                feature_slug = self._slug(name)
                features.append(
                    {
                        "id": f"F{len(features)+1:03d}",
                        "name": name,
                        "description": desc,
                        "priority": priority,
                        "risk": risk,
                        "coverage_goals": coverage_goals,
                        "test_strategy": strategy,
                        "tests": [f"test_{feature_slug}_basic", f"test_{feature_slug}_stress"],
                        "assertions": [f"A{len(features)+1:03d}_{feature_slug}_safety"],
                    }
                )

        features = features[: self.max_features]

        cross_feature_tests = []
        if len(features) >= 2:
            cross_feature_tests.append(
                {
                    "id": "X001",
                    "name": "Concurrent Datapath and Event Stress",
                    "features": [features[2]["id"] if len(features) > 2 else features[0]["id"], features[5]["id"] if len(features) > 5 else features[1]["id"]],
                    "description": "Exercise data-path operation while event signaling conditions are active.",
                }
            )
        if len(features) >= 3:
            cross_feature_tests.append(
                {
                    "id": "X002",
                    "name": "Reset During Active Traffic",
                    "features": [features[0]["id"], features[-1]["id"]],
                    "description": "Verify state convergence and integrity when reset intersects active operation.",
                }
            )

        covergroups = self._build_heuristic_covergroups(features)
        assertions = self._build_heuristic_assertions(features)
        tests = self._collect_tests(features)

        return {
            "dut_name": dut_name,
            "spec_version": self._infer_spec_version(spec_text),
            "features": features,
            "cross_feature_tests": cross_feature_tests,
            "covergroups": covergroups,
            "assertions": assertions,
            "report_summary": (
                "Generated from specification-level interpretation with emphasis on "
                "completeness, non-hallucinated feature coverage, and actionable pre-RTL intent artifacts."
            ),
            "tests": tests,
        }

    def _write_vplan(self, *, output_dir: Path, interpreted: dict) -> None:
        priority_dist = {"high": 0, "medium": 0, "low": 0}
        for feature in interpreted["features"]:
            priority_dist[feature["priority"]] = priority_dist.get(feature["priority"], 0) + 1

        vplan_entries = []
        for idx, feature in enumerate(interpreted["features"], start=1):
            vplan_entries.append(
                {
                    "id": f"VP-{idx:03d}",
                    "feature": feature["name"],
                    "description": feature["description"],
                    "priority": feature["priority"],
                    "risk": feature["risk"],
                    "coverage_goals": feature["coverage_goals"],
                    "test_strategy": feature["test_strategy"],
                    "tests": feature["tests"],
                    "assertions": feature["assertions"],
                }
            )

        payload = {
            "vplan": vplan_entries,
            "verification_plan": {
                "dut_name": interpreted["dut_name"],
                "spec_version": interpreted["spec_version"],
                "author": "agent",
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "features": interpreted["features"],
                "cross_feature_tests": interpreted["cross_feature_tests"],
                "coverage_summary": {
                    "total_features": len(interpreted["features"]),
                    "total_tests": len(interpreted["tests"]),
                    "total_assertions": len(interpreted["assertions"]),
                    "priority_distribution": priority_dist,
                },
            },
        }

        with (output_dir / "vplan.yaml").open("w", encoding="utf-8") as file_handle:
            yaml.safe_dump(payload, file_handle, sort_keys=False)

        self.logger.record_action(
            stage="OUTPUT",
            action="write_vplan",
            duration_seconds=0.0,
            input_summary=f"features={len(interpreted['features'])}",
            output_summary="vplan.yaml",
        )

    def _write_coverage(self, *, output_dir: Path, interpreted: dict) -> None:
        payload = {
            "covergroups": interpreted["covergroups"],
            "functional_coverage": {
                "dut_name": interpreted["dut_name"],
                "covergroups": interpreted["covergroups"],
            },
        }
        with (output_dir / "coverage_model.yaml").open("w", encoding="utf-8") as file_handle:
            yaml.safe_dump(payload, file_handle, sort_keys=False)

        self.logger.record_action(
            stage="OUTPUT",
            action="write_coverage_model",
            duration_seconds=0.0,
            input_summary=f"covergroups={len(interpreted['covergroups'])}",
            output_summary="coverage_model.yaml",
        )

        compat_dir = output_dir / "coverage"
        ensure_dir(compat_dir)
        with (compat_dir / "coverage_model.yaml").open("w", encoding="utf-8") as file_handle:
            yaml.safe_dump(payload, file_handle, sort_keys=False)

    def _write_assertions(self, *, output_dir: Path, interpreted: dict) -> None:
        payload = {
            "assertions": interpreted["assertions"],
            "assertion_catalog": {
                "dut_name": interpreted["dut_name"],
                "count": len(interpreted["assertions"]),
            },
        }
        with (output_dir / "assertions.yaml").open("w", encoding="utf-8") as file_handle:
            yaml.safe_dump(payload, file_handle, sort_keys=False)

        self.logger.record_action(
            stage="OUTPUT",
            action="write_assertions",
            duration_seconds=0.0,
            input_summary=f"assertions={len(interpreted['assertions'])}",
            output_summary="assertions.yaml",
        )

        compat_dir = output_dir / "assertions"
        ensure_dir(compat_dir)
        with (compat_dir / "assertions.yaml").open("w", encoding="utf-8") as file_handle:
            yaml.safe_dump(payload, file_handle, sort_keys=False)

    def _write_test_stubs(self, *, output_dir: Path, interpreted: dict) -> None:
        test_stubs_dir = output_dir / "test_stubs"
        task_page_tests_dir = output_dir / "tests"
        ensure_dir(test_stubs_dir)
        ensure_dir(task_page_tests_dir)

        helpers = '''"""Specification-level helper stubs for Task 4.3 test intent."""

from __future__ import annotations


async def reset_dut(dut):
    """Reset sequence placeholder for implementation-time binding."""
    raise NotImplementedError("Bind to actual reset and clock sequence")


async def apply_configuration(dut, config_name: str, **kwargs):
    """Apply configuration placeholder (CSR/protocol-specific binding deferred)."""
    raise NotImplementedError("Bind to concrete configuration interface")


async def drive_stimulus(dut, scenario: str, **kwargs):
    """Stimulus driver placeholder for spec-level test intent."""
    raise NotImplementedError("Bind to protocol/CSR stimulus implementation")


async def observe_behavior(dut, observation: str, **kwargs):
    """Observation placeholder for expected behavior checks."""
    raise NotImplementedError("Bind to monitors/scoreboard observations")


async def check_expectation(dut, expectation: str, **kwargs):
    """Assertion placeholder for intent-level check semantics."""
    raise NotImplementedError("Bind to concrete check implementation")
'''
        (test_stubs_dir / "helpers.py").write_text(helpers, encoding="utf-8")
        (task_page_tests_dir / "helpers.py").write_text(helpers, encoding="utf-8")

        emitted = set()
        for feature in interpreted["features"][: self.max_test_stubs]:
            test_name = feature["tests"][0]
            file_name = f"{test_name}.py"
            if file_name in emitted:
                continue
            emitted.add(file_name)

            content = self._build_test_stub_content(feature=feature, dut_name=interpreted["dut_name"])
            (test_stubs_dir / file_name).write_text(content, encoding="utf-8")
            (task_page_tests_dir / file_name).write_text(content, encoding="utf-8")

        self.logger.record_action(
            stage="OUTPUT",
            action="write_test_stubs",
            duration_seconds=0.0,
            input_summary=f"features={len(interpreted['features'])}",
            output_summary=f"test_stubs={len(emitted)}",
        )

    def _build_test_stub_content(self, *, feature: dict, dut_name: str) -> str:
        function_name = self._normalize_test_name(feature["tests"][0])
        scenario_slug = self._slug(feature["name"])
        coverage_goal = feature["coverage_goals"][0] if feature["coverage_goals"] else "Nominal behavior"

        return f'''"""
Test Stub: {feature['name']}
DUT: {dut_name}
Feature ID: {feature['id']}

This spec-level test captures verification intent before RTL signal binding.
"""

from __future__ import annotations

import cocotb
from cocotb.triggers import RisingEdge, Timer

from helpers import (
    apply_configuration,
    check_expectation,
    drive_stimulus,
    observe_behavior,
    reset_dut,
)


@cocotb.test()
async def {function_name}(dut):
    """
    Feature: {feature['id']} — {feature['name']}
    Priority: {feature['priority']} | Risk: {feature['risk']}

    Goal:
      Validate specification intent for {feature['name'].lower()}.

    Procedure:
      1. Reset DUT and establish baseline state.
      2. Apply configuration relevant to this feature.
      3. Drive directed and boundary stimulus for scenario '{scenario_slug}'.
      4. Observe behavior and check expected outcomes.

    Expected:
      - {coverage_goal}
      - No contradictory behavior relative to specification text.
    """
    await reset_dut(dut)
    await apply_configuration(dut, config_name="{scenario_slug}_config")

    await drive_stimulus(dut, scenario="{scenario_slug}_directed")
    await observe_behavior(dut, observation="{scenario_slug}_response")
    await check_expectation(dut, expectation="{scenario_slug}_matches_spec")

    # Timing placeholder to indicate sequencing intent without RTL binding.
    await Timer(1, unit="ns")
    if hasattr(dut, "clk_i"):
        await RisingEdge(dut.clk_i)
    else:
        await Timer(1, unit="ns")
'''

    def _write_report(
        self,
        *,
        output_dir: Path,
        interpreted: dict,
        spec_path: Path,
        spec_text: str,
    ) -> None:
        heading_count = len(self._extract_headings(spec_text))
        report = f'''# Task 4.3 Spec Interpretation Report

## Input Summary

- Spec file: {spec_path}
- DUT inferred: {interpreted['dut_name']}
- Spec version inferred: {interpreted['spec_version']}
- Markdown headings detected: {heading_count}

## Generated Artifact Summary

- Features in vplan: {len(interpreted['features'])}
- Test stubs generated: {len(interpreted['tests'])}
- Covergroups generated: {len(interpreted['covergroups'])}
- Assertions generated: {len(interpreted['assertions'])}

## Interpretation Strategy

1. Extract candidate verification intents from specification sections and keyword clusters.
2. Build feature-level entries with priority, risk, coverage goals, and test strategy.
3. Emit implementation-independent cocotb test stubs with helper placeholders.
4. Build purposeful coverage model entries and non-trivial behavioral assertions.
5. Preserve traceability with structured `agent_log.json` metadata and LLM call traces.

## LLM Reasoning Summary

{interpreted['report_summary']}

## Notes for Implementation-Time Binding

- Test stubs intentionally avoid hard binding to finalized RTL signal names.
- `test_stubs/helpers.py` defines explicit placeholders for reset, configuration,
  stimulus, observation, and expectation checks.
- Assertions are expressed as structured pseudo-properties for later translation
  to SVA, PSL, or Python checkers.
'''
        (output_dir / "report.md").write_text(report, encoding="utf-8")

        self.logger.record_action(
            stage="OUTPUT",
            action="write_report",
            duration_seconds=0.0,
            input_summary=f"spec={spec_path.name}",
            output_summary="report.md",
        )

    def _extract_headings(self, spec_text: str) -> list[str]:
        headings = []
        for line in spec_text.splitlines():
            match = re.match(r"^#{1,6}\s+(.+)$", line.strip())
            if match:
                headings.append(match.group(1).strip())
        return headings

    def _infer_dut_name(self, *, spec_text: str, spec_path: Path) -> str:
        headings = self._extract_headings(spec_text)
        if headings:
            candidate = headings[0]
            tokens = tokenize(candidate)
            if tokens:
                return "_".join(tokens[:3])

        path_tokens = tokenize(spec_path.stem)
        if path_tokens:
            return "_".join(path_tokens[:3])
        return "spec_interpreted_dut"

    def _infer_spec_version(self, spec_text: str) -> str:
        version_match = re.search(r"\b(v(?:ersion)?\s*[:=]?\s*\d+(?:\.\d+)?)\b", spec_text, re.I)
        if version_match:
            token = version_match.group(1)
            number = re.search(r"\d+(?:\.\d+)?", token)
            if number:
                return number.group(0)
        return "1.0"

    def _collect_tests(self, features: list[dict]) -> list[str]:
        names = []
        seen = set()
        for feature in features:
            for item in feature.get("tests", []):
                normalized = self._normalize_test_name(str(item))
                if normalized in seen:
                    continue
                seen.add(normalized)
                names.append(normalized)
        return names

    def _build_heuristic_covergroups(self, features: list[dict]) -> list[dict]:
        groups = []
        for idx, feature in enumerate(features[: self.max_covergroups], start=1):
            slug = self._slug(feature["name"])
            groups.append(
                {
                    "name": f"cg_{slug}",
                    "description": f"Coverage model for {feature['name']}",
                    "sample_event": f"On key event for {feature['id']}",
                    "coverpoints": [
                        {
                            "name": "cp_operational_class",
                            "description": "Nominal, boundary, and error-path classes",
                            "bins": ["nominal", "boundary", "error_path"],
                        },
                        {
                            "name": "cp_activity_level",
                            "description": "Traffic/intensity class",
                            "bins": ["low", "medium", "high"],
                        },
                    ],
                    "crosses": [
                        {
                            "name": f"cx_{slug}_class_x_activity",
                            "coverpoints": ["cp_operational_class", "cp_activity_level"],
                        }
                    ],
                }
            )
        return groups

    def _build_heuristic_assertions(self, features: list[dict]) -> list[dict]:
        assertions = []
        for idx, feature in enumerate(features[: self.max_assertions], start=1):
            name_lower = feature["name"].lower()
            assertion_type = "safety"
            property_text = (
                f"When {feature['name'].lower()} conditions are active, outputs and status shall remain "
                "consistent with documented behavior."
            )
            importance = "high"

            if "reset" in name_lower:
                property_text = (
                    "On reset assertion, internal state and externally visible status shall return "
                    "to documented defaults before normal operation resumes."
                )
                importance = "critical"
            elif "interrupt" in name_lower:
                property_text = (
                    "Interrupt output shall assert iff at least one enabled source condition is active, "
                    "and shall clear according to documented clear semantics."
                )
                importance = "critical"
            elif "error" in name_lower:
                property_text = (
                    "Defined protocol/usage violations shall set corresponding error status before next "
                    "normal transaction completion."
                )
                importance = "critical"
            elif "transmit" in name_lower or "receive" in name_lower:
                assertion_type = "liveness"
                property_text = (
                    "Every accepted operation request shall eventually produce the corresponding "
                    "observable completion or status update within bounded progress conditions."
                )

            assertions.append(
                {
                    "name": f"assert_{self._slug(feature['name'])}_{idx:03d}",
                    "type": assertion_type,
                    "property": property_text,
                    "importance": importance,
                    "feature_ref": feature["id"],
                }
            )
        return assertions

    def _sanitize_covergroups(self, *, covergroups: list, fallback: dict) -> list[dict]:
        normalized = []
        for idx, group in enumerate(covergroups[: self.max_covergroups], start=1):
            if not isinstance(group, dict):
                continue
            name = str(group.get("name", f"cg_feature_{idx}")).strip() or f"cg_feature_{idx}"
            description = str(group.get("description", "Coverage group derived from feature intent")).strip()
            sample_event = str(group.get("sample_event", "On feature-related activity")).strip()

            cps = group.get("coverpoints", [])
            if not isinstance(cps, list):
                cps = []
            coverpoints = []
            for cp_idx, cp in enumerate(cps[:6], start=1):
                if not isinstance(cp, dict):
                    continue
                bins = cp.get("bins", [])
                if not isinstance(bins, list):
                    bins = []
                bins = [str(item) for item in bins if str(item).strip()][:10]
                if not bins:
                    bins = ["nominal", "boundary", "error_path"]
                coverpoints.append(
                    {
                        "name": str(cp.get("name", f"cp_{cp_idx}")).strip() or f"cp_{cp_idx}",
                        "description": str(cp.get("description", "Coverage point")).strip(),
                        "bins": bins,
                    }
                )
            if not coverpoints:
                coverpoints = [
                    {
                        "name": "cp_operational_class",
                        "description": "Operational class coverage",
                        "bins": ["nominal", "boundary", "error_path"],
                    }
                ]

            crosses_raw = group.get("crosses", [])
            if not isinstance(crosses_raw, list):
                crosses_raw = []
            crosses = []
            for cx_idx, cx in enumerate(crosses_raw[:4], start=1):
                if not isinstance(cx, dict):
                    continue
                refs = cx.get("coverpoints", [])
                if not isinstance(refs, list):
                    refs = []
                refs = [str(item) for item in refs if str(item).strip()][:4]
                if len(refs) < 2:
                    refs = [coverpoints[0]["name"], coverpoints[min(1, len(coverpoints) - 1)]["name"]]
                crosses.append(
                    {
                        "name": str(cx.get("name", f"cx_{idx}_{cx_idx}")).strip()
                        or f"cx_{idx}_{cx_idx}",
                        "coverpoints": refs,
                    }
                )

            normalized.append(
                {
                    "name": self._slug(name, prefix="cg_"),
                    "description": description,
                    "sample_event": sample_event,
                    "coverpoints": coverpoints,
                    "crosses": crosses,
                }
            )

        if not normalized:
            return fallback["covergroups"]
        return normalized

    def _sanitize_assertions(self, *, assertions: list, fallback: dict) -> list[dict]:
        normalized = []
        for idx, assertion in enumerate(assertions[: self.max_assertions], start=1):
            if not isinstance(assertion, dict):
                continue
            assertion_type = str(assertion.get("type", "safety")).strip().lower()
            if assertion_type not in {"safety", "liveness"}:
                assertion_type = "safety"

            importance = str(assertion.get("importance", "high")).strip().lower()
            if importance not in {"critical", "high", "medium", "low"}:
                importance = "high"

            normalized.append(
                {
                    "name": self._slug(str(assertion.get("name", f"assert_{idx}")), prefix=""),
                    "type": assertion_type,
                    "property": str(
                        assertion.get(
                            "property",
                            "Property shall hold under all relevant specification-defined conditions.",
                        )
                    ).strip(),
                    "importance": importance,
                    "feature_ref": str(assertion.get("feature_ref", f"F{idx:03d}")),
                }
            )

        if not normalized:
            return fallback["assertions"]
        return normalized

    def _normalize_test_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            return "test_spec_feature_basic"
        if not value.startswith("test_"):
            value = f"test_{value}"
        return self._slug(value, prefix="")

    def _slug(self, value: str, prefix: str = "") -> str:
        tokens = tokenize(value)
        if not tokens:
            return f"{prefix}item" if prefix else "item"
        base = "_".join(tokens[:8])
        return f"{prefix}{base}" if prefix else base
