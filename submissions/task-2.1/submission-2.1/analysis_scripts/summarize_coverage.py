#!/usr/bin/env python3
"""Summarize lcov-style coverage.info files into Task 2.1 analysis inputs."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, TypedDict, cast

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT.parents[2]
ART = ROOT / "baseline_artifacts"
OUT_JSON = ART / "coverage_summary.json"
OUT_MD = ART / "coverage_summary.md"

DUTS = [
    "nexus_uart",
    "bastion_gpio",
    "warden_timer",
    "citadel_spi",
    "aegis_aes",
    "sentinel_hmac",
    "rampart_i2c",
]


class FileStats(TypedDict):
    line_total: int
    line_hit: int
    branch_total: int
    branch_hit: int
    uncovered_lines: list[int]


class UncoveredEntry(TypedDict):
    file: str
    uncovered_lines: int
    ranges: list[str]


def new_stats() -> FileStats:
    return {
        "line_total": 0,
        "line_hit": 0,
        "branch_total": 0,
        "branch_hit": 0,
        "uncovered_lines": [],
    }


def ranges_from_lines(lines: list[int]) -> list[str]:
    if not lines:
        return []
    lines = sorted(set(lines))
    out = []
    start = prev = lines[0]
    for line in lines[1:]:
        if line == prev + 1:
            prev = line
            continue
        out.append(f"{start}-{prev}" if start != prev else f"{start}")
        start = prev = line
    out.append(f"{start}-{prev}" if start != prev else f"{start}")
    return out


def largest_ranges(lines: list[int], limit: int = 8) -> list[str]:
    """Return the largest contiguous uncovered ranges first."""
    if not lines:
        return []
    lines = sorted(set(lines))
    ranges = []
    start = prev = lines[0]
    for line in lines[1:]:
        if line == prev + 1:
            prev = line
            continue
        ranges.append((start, prev))
        start = prev = line
    ranges.append((start, prev))

    ranges.sort(key=lambda r: (r[1] - r[0] + 1, -r[0]), reverse=True)

    formatted = []
    for start, end in ranges[:limit]:
        formatted.append(f"{start}-{end}" if start != end else f"{start}")
    return formatted


def normalize_source_path(raw_path: str, lcov_path: Path) -> str:
    """Normalize lcov SF paths into workspace-relative paths when possible."""
    p = Path(raw_path)
    if not p.is_absolute():
        p = (lcov_path.parent / p).resolve()
    else:
        p = p.resolve()

    try:
        return str(p.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def parse_lcov(path: Path) -> dict:
    per_file: dict[str, FileStats] = {}
    cur_file = None

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if line.startswith("SF:"):
                cur_file = normalize_source_path(line[3:], path)
                continue
            if not cur_file:
                continue

            if line.startswith("DA:"):
                m = re.match(r"DA:(\d+),(\d+)", line)
                if not m:
                    continue
                stats = per_file.setdefault(cur_file, new_stats())
                ln = int(m.group(1))
                hits = int(m.group(2))
                stats["line_total"] += 1
                if hits > 0:
                    stats["line_hit"] += 1
                else:
                    stats["uncovered_lines"].append(ln)
                continue

            if line.startswith("BRDA:"):
                parts = line[5:].split(",")
                if len(parts) != 4:
                    continue
                stats = per_file.setdefault(cur_file, new_stats())
                taken = parts[3]
                stats["branch_total"] += 1
                if taken != "-" and taken != "0":
                    stats["branch_hit"] += 1

    total_line = sum(v["line_total"] for v in per_file.values())
    hit_line = sum(v["line_hit"] for v in per_file.values())
    total_branch = sum(v["branch_total"] for v in per_file.values())
    hit_branch = sum(v["branch_hit"] for v in per_file.values())

    top_uncovered: list[UncoveredEntry] = []
    for file_path, stats in per_file.items():
        uncovered = stats["line_total"] - stats["line_hit"]
        if uncovered <= 0:
            continue
        top_uncovered.append(
            {
                "file": file_path,
                "uncovered_lines": uncovered,
                "ranges": largest_ranges(stats["uncovered_lines"], limit=8),
            }
        )

    top_uncovered.sort(key=lambda x: x["uncovered_lines"], reverse=True)

    line_cov = (100.0 * hit_line / total_line) if total_line else 0.0
    branch_cov = (100.0 * hit_branch / total_branch) if total_branch else 0.0

    return {
        "line_coverage": round(line_cov, 2),
        "branch_coverage": round(branch_cov, 2),
        "line_total": total_line,
        "line_hit": hit_line,
        "branch_total": total_branch,
        "branch_hit": hit_branch,
        "top_uncovered": top_uncovered[:12],
    }


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)

    summary = {}
    for dut in DUTS:
        info = ART / dut / "coverage.info"
        if not info.exists():
            summary[dut] = {
                "status": "missing",
                "line_coverage": 0.0,
                "branch_coverage": 0.0,
                "top_uncovered": [],
            }
            continue
        parsed = parse_lcov(info)
        parsed["status"] = "ok"
        summary[dut] = parsed

    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md_lines = [
        "# Baseline Coverage Summary",
        "",
        "| DUT | Status | Line % | Branch % |",
        "|-----|--------|--------|----------|",
    ]

    for dut in DUTS:
        row = summary[dut]
        md_lines.append(
            f"| {dut} | {row['status']} | {row['line_coverage']:.2f} | {row['branch_coverage']:.2f} |"
        )

    md_lines.append("")
    md_lines.append("## Top Uncovered Regions (per DUT)")

    for dut in DUTS:
        row = summary[dut]
        md_lines.append("")
        md_lines.append(f"### {dut}")
        if row["status"] != "ok" or not row["top_uncovered"]:
            md_lines.append("- No coverage info available.")
            continue
        top_uncovered = cast(list[dict[str, Any]], row["top_uncovered"])
        for item in top_uncovered[:5]:
            ranges_list = cast(list[str], item["ranges"])
            ranges = ", ".join(ranges_list) if ranges_list else "n/a"
            md_lines.append(
                f"- {item['file']} | uncovered={item['uncovered_lines']} | ranges={ranges}"
            )

    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
