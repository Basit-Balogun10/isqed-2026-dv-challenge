"""Specification-level helper stubs for Task 4.3 test intent."""

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
