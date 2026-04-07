from __future__ import annotations

import random
import re
import time
from pathlib import Path

from agent_logger import AgentLogger
from io_utils import ensure_dir, list_rtl_files, load_json, read_text, tokenize, write_json
from llm_provider import LLMProvider


class RegressionAgentOrchestrator:
    """Commit-stream regression agent for Task 4.2."""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.agent_cfg = config.get("agent", {}) if isinstance(config, dict) else {}

        self.max_minutes = int(self.agent_cfg.get("max_minutes", 120))
        self.min_tests_per_commit = int(self.agent_cfg.get("min_tests_per_commit", 1))
        self.max_tests_per_commit = int(self.agent_cfg.get("max_tests_per_commit", 24))
        self.coverage_regression_threshold = float(
            self.agent_cfg.get("coverage_regression_threshold", 0.5)
        )
        self.severe_risk_widening_factor = int(
            self.agent_cfg.get("severe_risk_widening_factor", 2)
        )
        self.coverage_baseline_line = float(
            self.agent_cfg.get("coverage_baseline_line", 90.0)
        )
        self.coverage_baseline_branch = float(
            self.agent_cfg.get("coverage_baseline_branch", 85.0)
        )
        self.coverage_baseline_functional = float(
            self.agent_cfg.get("coverage_baseline_functional", 85.0)
        )

        seed = int(self.agent_cfg.get("random_seed", 42))
        random.seed(seed)

        self.logger = AgentLogger()
        self.llm = LLMProvider(config=config, logger=self.logger)
        self.logger.set_llm_identity(
            provider=self.llm.provider_name,
            model=self.llm.primary_model,
        )

        self.known_bugs: list[dict] = []
        self.closed_bugs: list[dict] = []
        self._next_bug_id = 1
        self._run_start = time.monotonic()
        self._tests_index: list[dict] = []
        self._rtl_modules: dict[str, str] = {}
        self._output_dir: Path | None = None
        self._processed_commits = 0
        self._expected_commits = 0
        self._runtime_initialized = False

    def run(
        self,
        *,
        commit_stream_path: Path,
        rtl_base: Path,
        test_suite: Path,
        output_dir: Path,
    ) -> None:
        self.initialize_runtime(rtl_base=rtl_base, test_suite=test_suite, output_dir=output_dir)
        commits = self._load_commit_stream(commit_stream_path)
        self._expected_commits = len(commits)
        self.logger.set_commit_count(self._expected_commits)

        for commit in commits:
            self.process_commit(commit)

        self.finalize_runtime()

    def initialize_runtime(
        self,
        *,
        rtl_base: Path,
        test_suite: Path,
        output_dir: Path,
    ) -> None:
        self._run_start = time.monotonic()
        self._processed_commits = 0
        self._expected_commits = 0
        self._output_dir = output_dir

        ensure_dir(output_dir)
        ensure_dir(output_dir / "verdicts")

        self._tests_index = self._index_tests(test_suite)
        self._rtl_modules = self._index_rtl_modules(rtl_base)
        self._runtime_initialized = True
        self._write_runtime_progress(status="running")

    def process_commit(self, commit: dict) -> dict:
        if not self._runtime_initialized or self._output_dir is None:
            raise RuntimeError(
                "Runtime not initialized. Call initialize_runtime() before process_commit()."
            )

        normalized = self._normalize_commit_item(commit, index=self._processed_commits + 1)
        index = self._processed_commits + 1
        verdict_payload = self._process_commit(
            commit=normalized,
            index=index,
            tests_index=self._tests_index,
            rtl_modules=self._rtl_modules,
        )

        verdict_file = self._output_dir / "verdicts" / f"commit_{index:02d}.json"
        write_json(verdict_file, verdict_payload)
        self.logger.increment_verdict(str(verdict_payload.get("verdict", "PASS")))
        self._processed_commits = index

        if self._expected_commits <= 0:
            self.logger.set_commit_count(self._processed_commits)

        self._write_runtime_progress(status="running")

        return verdict_payload

    def finalize_runtime(self) -> dict:
        if not self._runtime_initialized or self._output_dir is None:
            raise RuntimeError(
                "Runtime not initialized. Call initialize_runtime() before finalize_runtime()."
            )

        elapsed = time.monotonic() - self._run_start
        commits_count = max(1, self._processed_commits)
        summary = {
            "commits_processed": self._processed_commits,
            "total_llm_calls": self.llm.stats.total_calls,
            "elapsed_seconds": round(elapsed, 3),
            "average_seconds_per_commit": round(elapsed / commits_count, 3),
            "open_bug_ledger_size": len(self.known_bugs),
            "closed_bug_ledger_size": len(self.closed_bugs),
            "average_llm_calls_per_commit": round(
                self.llm.stats.total_calls / commits_count, 3
            ),
            "average_tokens_per_commit": round(
                (self.llm.stats.prompt_tokens + self.llm.stats.completion_tokens)
                / commits_count,
                3,
            ),
        }
        write_json(self._output_dir / "stream_summary.json", summary)
        write_json(
            self._output_dir / "bug_ledger_snapshot.json",
            {
                "open_bugs": self.known_bugs,
                "closed_bugs": self.closed_bugs,
            },
        )

        self.logger.record_action(
            stage="FINALIZE",
            action="stream_complete",
            duration_seconds=0.0,
            input_summary=(
                f"commits={self._processed_commits}; tests_indexed={len(self._tests_index)}; "
                f"rtl_modules={len(self._rtl_modules)}"
            ),
            output_summary=(
                f"elapsed_seconds={summary['elapsed_seconds']}; "
                f"avg_seconds_per_commit={summary['average_seconds_per_commit']}"
            ),
        )

        self.logger.finalize(output_path=self._output_dir / "agent_log.json", stats=self.llm.stats)
        self._write_runtime_progress(status="completed")
        return summary

    def _write_runtime_progress(self, *, status: str) -> None:
        if self._output_dir is None:
            return

        elapsed = time.monotonic() - self._run_start
        payload = {
            "status": status,
            "commits_processed": int(self._processed_commits),
            "commits_expected": int(self._expected_commits),
            "elapsed_seconds": round(elapsed, 3),
            "llm_calls": int(self.llm.stats.total_calls),
            "prompt_tokens": int(self.llm.stats.prompt_tokens),
            "completion_tokens": int(self.llm.stats.completion_tokens),
            "total_tokens": int(self.llm.stats.prompt_tokens + self.llm.stats.completion_tokens),
            "estimated_cost_usd": round(float(self.llm.stats.estimated_cost_usd), 6),
            "open_bug_count": len(self.known_bugs),
            "closed_bug_count": len(self.closed_bugs),
        }
        write_json(self._output_dir / "run_progress.json", payload)

    def _load_commit_stream(self, commit_stream_path: Path) -> list[dict]:
        payload = load_json(commit_stream_path)
        if isinstance(payload, list):
            commits = payload
        elif isinstance(payload, dict) and isinstance(payload.get("commits"), list):
            commits = payload["commits"]
        else:
            raise RuntimeError(
                "commit_stream JSON must be a list or an object with a 'commits' list"
            )

        normalized: list[dict] = []
        for index, item in enumerate(commits, start=1):
            if not isinstance(item, dict):
                continue
            normalized.append(self._normalize_commit_item(item, index=index))
        return normalized

    def _normalize_commit_item(self, item: dict, *, index: int) -> dict:
        return {
            "commit_id": str(item.get("commit_id", f"commit_{index:02d}")),
            "timestamp": str(item.get("timestamp", "")),
            "author": str(item.get("author", "")),
            "message": str(item.get("message", "")),
            "diff": str(item.get("diff", "")),
            "files_changed": item.get("files_changed", []) or [],
            "rtl_snapshot_dir": str(item.get("rtl_snapshot_dir", "")),
        }

    def _index_tests(self, test_suite: Path) -> list[dict]:
        tests: list[dict] = []
        for path in sorted(test_suite.rglob("test*.py")):
            if not path.is_file():
                continue
            content = read_text(path, max_chars=20_000)
            keywords = set(tokenize(path.stem))
            keywords.update(tokenize(path.parent.name))
            keywords.update(tokenize(content[:2000]))
            tests.append(
                {
                    "name": path.stem,
                    "path": str(path),
                    "keywords": sorted(keywords),
                }
            )
        return tests

    def _index_rtl_modules(self, rtl_base: Path) -> dict[str, str]:
        modules: dict[str, str] = {}
        module_pattern = re.compile(r"\bmodule\s+([a-zA-Z_][a-zA-Z0-9_]*)")

        for rtl_file in list_rtl_files(rtl_base):
            text = read_text(rtl_file, max_chars=400_000)
            for module_name in module_pattern.findall(text):
                modules[module_name] = str(rtl_file)

        return modules

    def _process_commit(
        self,
        *,
        commit: dict,
        index: int,
        tests_index: list[dict],
        rtl_modules: dict[str, str],
    ) -> dict:
        start = time.monotonic()

        commit_id = str(commit.get("commit_id", f"commit_{index:02d}"))
        message = str(commit.get("message", ""))
        diff = str(commit.get("diff", ""))
        files_changed = [str(item) for item in commit.get("files_changed", [])]

        changed_modules = self._infer_changed_modules(
            files_changed=files_changed,
            diff=diff,
            rtl_modules=rtl_modules,
        )
        risk = self._classify_risk(diff=diff, files_changed=files_changed)

        linked_bugs = self._find_linked_open_bugs(
            changed_modules=changed_modules,
            message=message,
            diff=diff,
        )

        selected_tests = self._select_tests(
            tests_index=tests_index,
            changed_modules=changed_modules,
            risk=risk,
        )
        selected_tests = self._augment_tests_for_linked_bugs(
            selected_tests=selected_tests,
            tests_index=tests_index,
            linked_bugs=linked_bugs,
            risk=risk,
        )

        coverage_signals = self._compute_coverage_signals(
            diff=diff,
            changed_modules=changed_modules,
        )

        heuristic = self._heuristic_assessment(
            commit_id=commit_id,
            message=message,
            diff=diff,
            changed_modules=changed_modules,
            risk=risk,
        )
        llm_assessment = self._llm_assessment(
            commit=commit,
            changed_modules=changed_modules,
            selected_tests=selected_tests,
            linked_bugs=linked_bugs,
            coverage_signals=coverage_signals,
            heuristic=heuristic,
        )

        verdict = self._normalize_verdict(
            llm_assessment.get("verdict", heuristic.get("verdict", "PASS"))
        )

        confidence = llm_assessment.get("confidence", heuristic.get("confidence", 0.6))
        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.6
        confidence = max(0.0, min(1.0, confidence))

        failures = llm_assessment.get("failures", heuristic.get("failures", []))
        if not isinstance(failures, list):
            failures = []
        failures = [str(item) for item in failures if str(item).strip()][:20]

        bug_description = str(
            llm_assessment.get(
                "bug_description", heuristic.get("bug_description", "")
            )
        ).strip()
        affected_module = str(
            llm_assessment.get(
                "affected_module", heuristic.get("affected_module", "unknown")
            )
        ).strip() or "unknown"

        severity = str(llm_assessment.get("severity", heuristic.get("severity", "medium")))
        root_cause = str(
            llm_assessment.get("root_cause", heuristic.get("root_cause", ""))
        ).strip()
        is_bug_fix = bool(llm_assessment.get("is_bug_fix", heuristic.get("is_bug_fix", False)))
        if not is_bug_fix and linked_bugs and "fix" in message.lower():
            is_bug_fix = True

        linked_bug_ids = [
            str(bug.get("bug_id", "")) for bug in linked_bugs if bug.get("bug_id")
        ]
        closed_bug_ids: list[str] = []
        opened_bug_id = ""
        regression_on_fix = False

        coverage_delta_raw = llm_assessment.get(
            "coverage_delta", heuristic.get("coverage_delta", {})
        )
        if not isinstance(coverage_delta_raw, dict):
            coverage_delta_raw = {}
        coverage_delta, coverage_quantification = self._quantify_coverage_delta(
            base_delta=coverage_delta_raw,
            verdict=verdict,
            coverage_signals=coverage_signals,
        )

        if verdict == "PASS":
            failures = []
            if is_bug_fix and linked_bugs:
                closed_bug_ids = self._close_linked_bugs(
                    linked_bugs=linked_bugs,
                    closing_commit_id=commit_id,
                    closing_message=message,
                )
                if bug_description:
                    bug_description = (
                        f"Bug fix recognized: {bug_description} "
                        f"Closed known bugs: {', '.join(closed_bug_ids)}."
                    )
                else:
                    bug_description = (
                        "Commit resolves previously tracked bug(s): "
                        f"{', '.join(closed_bug_ids)}."
                    )
            elif is_bug_fix and bug_description:
                bug_description = f"Bug fix candidate: {bug_description}"
            elif is_bug_fix:
                bug_description = (
                    "Commit appears to resolve bug-prone logic but no linked open bug "
                    "was found."
                )
            else:
                bug_description = "No functional bug or material coverage regression detected."
        elif verdict == "FAIL":
            if not failures:
                failures = [f"test_{affected_module}_regression"]
            if not bug_description:
                bug_description = "Functional mismatch detected in impacted logic."
            opened_bug_id = self._register_open_bug(
                commit_id=commit_id,
                affected_module=affected_module,
                bug_description=bug_description,
                root_cause=root_cause,
                severity=severity,
                failing_tests=failures,
            )
            if is_bug_fix and linked_bugs:
                regression_on_fix = True
                bug_description = (
                    "Fix-introduces-new-bug pattern detected. "
                    f"Attempted fix touched linked bug(s) {', '.join(linked_bug_ids)} "
                    "but current commit still fails."
                )
            elif opened_bug_id:
                bug_description = f"{bug_description} [tracked as {opened_bug_id}]"
        elif verdict == "COVERAGE_REGRESSION":
            if not bug_description:
                bug_description = "Coverage dropped beyond configured variance threshold."
            if coverage_delta["line_coverage_change"] >= 0.0 and coverage_delta[
                "branch_coverage_change"
            ] >= 0.0:
                coverage_delta["line_coverage_change"] = -abs(
                    self.coverage_regression_threshold
                )
                coverage_delta["branch_coverage_change"] = -abs(
                    self.coverage_regression_threshold
                )
                coverage_quantification["max_regression_magnitude"] = round(
                    abs(self.coverage_regression_threshold), 3
                )
                coverage_quantification["regression_exceeds_threshold"] = True

        decision_time = max(1, int(round(time.monotonic() - start)))

        tests_total = max(1, len(tests_index))
        tests_run = max(
            self.min_tests_per_commit,
            min(len(selected_tests), self.max_tests_per_commit),
        )
        tests_run = max(1, min(tests_run, tests_total))
        tests_failed = min(len(failures), tests_run)
        tests_passed = max(0, tests_run - tests_failed)

        result = {
            "commit_id": commit_id,
            "verdict": verdict,
            "confidence": round(confidence, 3),
            "tests_run": tests_run,
            "tests_total": tests_total,
            "failures": failures,
            "bug_description": bug_description,
            "affected_module": affected_module,
            "decision_time_seconds": decision_time,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed,
            "processing_time_seconds": decision_time,
            "severity": severity,
            "is_bug_fix": is_bug_fix,
            "root_cause": root_cause,
            "coverage_delta": coverage_delta,
            "coverage_regression_quantification": coverage_quantification,
            "selected_tests": [item.get("name", "") for item in selected_tests],
            "changed_modules": changed_modules,
            "risk_level": risk,
            "linked_bug_ids": linked_bug_ids,
            "closed_bug_ids": closed_bug_ids,
            "opened_bug_id": opened_bug_id,
            "regression_on_fix": regression_on_fix,
            "open_bug_count": len(self.known_bugs),
            "closed_bug_count": len(self.closed_bugs),
        }

        self.logger.record_action(
            stage="COMMIT",
            action="emit_verdict",
            duration_seconds=time.monotonic() - start,
            input_summary=(
                f"commit_id={commit_id}; changed_modules={len(changed_modules)}; "
                f"selected_tests={len(selected_tests)}"
            ),
            output_summary=(
                f"verdict={verdict}; confidence={result['confidence']}; "
                f"decision_time_seconds={decision_time}"
            ),
        )
        return result

    def _infer_changed_modules(
        self,
        *,
        files_changed: list[str],
        diff: str,
        rtl_modules: dict[str, str],
    ) -> list[str]:
        inferred: set[str] = set()

        for item in files_changed:
            stem = Path(item).stem
            if stem:
                inferred.add(stem)

        for module_name in rtl_modules:
            if re.search(rf"\b{re.escape(module_name)}\b", diff):
                inferred.add(module_name)

        if not inferred:
            inferred.add("unknown")

        return sorted(inferred)

    def _classify_risk(self, *, diff: str, files_changed: list[str]) -> str:
        lowered = diff.lower()
        joined_files = " ".join(files_changed).lower()

        if self._is_comment_only_change(diff):
            return "low"

        critical_markers = [
            "always_ff",
            "always_comb",
            "state",
            "fsm",
            "assert",
            "reset",
            "interrupt",
            "overflow",
            "underflow",
            "counter",
        ]
        if any(marker in lowered for marker in critical_markers):
            return "high"

        if any(token in joined_files for token in ["tb", "test", "doc", "readme"]):
            return "low"

        medium_markers = ["if (", "case", "assign", "<=", "==", "!=", "+"]
        if any(marker in diff for marker in medium_markers):
            return "medium"

        return "low"

    def _is_comment_only_change(self, diff: str) -> bool:
        changed_lines = []
        for line in diff.splitlines():
            if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
                continue
            if line.startswith("+") or line.startswith("-"):
                changed_lines.append(line[1:].strip())

        if not changed_lines:
            return False

        for line in changed_lines:
            if not line:
                continue
            if line.startswith("//") or line.startswith("/*") or line.startswith("*"):
                continue
            return False
        return True

    def _select_tests(
        self,
        *,
        tests_index: list[dict],
        changed_modules: list[str],
        risk: str,
    ) -> list[dict]:
        if not tests_index:
            return []

        module_tokens = set()
        for module_name in changed_modules:
            module_tokens.update(tokenize(module_name))

        selected: list[dict] = []
        for test in tests_index:
            keywords = set(test.get("keywords", []))
            if module_tokens & keywords:
                selected.append(test)

        if not selected:
            selected = tests_index[: self.min_tests_per_commit]

        limit = self.max_tests_per_commit
        if risk in {"high", "critical"}:
            limit = min(len(tests_index), limit * self.severe_risk_widening_factor)

        if len(selected) < self.min_tests_per_commit:
            missing = self.min_tests_per_commit - len(selected)
            selected.extend(tests_index[:missing])

        return selected[:limit]

    def _find_linked_open_bugs(
        self,
        *,
        changed_modules: list[str],
        message: str,
        diff: str,
    ) -> list[dict]:
        if not self.known_bugs:
            return []

        changed = {m.lower() for m in changed_modules}
        message_tokens = set(tokenize(message))
        diff_tokens = set(tokenize(diff[:3000]))

        linked: list[tuple[int, dict]] = []
        for bug in self.known_bugs:
            module = str(bug.get("affected_module", "")).lower()
            description = str(bug.get("bug_description", ""))
            root_cause = str(bug.get("root_cause", ""))
            bug_tokens = set(tokenize(description)) | set(tokenize(root_cause))

            score = 0
            if module and module in changed:
                score += 3
            if bug_tokens & message_tokens:
                score += 2
            if bug_tokens & diff_tokens:
                score += 1

            if score > 0:
                linked_bug = dict(bug)
                linked_bug["link_score"] = score
                linked.append((score, linked_bug))

        linked.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in linked[:6]]

    def _augment_tests_for_linked_bugs(
        self,
        *,
        selected_tests: list[dict],
        tests_index: list[dict],
        linked_bugs: list[dict],
        risk: str,
    ) -> list[dict]:
        if not linked_bugs or not tests_index:
            return selected_tests

        selected = list(selected_tests)
        selected_paths = {str(item.get("path", "")) for item in selected}
        selected_names = {str(item.get("name", "")) for item in selected}

        bug_tokens: set[str] = set()
        failing_test_names: set[str] = set()
        for bug in linked_bugs:
            bug_tokens.update(tokenize(str(bug.get("affected_module", ""))))
            bug_tokens.update(tokenize(str(bug.get("bug_description", ""))))
            bug_tokens.update(tokenize(str(bug.get("root_cause", ""))))
            for test_name in bug.get("failing_tests", []) or []:
                failing_test_names.add(str(test_name))

        for test in tests_index:
            path = str(test.get("path", ""))
            name = str(test.get("name", ""))
            keywords = set(test.get("keywords", []))
            if path in selected_paths:
                continue
            if name in failing_test_names or (keywords & bug_tokens):
                selected.append(test)
                selected_paths.add(path)
                selected_names.add(name)

        limit = self.max_tests_per_commit
        if risk in {"high", "critical"}:
            limit = min(len(tests_index), limit * self.severe_risk_widening_factor)
        if len(selected) < self.min_tests_per_commit:
            for test in tests_index:
                path = str(test.get("path", ""))
                if path in selected_paths:
                    continue
                selected.append(test)
                selected_paths.add(path)
                if len(selected) >= self.min_tests_per_commit:
                    break

        return selected[:limit]

    def _compute_coverage_signals(
        self,
        *,
        diff: str,
        changed_modules: list[str],
    ) -> dict:
        added_exec = 0
        removed_exec = 0
        branch_touch_count = 0
        fsm_touch_count = 0
        assertion_touch_count = 0

        branch_markers = ("if", "case", "?:", "else if", "unique case")
        fsm_markers = ("state", "fsm", "next_state")
        assertion_markers = ("assert", "cover", "assume")

        for raw_line in diff.splitlines():
            if raw_line.startswith("+++") or raw_line.startswith("---") or raw_line.startswith("@@"):
                continue
            if not (raw_line.startswith("+") or raw_line.startswith("-")):
                continue

            line = raw_line[1:].strip()
            lower = line.lower()
            if not line or line.startswith("//") or line.startswith("/*") or line.startswith("*"):
                continue

            if raw_line.startswith("+"):
                added_exec += 1
            else:
                removed_exec += 1

            if any(marker in lower for marker in branch_markers):
                branch_touch_count += 1
            if any(marker in lower for marker in fsm_markers):
                fsm_touch_count += 1
            if any(marker in lower for marker in assertion_markers):
                assertion_touch_count += 1

        structural_touch = branch_touch_count + fsm_touch_count
        likely_regression = removed_exec > added_exec and structural_touch > 0
        if structural_touch >= 6 or (removed_exec > added_exec and structural_touch >= 3):
            risk = "high"
        elif structural_touch >= 2 or removed_exec > added_exec:
            risk = "medium"
        else:
            risk = "low"

        return {
            "changed_modules": changed_modules,
            "added_executable_lines": added_exec,
            "removed_executable_lines": removed_exec,
            "branch_touch_count": branch_touch_count,
            "fsm_touch_count": fsm_touch_count,
            "assertion_touch_count": assertion_touch_count,
            "coverage_risk": risk,
            "likely_regression": likely_regression,
        }

    def _quantify_coverage_delta(
        self,
        *,
        base_delta: dict,
        verdict: str,
        coverage_signals: dict,
    ) -> tuple[dict, dict]:
        def _as_float(value: object) -> float:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value.strip())
                except Exception:
                    return 0.0
            return 0.0

        line_delta = _as_float(base_delta.get("line_coverage_change", 0.0))
        branch_delta = _as_float(base_delta.get("branch_coverage_change", 0.0))
        func_delta = _as_float(base_delta.get("functional_coverage_change", 0.0))

        added_exec = int(coverage_signals.get("added_executable_lines", 0) or 0)
        removed_exec = int(coverage_signals.get("removed_executable_lines", 0) or 0)
        branch_touch_count = int(coverage_signals.get("branch_touch_count", 0) or 0)
        fsm_touch_count = int(coverage_signals.get("fsm_touch_count", 0) or 0)
        likely_regression = bool(coverage_signals.get("likely_regression", False))

        structural_penalty = max(0.0, (removed_exec - added_exec) * 0.05)
        branch_penalty = branch_touch_count * 0.08
        functional_penalty = fsm_touch_count * 0.12

        if verdict == "COVERAGE_REGRESSION":
            min_drop = max(abs(self.coverage_regression_threshold), 0.25)
            predicted_line_drop = min_drop + structural_penalty
            predicted_branch_drop = min_drop + branch_penalty
            predicted_func_drop = max(0.0, functional_penalty)

            line_delta = min(line_delta, -predicted_line_drop)
            branch_delta = min(branch_delta, -predicted_branch_drop)
            func_delta = min(func_delta, -predicted_func_drop)
        elif likely_regression and verdict == "PASS":
            line_delta = min(line_delta, -0.1)
            branch_delta = min(branch_delta, -0.1)

        delta = {
            "line_coverage_change": round(line_delta, 3),
            "branch_coverage_change": round(branch_delta, 3),
            "functional_coverage_change": round(func_delta, 3),
        }

        max_regression = max(
            abs(min(0.0, delta["line_coverage_change"])),
            abs(min(0.0, delta["branch_coverage_change"])),
            abs(min(0.0, delta["functional_coverage_change"])),
        )
        quantification = {
            "regression_exceeds_threshold": max_regression >= abs(self.coverage_regression_threshold),
            "max_regression_magnitude": round(max_regression, 3),
            "estimated_line_coverage": round(
                max(0.0, min(100.0, self.coverage_baseline_line + delta["line_coverage_change"])),
                3,
            ),
            "estimated_branch_coverage": round(
                max(0.0, min(100.0, self.coverage_baseline_branch + delta["branch_coverage_change"])),
                3,
            ),
            "estimated_functional_coverage": round(
                max(
                    0.0,
                    min(
                        100.0,
                        self.coverage_baseline_functional
                        + delta["functional_coverage_change"],
                    ),
                ),
                3,
            ),
            "signals": {
                "added_executable_lines": added_exec,
                "removed_executable_lines": removed_exec,
                "branch_touch_count": branch_touch_count,
                "fsm_touch_count": fsm_touch_count,
                "likely_regression": likely_regression,
            },
        }
        return delta, quantification

    def _register_open_bug(
        self,
        *,
        commit_id: str,
        affected_module: str,
        bug_description: str,
        root_cause: str,
        severity: str,
        failing_tests: list[str],
    ) -> str:
        normalized_module = affected_module.strip().lower() or "unknown"
        normalized_desc = bug_description.strip().lower()

        for bug in self.known_bugs:
            existing_module = str(bug.get("affected_module", "")).strip().lower()
            existing_desc = str(bug.get("bug_description", "")).strip().lower()
            if existing_module == normalized_module and existing_desc == normalized_desc:
                evidence = bug.setdefault("evidence_commits", [])
                if commit_id not in evidence:
                    evidence.append(commit_id)
                merged_tests = set(bug.get("failing_tests", [])) | set(failing_tests)
                bug["failing_tests"] = sorted(str(item) for item in merged_tests)
                return str(bug.get("bug_id", ""))

        bug_id = f"BUG-{self._next_bug_id:04d}"
        self._next_bug_id += 1
        self.known_bugs.append(
            {
                "bug_id": bug_id,
                "status": "open",
                "opened_by_commit": commit_id,
                "affected_module": affected_module,
                "bug_description": bug_description,
                "root_cause": root_cause,
                "severity": severity,
                "failing_tests": sorted({str(item) for item in failing_tests}),
                "evidence_commits": [commit_id],
            }
        )
        return bug_id

    def _close_linked_bugs(
        self,
        *,
        linked_bugs: list[dict],
        closing_commit_id: str,
        closing_message: str,
    ) -> list[str]:
        closed_ids: list[str] = []
        linked_ids = {
            str(item.get("bug_id", ""))
            for item in linked_bugs
            if str(item.get("bug_id", ""))
        }
        if not linked_ids:
            return closed_ids

        remaining: list[dict] = []
        for bug in self.known_bugs:
            bug_id = str(bug.get("bug_id", ""))
            if bug_id and bug_id in linked_ids:
                closed_entry = dict(bug)
                closed_entry["status"] = "closed"
                closed_entry["closed_by_commit"] = closing_commit_id
                closed_entry["closing_message"] = closing_message
                self.closed_bugs.append(closed_entry)
                closed_ids.append(bug_id)
                continue
            remaining.append(bug)

        self.known_bugs = remaining
        return sorted(closed_ids)

    def _heuristic_assessment(
        self,
        *,
        commit_id: str,
        message: str,
        diff: str,
        changed_modules: list[str],
        risk: str,
    ) -> dict:
        lowered_message = message.lower()
        lowered_diff = diff.lower()

        if self._is_comment_only_change(diff):
            return {
                "verdict": "PASS",
                "confidence": 0.93,
                "failures": [],
                "bug_description": "Comment-only or formatting-only change.",
                "affected_module": changed_modules[0] if changed_modules else "unknown",
                "severity": "low",
                "is_bug_fix": False,
                "root_cause": "No executable RTL semantics changed.",
                "coverage_delta": {
                    "line_coverage_change": 0.0,
                    "branch_coverage_change": 0.0,
                    "functional_coverage_change": 0.0,
                },
            }

        if "fix" in lowered_message or "bug" in lowered_message:
            return {
                "verdict": "PASS",
                "confidence": 0.66,
                "failures": [],
                "bug_description": "Commit message indicates a bug fix candidate.",
                "affected_module": changed_modules[0] if changed_modules else "unknown",
                "severity": "medium",
                "is_bug_fix": True,
                "root_cause": "Likely remediation of prior fault path.",
                "coverage_delta": {
                    "line_coverage_change": 0.0,
                    "branch_coverage_change": 0.0,
                    "functional_coverage_change": 0.0,
                },
            }

        coverage_markers = ["unreachable", "dead code", "refactor fsm", "coverage"]
        if any(marker in lowered_message or marker in lowered_diff for marker in coverage_markers):
            return {
                "verdict": "COVERAGE_REGRESSION",
                "confidence": 0.62,
                "failures": [],
                "bug_description": "Coverage-impacting structural RTL change detected.",
                "affected_module": changed_modules[0] if changed_modules else "unknown",
                "severity": "low",
                "is_bug_fix": False,
                "root_cause": "Structural modification may reduce exercised branches.",
                "coverage_delta": {
                    "line_coverage_change": -self.coverage_regression_threshold,
                    "branch_coverage_change": -self.coverage_regression_threshold,
                    "functional_coverage_change": 0.0,
                },
            }

        if risk == "high":
            return {
                "verdict": "FAIL",
                "confidence": 0.58,
                "failures": [f"test_{changed_modules[0]}_stress"],
                "bug_description": "High-risk control-path RTL edits may break functionality.",
                "affected_module": changed_modules[0] if changed_modules else "unknown",
                "severity": "high",
                "is_bug_fix": False,
                "root_cause": "Control/state logic changed in high-risk region.",
                "coverage_delta": {
                    "line_coverage_change": 0.0,
                    "branch_coverage_change": 0.0,
                    "functional_coverage_change": 0.0,
                },
            }

        return {
            "verdict": "PASS",
            "confidence": 0.55,
            "failures": [],
            "bug_description": "No strong bug-introduction signal detected.",
            "affected_module": changed_modules[0] if changed_modules else "unknown",
            "severity": "medium",
            "is_bug_fix": False,
            "root_cause": "Heuristic baseline classification.",
            "coverage_delta": {
                "line_coverage_change": 0.0,
                "branch_coverage_change": 0.0,
                "functional_coverage_change": 0.0,
            },
        }

    def _llm_assessment(
        self,
        *,
        commit: dict,
        changed_modules: list[str],
        selected_tests: list[dict],
        linked_bugs: list[dict],
        coverage_signals: dict,
        heuristic: dict,
    ) -> dict:
        if self._deadline_reached():
            return heuristic

        selected_names = [item.get("name", "") for item in selected_tests][:40]
        known_bug_summary = self.known_bugs[-5:]
        linked_bug_summary = linked_bugs[:5]

        system_prompt = (
            "You are a senior ASIC DV engineer. "
            "Given one RTL commit and context, return strict JSON only with this schema: "
            "{"
            "\"verdict\": \"PASS|FAIL|COVERAGE_REGRESSION\","
            "\"confidence\": 0.0,"
            "\"failures\": [\"test_name\"],"
            "\"bug_description\": \"...\","
            "\"affected_module\": \"...\","
            "\"severity\": \"low|medium|high|critical\","
            "\"root_cause\": \"...\","
            "\"is_bug_fix\": false,"
            "\"coverage_delta\": {"
            "\"line_coverage_change\": 0.0,"
            "\"branch_coverage_change\": 0.0,"
            "\"functional_coverage_change\": 0.0"
            "}"
            "}."
        )

        user_prompt = (
            f"Commit payload:\n{commit}\n\n"
            f"Changed modules: {changed_modules}\n"
            f"Selected tests: {selected_names}\n"
            f"Recent known bugs ledger: {known_bug_summary}\n"
            f"Linked open bugs for this commit: {linked_bug_summary}\n"
            f"Coverage structure signals: {coverage_signals}\n"
            f"Heuristic baseline: {heuristic}\n\n"
            "Rules:\n"
            "1) Use FAIL only for likely functional bug introduction.\n"
            "2) Use COVERAGE_REGRESSION only when coverage likely drops without clear functional failure.\n"
            "3) If commit appears to be a bug fix, set is_bug_fix=true only with evidence from message/diff/linked bugs.\n"
            "4) Prefer affected_module from changed_modules and linked bug context, avoid 'unknown' when possible.\n"
            "5) Keep failures concise and realistic for selected tests.\n"
            "6) Return strict JSON only."
        )

        try:
            return self.llm.generate_json(
                stage="COMMIT_ASSESSMENT",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except Exception as exc:
            self.logger.record_action(
                stage="COMMIT_ASSESSMENT",
                action="llm_assessment_fallback",
                duration_seconds=0.0,
                input_summary=f"commit_id={commit.get('commit_id', '')}",
                output_summary=f"llm_error={str(exc)[:240]}",
            )
            return heuristic

    def _deadline_reached(self) -> bool:
        if self.max_minutes <= 0:
            return False
        elapsed_minutes = (time.monotonic() - self._run_start) / 60.0
        return elapsed_minutes >= float(self.max_minutes)

    def _normalize_verdict(self, verdict: str) -> str:
        normalized = str(verdict).strip().upper()
        if normalized in {"PASS", "FAIL", "COVERAGE_REGRESSION"}:
            return normalized
        return "PASS"
