"""Functional coverage model for Task 2.2 AES tests."""

from __future__ import annotations

import atexit
import os
from typing import Optional

from cocotb_coverage.coverage import CoverPoint, coverage_db

_POINT_NAMES = [
    "aes.func.ctrl_mode",
    "aes.func.start_seen",
    "aes.func.status_idle",
    "aes.func.status_input_ready",
]

_DEFAULT_REPORT_PATH = "results/functional_coverage_runtime.txt"


@CoverPoint("aes.func.ctrl_mode", xf=lambda mode: int(mode) & 0x3, bins=[0, 1, 2, 3])
def _cover_ctrl_mode(mode: int) -> None:
    pass


@CoverPoint("aes.func.start_seen", xf=lambda started: 1 if started else 0, bins=[1])
def _cover_start(started: bool) -> None:
    pass


@CoverPoint("aes.func.status_idle", xf=lambda idle: 1 if idle else 0, bins=[1])
def _cover_status_idle(idle: bool) -> None:
    pass


@CoverPoint(
    "aes.func.status_input_ready",
    xf=lambda input_ready: 1 if input_ready else 0,
    bins=[1],
)
def _cover_status_input_ready(input_ready: bool) -> None:
    pass


def sample_ctrl_mode(mode: int) -> None:
    """Sample AES control mode (ECB/CBC x ENC/DEC)."""
    _cover_ctrl_mode(mode)


def sample_start_event() -> None:
    """Sample AES operation start pulse event."""
    _cover_start(True)


def sample_status(status: int) -> None:
    """Sample selected status bits used for readiness checks."""
    _cover_status_idle((status & 0x1) != 0)
    _cover_status_input_ready(((status >> 2) & 0x1) != 0)


def get_functional_coverage_percent() -> float:
    """Return aggregated functional coverage percentage for this model."""
    covered = sum(coverage_db[name].coverage for name in _POINT_NAMES)
    total = sum(coverage_db[name].size for name in _POINT_NAMES)
    return 100.0 * covered / total if total else 0.0


def write_functional_coverage_report(report_path: Optional[str] = None) -> float:
    """Write a text report that includes measured functional coverage percentage."""
    out_path = report_path if report_path is not None else (os.getenv("FUNC_COV_OUT") or _DEFAULT_REPORT_PATH)
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    covered = sum(coverage_db[name].coverage for name in _POINT_NAMES)
    total = sum(coverage_db[name].size for name in _POINT_NAMES)
    percent = 100.0 * covered / total if total else 0.0

    with open(out_path, "w", encoding="utf-8") as fp:
        fp.write(f"functional_coverage: {percent:.2f}\n")
        fp.write(f"covered_bins: {covered}/{total}\n")
        for name in _POINT_NAMES:
            item = coverage_db[name]
            fp.write(f"{name}: {item.coverage}/{item.size}\n")

    return percent


def _write_report_on_exit() -> None:
    try:
        write_functional_coverage_report()
    except Exception:
        # Best effort only; tests must not fail due to report I/O.
        pass


atexit.register(_write_report_on_exit)
