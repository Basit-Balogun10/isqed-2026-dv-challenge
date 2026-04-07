"""Functional coverage model for Task 2.2 HMAC tests."""

from __future__ import annotations

import atexit
import os
from typing import Optional

from cocotb_coverage.coverage import CoverPoint, coverage_db

_POINT_NAMES = [
    "hmac.func.cfg_sha_enabled",
    "hmac.func.cfg_hmac_disabled",
    "hmac.func.intr_write_kind",
    "hmac.func.msg_len_nonzero",
    "hmac.func.msg_len_bucket",
]

_DEFAULT_REPORT_PATH = "results/functional_coverage_runtime.txt"


@CoverPoint("hmac.func.cfg_sha_enabled", xf=lambda sha_en: 1 if sha_en else 0, bins=[1])
def _cover_cfg_sha_enabled(sha_en: bool) -> None:
    pass


@CoverPoint(
    "hmac.func.cfg_hmac_disabled", xf=lambda hmac_en: 1 if hmac_en else 0, bins=[0]
)
def _cover_cfg_hmac_disabled(hmac_en: bool) -> None:
    pass


@CoverPoint(
    "hmac.func.intr_write_kind",
    xf=lambda kind: str(kind),
    bins=["enable", "test"],
)
def _cover_intr_write_kind(kind: str) -> None:
    pass


@CoverPoint(
    "hmac.func.msg_len_nonzero",
    xf=lambda msg_len: 1 if int(msg_len) > 0 else 0,
    bins=[1],
)
def _cover_msg_len_nonzero(msg_len: int) -> None:
    pass


@CoverPoint(
    "hmac.func.msg_len_bucket",
    xf=lambda msg_len: "short" if int(msg_len) <= 16 else "long",
    bins=["short"],
)
def _cover_msg_len_bucket(msg_len: int) -> None:
    pass


def sample_config(hmac_en: int, sha_en: int) -> None:
    """Sample HMAC/SHA configuration intent."""
    _cover_cfg_sha_enabled(bool(sha_en))
    _cover_cfg_hmac_disabled(bool(hmac_en))


def sample_interrupt_write(kind: str) -> None:
    """Sample interrupt register write intent (enable/test)."""
    _cover_intr_write_kind(kind)


def sample_message_length(msg_len: int) -> None:
    """Sample message-length driven bins."""
    _cover_msg_len_nonzero(msg_len)
    _cover_msg_len_bucket(msg_len)


def get_functional_coverage_percent() -> float:
    """Return aggregated functional coverage percentage for this model."""
    covered = sum(coverage_db[name].coverage for name in _POINT_NAMES)
    total = sum(coverage_db[name].size for name in _POINT_NAMES)
    return 100.0 * covered / total if total else 0.0


def write_functional_coverage_report(report_path: Optional[str] = None) -> float:
    """Write a text report that includes measured functional coverage percentage."""
    out_path = (
        report_path
        if report_path is not None
        else (os.getenv("FUNC_COV_OUT") or _DEFAULT_REPORT_PATH)
    )
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
