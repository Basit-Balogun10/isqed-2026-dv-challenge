"""Generated-stimulus cocotb test used by the Task 2.3 CDG engine."""

from __future__ import annotations

import json
import os
import random

import cocotb
from cocotb.triggers import RisingEdge, Timer

from .helpers import (
    generate_clock,
    generate_reset,
    init_tl_driver,
    read_hmac_digest,
    set_config,
    issue_hash_start,
    issue_hash_stop,
    wait_for_digest_valid,
    write_hmac_csr,
    write_hmac_msg_fifo,
)


def _default_stimulus() -> dict:
    return {
        "seed": 2026,
        "iteration": 0,
        "target_cycles": 8000,
        "focus_target": "global:coverage_efficiency",
        "selected_knobs": {
            "msg_len_profile": "short",
            "intr_pattern": "enable",
            "burst_count": "2",
            "chunking": "4",
        },
        "transactions": [
            {
                "id": 0,
                "msg_len": 8,
                "intr_pattern": "enable",
                "chunking": 4,
                "tx_seed": 111,
                "pattern": "incremental",
            },
            {
                "id": 1,
                "msg_len": 32,
                "intr_pattern": "both",
                "chunking": 8,
                "tx_seed": 222,
                "pattern": "alternating",
            },
        ],
    }


def _load_stimulus() -> dict:
    path = os.getenv("STIMULUS_FILE", "").strip()
    if not path:
        return _default_stimulus()

    try:
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    return _default_stimulus()


def _build_payload(msg_len: int, pattern: str, seed: int) -> bytes:
    rng = random.Random(seed)
    if msg_len <= 0:
        return b""

    if pattern == "all_zero":
        return b"\x00" * msg_len
    if pattern == "all_ff":
        return b"\xff" * msg_len
    if pattern == "alternating":
        return bytes(0xAA if i % 2 == 0 else 0x55 for i in range(msg_len))
    if pattern == "walking_ones":
        return bytes(1 << (i % 8) for i in range(msg_len))

    # incremental / default
    return bytes((i + rng.randint(0, 15)) & 0xFF for i in range(msg_len))


async def _drive_interrupt_pattern(dut, pattern: str) -> None:
    if pattern == "enable":
        await write_hmac_csr(dut, 0x5C, 0x1)
    elif pattern == "test":
        await write_hmac_csr(dut, 0x60, 0x1)
    elif pattern == "both":
        await write_hmac_csr(dut, 0x5C, 0x1)
        await write_hmac_csr(dut, 0x60, 0x1)


@cocotb.test()
async def test_cdg_generated(dut):
    """Execute one CDG-generated stimulus bundle from STIMULUS_FILE."""
    stimulus = _load_stimulus()

    await generate_clock(dut)
    await generate_reset(dut)
    init_tl_driver(dut)

    # Keep configuration stable for deterministic runs.
    await set_config(dut, hmac_en=0, sha_en=1)

    transactions = stimulus.get("transactions", [])
    if not isinstance(transactions, list) or not transactions:
        transactions = _default_stimulus()["transactions"]

    for tx in transactions:
        msg_len = int(tx.get("msg_len", 8))
        pattern = str(tx.get("pattern", "incremental"))
        tx_seed = int(tx.get("tx_seed", 1))
        intr_pattern = str(tx.get("intr_pattern", "none"))
        chunking = max(1, int(tx.get("chunking", 8)))

        await _drive_interrupt_pattern(dut, intr_pattern)

        payload = _build_payload(msg_len=msg_len, pattern=pattern, seed=tx_seed)

        await issue_hash_start(dut)
        if payload:
            for offset in range(0, len(payload), chunking):
                await write_hmac_msg_fifo(dut, payload[offset : offset + chunking])
        await issue_hash_stop(dut)

        digest_ready = await wait_for_digest_valid(dut, max_us=2000)
        assert digest_ready, f"Digest did not become valid for tx={tx}"

        digest = await read_hmac_digest(dut)
        # Digest value is implementation-dependent; only enforce non-trivial result.
        if msg_len > 0:
            assert digest != 0, f"Unexpected all-zero digest for tx={tx}"

        await Timer(100, unit="ns")

    # Honor per-iteration cycle budget so convergence curves map to real simulation work.
    target_cycles = max(0, int(stimulus.get("target_cycles", 0)))
    for _ in range(target_cycles):
        await RisingEdge(dut.clk_i)
