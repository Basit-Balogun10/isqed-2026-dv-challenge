"""Functional coverage model for Task 2.2 warden_timer tests."""

from __future__ import annotations

import atexit
import os
from typing import Optional

from cocotb_coverage.coverage import CoverPoint, coverage_db

_POINT_NAMES = [
    "timer.func.wd_ctrl_mode",
    "timer.func.bark_thresh_nonzero",
    "timer.func.bite_thresh_nonzero",
    "timer.func.pet_seen",
    "timer.func.timer_irq_source",
    "timer.func.intr_enable_written",
    "timer.func.prescaler_nonzero",
    "timer.func.compare_programmed",
]

_DEFAULT_REPORT_PATH = "results/functional_coverage_runtime.txt"


@CoverPoint(
    "timer.func.wd_ctrl_mode",
    xf=lambda mode: str(mode),
    bins=["disabled", "enabled", "enabled_locked"],
)
def _cover_wd_ctrl_mode(mode: str) -> None:
    pass


@CoverPoint(
    "timer.func.bark_thresh_nonzero",
    xf=lambda value: 1 if int(value) > 0 else 0,
    bins=[1],
)
def _cover_bark_thresh_nonzero(value: int) -> None:
    pass


@CoverPoint(
    "timer.func.bite_thresh_nonzero",
    xf=lambda value: 1 if int(value) > 0 else 0,
    bins=[1],
)
def _cover_bite_thresh_nonzero(value: int) -> None:
    pass


@CoverPoint("timer.func.pet_seen", xf=lambda pet: 1 if pet else 0, bins=[1])
def _cover_pet_seen(pet: bool) -> None:
    pass


@CoverPoint(
    "timer.func.timer_irq_source",
    xf=lambda source: str(source),
    bins=["timer0", "timer1", "intr_test", "wd_bark"],
)
def _cover_timer_irq_source(source: str) -> None:
    pass


@CoverPoint(
    "timer.func.intr_enable_written",
    xf=lambda value: 1 if (int(value) & 0x7) != 0 else 0,
    bins=[1],
)
def _cover_intr_enable_written(value: int) -> None:
    pass


@CoverPoint(
    "timer.func.prescaler_nonzero",
    xf=lambda value: 1 if int(value) > 0 else 0,
    bins=[1],
)
def _cover_prescaler_nonzero(value: int) -> None:
    pass


@CoverPoint(
    "timer.func.compare_programmed",
    xf=lambda cmp_id: str(cmp_id),
    bins=["cmp0", "cmp1"],
)
def _cover_compare_programmed(cmp_id: str) -> None:
    pass


def sample_wd_ctrl_value(ctrl_value: int) -> None:
    """Sample watchdog control mode."""
    en = bool(ctrl_value & 0x1)
    lock = bool(ctrl_value & 0x2)
    if en and lock:
        _cover_wd_ctrl_mode("enabled_locked")
    elif en:
        _cover_wd_ctrl_mode("enabled")
    else:
        _cover_wd_ctrl_mode("disabled")


def sample_bark_threshold(value: int) -> None:
    """Sample watchdog bark threshold write/read value."""
    _cover_bark_thresh_nonzero(value)


def sample_bite_threshold(value: int) -> None:
    """Sample watchdog bite threshold write/read value."""
    _cover_bite_thresh_nonzero(value)


def sample_pet_event() -> None:
    """Sample watchdog pet write path."""
    _cover_pet_seen(True)


def sample_timer_irq_source(source: str) -> None:
    """Sample which timer/interrupt source path was stimulated."""
    _cover_timer_irq_source(source)


def sample_intr_enable(value: int) -> None:
    """Sample interrupt-enable writes."""
    _cover_intr_enable_written(value)


def sample_prescaler(value: int) -> None:
    """Sample prescaler programming path."""
    _cover_prescaler_nonzero(value)


def sample_compare_programming(cmp_id: str) -> None:
    """Sample comparator programming path."""
    _cover_compare_programmed(cmp_id)


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
