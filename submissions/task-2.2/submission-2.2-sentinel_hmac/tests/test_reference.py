"""Reference baseline smoke test for Task 2.2 HMAC submission."""

import cocotb

from .helpers import (
    generate_clock,
    generate_reset,
    init_tl_driver,
    read_hmac_csr,
    set_config,
)


@cocotb.test()
async def test_reference(dut):
    """Task 2.2 reference test: reset and config baseline behavior."""
    await generate_clock(dut)
    await generate_reset(dut)
    init_tl_driver(dut)

    status = await read_hmac_csr(dut, 0x08)
    fifo_empty = (status >> 1) & 0x1
    sha_idle = (status >> 8) & 0x1
    assert fifo_empty == 1, f"FIFO must be empty after reset, STATUS={status:#010x}"
    assert sha_idle == 1, f"SHA must be idle after reset, STATUS={status:#010x}"

    await set_config(dut, hmac_en=0, sha_en=1)
    cfg = await read_hmac_csr(dut, 0x00)
    assert (cfg & 0x2) == 0x2, f"SHA enable bit must be set, CFG={cfg:#010x}"
