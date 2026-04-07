"""Coverage parsing and target extraction for Task 2.3 CDG."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable


@dataclass
class CoverageMetrics:
    line: float = 0.0
    branch: float = 0.0
    toggle: float = 0.0
    functional: float = 0.0
    uncovered_targets: list[str] = field(default_factory=list)

    @property
    def combined_for_convergence(self) -> float:
        # Task text defines convergence on line+branch+functional average.
        return (self.line + self.branch + self.functional) / 3.0


class CoverageAnalyzer:
    """Parses local coverage artifacts into normalized metrics."""

    _FUNC_HEADER_RE = re.compile(r"^functional_coverage:\s*([0-9]+(?:\.[0-9]+)?)\s*$")
    _FUNC_BIN_RE = re.compile(r"^([\w\.:-]+):\s*(\d+)\/(\d+)\s*$")

    def parse_metrics(
        self,
        line_info: Path,
        branch_info: Path,
        toggle_info: Path,
        functional_report: Path,
    ) -> CoverageMetrics:
        functional, uncovered_targets = self._parse_functional_report(functional_report)
        line = self._parse_lcov_ratio(line_info, data_prefix="DA:")
        branch = self._parse_lcov_ratio(branch_info, data_prefix="BRDA:")
        toggle = self._parse_toggle_ratio(toggle_info)

        return CoverageMetrics(
            line=line,
            branch=branch,
            toggle=toggle,
            functional=functional,
            uncovered_targets=uncovered_targets,
        )

    def _parse_functional_report(self, report_path: Path) -> tuple[float, list[str]]:
        if not report_path.exists():
            return 0.0, ["functional_report:missing"]

        functional = 0.0
        uncovered: list[str] = []

        for line in report_path.read_text(encoding="utf-8").splitlines():
            m_header = self._FUNC_HEADER_RE.match(line.strip())
            if m_header:
                functional = float(m_header.group(1))
                continue

            m_bin = self._FUNC_BIN_RE.match(line.strip())
            if not m_bin:
                continue

            name = m_bin.group(1)
            covered = int(m_bin.group(2))
            total = int(m_bin.group(3))
            if covered < total:
                uncovered.append(f"{name}:{covered}/{total}")

        return functional, uncovered

    def _parse_lcov_ratio(self, info_path: Path, data_prefix: str) -> float:
        if not info_path.exists():
            return 0.0

        covered = 0
        total = 0

        for raw in info_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line.startswith(data_prefix):
                continue

            total += 1
            if data_prefix == "DA:":
                # DA:<line>,<exec_count>
                fields = line[3:].split(",")
                if len(fields) >= 2:
                    try:
                        hit = int(fields[1])
                    except ValueError:
                        hit = 0
                    if hit > 0:
                        covered += 1
            else:
                # BRDA:<line>,<block>,<branch>,<taken>
                fields = line[5:].split(",")
                if len(fields) >= 4:
                    taken_str = fields[3]
                    if taken_str != "-":
                        try:
                            taken = int(taken_str)
                        except ValueError:
                            taken = 0
                        if taken > 0:
                            covered += 1

        return 100.0 * covered / total if total else 0.0

    def _parse_toggle_ratio(self, info_path: Path) -> float:
        # Verilator toggle exports are not perfectly standardized by tool version.
        # Try branch-style first, then DA-style fallback.
        ratio = self._parse_lcov_ratio(info_path, data_prefix="BRDA:")
        if ratio > 0.0:
            return ratio
        return self._parse_lcov_ratio(info_path, data_prefix="DA:")

    def rank_focus_targets(
        self, uncovered_targets: Iterable[str], max_targets: int = 4
    ) -> list[str]:
        """Return a stable, priority-ordered list of uncovered targets."""
        targets = list(uncovered_targets)

        def sort_key(target: str) -> tuple[int, str]:
            # Priority heuristics: interrupt and long-message bins are often hard to close.
            priority = 10
            if "intr_write_kind" in target:
                priority = 1
            elif "msg_len_bucket" in target:
                priority = 2
            elif "msg_len_nonzero" in target:
                priority = 3
            return priority, target

        targets.sort(key=sort_key)
        return targets[:max_targets]
