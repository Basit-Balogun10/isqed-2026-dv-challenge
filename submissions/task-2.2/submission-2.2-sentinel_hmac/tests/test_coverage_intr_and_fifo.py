"""Coverage-closing interrupt/FIFO test for Task 2.2 HMAC."""

import cocotb
from cocotb.triggers import Timer

from .helpers import (
    generate_clock,
    generate_reset,
    init_tl_driver,
    write_hmac_csr,
    read_hmac_csr,
    write_hmac_msg_fifo,
)


@cocotb.test()
async def test_coverage_intr_and_fifo(dut):
    """Task 2.2 coverage test: drive interrupt and message-length control paths."""
    await generate_clock(dut)
    await generate_reset(dut)
    init_tl_driver(dut)

    await write_hmac_csr(dut, 0x5C, 0x1)  # INTR_ENABLE.hmac_done
    await write_hmac_csr(dut, 0x60, 0x1)  # INTR_TEST.hmac_done
    intr_state = await read_hmac_csr(dut, 0x58)
    assert (
        intr_state & 0x1
    ) == 0x1, f"Expected interrupt bit to set, INTR_STATE={intr_state:#010x}"

    # Exercise MSG_FIFO write path and message length accounting.
    await write_hmac_msg_fifo(dut, b"task22")
    await Timer(200, unit="ns")
    msg_len = await read_hmac_csr(dut, 0x50)
    assert (
        msg_len > 0
    ), f"Message length must increase after FIFO writes, MSG_LENGTH_LOWER={msg_len:#010x}"
