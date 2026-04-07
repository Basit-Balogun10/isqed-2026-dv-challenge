"""Coverage-closing AES mode sweep for Task 2.2."""

import cocotb
from cocotb.triggers import Timer

from .helpers import (
    FIPS197_KEY,
    FIPS197_PT,
    generate_clock,
    generate_reset,
    init_tl_driver,
    write_aes_128,
    write_aes_csr,
    read_aes_csr,
)


@cocotb.test()
async def test_coverage_mode_sweep(dut):
    """Task 2.2 coverage test: sweep AES mode/opcode combinations."""
    await generate_clock(dut)
    await generate_reset(dut)
    init_tl_driver(dut)

    await write_aes_128(dut, 0x00, FIPS197_KEY)
    await write_aes_128(dut, 0x20, FIPS197_PT)

    # Exercise control-path mode decode branches: ECB/CBC x ENC/DEC.
    for ctrl_mode in (0x0, 0x1, 0x2, 0x3):
        await write_aes_csr(dut, 0x40, ctrl_mode)
        await write_aes_csr(dut, 0x44, 0x1)
        await Timer(800, unit="ns")

        status = await read_aes_csr(dut, 0x48)
        input_ready = (status >> 2) & 0x1
        assert (
            input_ready == 1
        ), f"Input-ready must recover after mode {ctrl_mode}, STATUS={status:#010x}"
