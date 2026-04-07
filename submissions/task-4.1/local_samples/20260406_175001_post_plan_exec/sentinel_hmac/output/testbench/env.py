from __future__ import annotations

from typing import Any

from agents.protocol_agent import ProtocolAgent
from agents.tl_ul_agent import TlUlDriver, TlUlMonitor
from coverage.coverage import CoverageCollector
from ref_model.reference_model import ReferenceModel
from scoreboard.scoreboard import Scoreboard


class VerificationEnv:
    """Top-level environment wiring agent, model, scoreboard, and coverage."""

    def __init__(self, dut: Any) -> None:
        self.dut = dut
        self.tl_driver = TlUlDriver(dut, clk_signal="clk_i", rst_signal="rst_ni")
        self.tl_monitor = TlUlMonitor(dut)
        self.protocol_agent = ProtocolAgent(dut, protocol="hmac")
        self.ref_model = ReferenceModel()
        self.scoreboard = Scoreboard()
        self.coverage = CoverageCollector()
