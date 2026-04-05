import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

from testbench.tl_ul_agent import TlUlDriver


def _set_optional_inputs(dut):
    # Keep optional protocol-side inputs at benign defaults so the DUT remains deterministic.
    for signal, value in [
        ('rx_i', 1),
        ('scl_i', 1),
        ('sda_i', 1),
        ('cio_gpio_i', 0),
        ('cs_i', 0),
        ('sck_i', 0),
        ('mosi_i', 0),
        ('alert_rx_i', 0),
    ]:
        if hasattr(dut, signal):
            getattr(dut, signal).value = value


@cocotb.test()
async def test_smoke_baseline(dut):
    """Generic low-stimulus baseline run to create reference-like coverage artifacts."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit='ns').start())

    _set_optional_inputs(dut)

    tl = TlUlDriver(dut)
    tl.idle_a_channel()

    await tl.reset()

    # Broad but shallow register traffic to emulate baseline smoke behavior.
    read_addrs = [0x00, 0x04, 0x08, 0x0C, 0x10, 0x14, 0x18]
    write_pairs = [
        (0x00, 0x0000_0001),
        (0x04, 0x0000_0000),
        (0x08, 0x1234_5678),
        (0x0C, 0x0000_00A5),
    ]

    for addr in read_addrs:
        await tl.read_reg(addr)

    for addr, data in write_pairs:
        await tl.write_reg(addr, data)
        await tl.read_reg(addr)

    for _ in range(80):
        await RisingEdge(dut.clk_i)
