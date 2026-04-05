"""Functional coverage model for Task 2.2 I2C tests."""

from __future__ import annotations

import atexit
import os
from typing import Optional

from cocotb_coverage.coverage import CoverPoint, coverage_db

_POINT_NAMES = [
    "i2c.func.ctrl_mode",
    "i2c.func.fmt_op",
    "i2c.func.timing_reg",
    "i2c.func.fifo_ctrl_reset",
    "i2c.func.status_host_idle",
    "i2c.func.status_bus_idle",
]

_DEFAULT_REPORT_PATH = "results/functional_coverage_runtime.txt"


@CoverPoint("i2c.func.ctrl_mode", xf=lambda mode: str(mode), bins=["host", "target"])
def _cover_ctrl_mode(mode: str) -> None:
    pass


@CoverPoint(
    "i2c.func.fmt_op",
    xf=lambda op: str(op),
    bins=["start", "write", "read", "stop"],
)
def _cover_fmt_op(op: str) -> None:
    pass


@CoverPoint(
    "i2c.func.timing_reg",
    xf=lambda addr: int(addr),
    bins=[0x1C, 0x20, 0x24, 0x28, 0x2C],
)
def _cover_timing_reg(addr: int) -> None:
    pass


@CoverPoint(
    "i2c.func.fifo_ctrl_reset",
    xf=lambda value: 1 if (int(value) & 0xF) != 0 else 0,
    bins=[1],
)
def _cover_fifo_ctrl_reset(value: int) -> None:
    pass


@CoverPoint(
    "i2c.func.status_host_idle",
    xf=lambda status: 1 if ((int(status) >> 6) & 0x1) else 0,
    bins=[1],
)
def _cover_status_host_idle(status: int) -> None:
    pass


@CoverPoint(
    "i2c.func.status_bus_idle",
    xf=lambda status: 1 if ((int(status) >> 8) & 0x1) == 0 else 0,
    bins=[1],
)
def _cover_status_bus_idle(status: int) -> None:
    pass


def sample_ctrl_mode(mode: str) -> None:
    """Sample host/target control mode selection."""
    _cover_ctrl_mode(mode)


def sample_fmt_op(op: str) -> None:
    """Sample format FIFO operation intent."""
    _cover_fmt_op(op)


def sample_timing_reg_write(addr: int) -> None:
    """Sample timing-register write addresses."""
    _cover_timing_reg(addr)


def sample_fifo_ctrl(value: int) -> None:
    """Sample FIFO reset-control write intent."""
    _cover_fifo_ctrl_reset(value)


def sample_status(status: int) -> None:
    """Sample selected status bits from STATUS CSR."""
    _cover_status_host_idle(status)
    _cover_status_bus_idle(status)


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
