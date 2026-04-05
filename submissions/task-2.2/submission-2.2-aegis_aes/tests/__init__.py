# pyright: reportMissingTypeStubs=false
"""
Cocotb test module discovery — imports all @cocotb.test() functions.

This file makes all test_vp_*.py functions available to cocotb's test discovery.
"""

import atexit
import importlib
import json
import os
from pathlib import Path

import cocotb

yaml = importlib.import_module("yaml")

_SUBMISSION_ROOT = Path(__file__).resolve().parent.parent
_MAPPING_PATH = _SUBMISSION_ROOT / "vplan_mapping.yaml"
_COVERAGE_PATH = Path(
    os.environ.get(
        "TASK12_RUNTIME_COVERAGE_FILE",
        str(_SUBMISSION_ROOT / "sim_build" / "task12_runtime_coverage.json"),
    )
)

_TEST_TO_BINS: dict[str, set[str]] = {}
_CLAIMED_BINS: set[str] = set()
_SEEN_TESTS: set[str] = set()
_PASSED_TESTS: set[str] = set()
_FAILED_TESTS: set[str] = set()
_HIT_BINS: set[str] = set()
_RUNTIME_ERRORS: list[str] = []


def _flatten_bins(raw):
    out = set()

    def walk(node):
        if node is None:
            return
        if isinstance(node, dict):
            for key, value in node.items():
                out.add(str(key))
                walk(value)
            return
        if isinstance(node, (list, tuple, set)):
            for value in node:
                walk(value)
            return
        out.add(str(node))

    walk(raw)
    return out


def _mapping_keys(test_name):
    if "::" not in test_name:
        return set()
    module_name, func_name = test_name.split("::", 1)
    module_leaf = module_name.split(".")[-1]
    module_variants = {
        module_name,
        module_leaf,
        f"tests.{module_name}",
        f"tests.{module_leaf}",
    }
    return {f"{module}::{func_name}" for module in module_variants}


def _runtime_keys(func):
    module_name = func.__module__
    module_leaf = module_name.split(".")[-1]
    if module_name.startswith("tests."):
        module_noprefix = module_name[len("tests.") :]
    else:
        module_noprefix = module_name
    module_variants = {
        module_name,
        module_leaf,
        module_noprefix,
        f"tests.{module_noprefix}",
        f"tests.{module_leaf}",
    }
    return {f"{module}::{func.__name__}" for module in module_variants}


def _load_mapping():
    if not _MAPPING_PATH.is_file():
        _RUNTIME_ERRORS.append(f"mapping file missing: {_MAPPING_PATH}")
        return

    try:
        data = yaml.safe_load(_MAPPING_PATH.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        _RUNTIME_ERRORS.append(f"failed to parse mapping file: {exc}")
        return

    mappings = data.get("mappings", []) if isinstance(data, dict) else []
    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue
        test_name = str(mapping.get("test_name", "")).strip()
        bins = _flatten_bins(mapping.get("coverage_bins", []))
        _CLAIMED_BINS.update(bins)
        for key in _mapping_keys(test_name):
            if key not in _TEST_TO_BINS:
                _TEST_TO_BINS[key] = set()
            _TEST_TO_BINS[key].update(bins)


def _write_runtime():
    payload = {
        "coverage_file_version": 1,
        "mapping_file": str(_MAPPING_PATH),
        "coverage_file": str(_COVERAGE_PATH),
        "claimed_bins": sorted(_CLAIMED_BINS),
        "hit_bins": sorted(_HIT_BINS),
        "seen_tests": sorted(_SEEN_TESTS),
        "passed_tests": sorted(_PASSED_TESTS),
        "failed_tests": sorted(_FAILED_TESTS),
        "runtime_errors": list(_RUNTIME_ERRORS),
    }
    _COVERAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _COVERAGE_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )


def _make_coverage_decorator(original_test):
    def _coverage_test(*test_args, **test_kwargs):
        if (
            test_args
            and callable(test_args[0])
            and len(test_args) == 1
            and not test_kwargs
        ):
            return _coverage_test()(test_args[0])

        cocotb_decorator = original_test(*test_args, **test_kwargs)

        def _decorate(func):
            candidate_keys = _runtime_keys(func)
            bins_for_func = set()
            for key in candidate_keys:
                bins_for_func.update(_TEST_TO_BINS.get(key, set()))
            canonical_key = sorted(candidate_keys)[0]

            async def _wrapped(*args, **kwargs):
                _SEEN_TESTS.add(canonical_key)
                try:
                    result = await func(*args, **kwargs)
                except Exception:
                    _FAILED_TESTS.add(canonical_key)
                    _write_runtime()
                    raise
                else:
                    _PASSED_TESTS.add(canonical_key)
                    _HIT_BINS.update(bins_for_func)
                    _write_runtime()
                    return result

            _wrapped.__name__ = func.__name__
            _wrapped.__qualname__ = func.__qualname__
            _wrapped.__module__ = func.__module__
            _wrapped.__doc__ = func.__doc__
            return cocotb_decorator(_wrapped)

        return _decorate

    return _coverage_test


_load_mapping()
atexit.register(_write_runtime)

if not getattr(cocotb, "_task12_runtime_cov_installed", False):
    cocotb.test = _make_coverage_decorator(cocotb.test)
    setattr(cocotb, "_task12_runtime_cov_installed", True)

from .test_vp_001 import test_vp_aes_001
from .test_vp_002 import test_vp_aes_002
from .test_vp_003 import test_vp_aes_003
from .test_vp_004 import test_vp_aes_004
from .test_vp_005 import test_vp_aes_005
from .test_vp_006 import test_vp_aes_006
from .test_vp_007 import test_vp_aes_007
from .test_vp_008 import test_vp_aes_008
from .test_vp_009 import test_vp_aes_009
from .test_vp_010 import test_vp_aes_010
from .test_vp_011 import test_vp_aes_011
from .test_vp_012 import test_vp_aes_012
from .test_vp_013 import test_vp_aes_013
from .test_vp_014 import test_vp_aes_014
from .test_vp_015 import test_vp_aes_015
from .test_vp_016 import test_vp_aes_016
from .test_vp_017 import test_vp_aes_017
from .test_vp_018 import test_vp_aes_018
from .test_vp_019 import test_vp_aes_019
from .test_vp_020 import test_vp_aes_020
