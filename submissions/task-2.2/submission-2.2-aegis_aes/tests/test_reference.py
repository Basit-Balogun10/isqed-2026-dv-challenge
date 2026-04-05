"""Reference baseline smoke test for Task 2.2 AES submission."""

import cocotb

from .helpers import generate_clock, generate_reset, init_tl_driver, read_aes_csr


@cocotb.test()
async def test_reference(dut):
    """Task 2.2 reference test: confirm reset/idle baseline behavior."""
    await generate_clock(dut)
    await generate_reset(dut)
    init_tl_driver(dut)

    status = await read_aes_csr(dut, 0x48)
    idle = status & 0x1
    input_ready = (status >> 2) & 0x1

    assert idle == 1, f"AES must be idle after reset, STATUS={status:#010x}"
    assert input_ready == 1, f"AES input must be ready after reset, STATUS={status:#010x}"
