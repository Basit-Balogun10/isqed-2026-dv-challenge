import cocotb
from cocotb.triggers import RisingEdge, ReadOnly, NextTimeStep


class TlUlDriver:
    """TileLink-UL bus driver for cocotb testbenches.

    Drives flat TL-UL signals (not packed structs) for maximum simulator
    compatibility. Works with Icarus Verilog, Verilator, VCS, Questa, Xcelium.
    """

    def __init__(self, dut, clk_signal="clk_i"):
        self.dut = dut
        self.clk = getattr(dut, clk_signal)

    async def reset(self, rst_signal="rst_ni", cycles=5):
        rst = getattr(self.dut, rst_signal)
        rst.value = 0
        for _ in range(cycles):
            await RisingEdge(self.clk)
        rst.value = 1
        await RisingEdge(self.clk)

    async def write_reg(self, addr, data, mask=0xF, source=0):
        """Write a 32-bit value to a CSR address via TL-UL PutFullData."""
        self.dut.tl_a_valid_i.value = 1
        self.dut.tl_a_opcode_i.value = 0  # PutFullData
        self.dut.tl_a_address_i.value = addr
        self.dut.tl_a_data_i.value = data
        self.dut.tl_a_mask_i.value = mask
        self.dut.tl_a_source_i.value = source
        self.dut.tl_a_size_i.value = 2  # 4 bytes
        self.dut.tl_d_ready_i.value = 1

        accepted = False
        d_seen = False
        for _ in range(100):
            await RisingEdge(self.clk)
            await ReadOnly()
            if int(self.dut.tl_a_ready_o.value) == 1:
                accepted = True
            if int(self.dut.tl_d_valid_o.value) == 1:
                d_seen = True
            if accepted and d_seen:
                break

        if not accepted:
            raise RuntimeError("TL-UL write request not accepted")

        # Drop A-channel request without waiting for another clock edge
        # to avoid re-issuing the same request on the next cycle.
        await NextTimeStep()
        self.dut.tl_a_valid_i.value = 0
        self.dut.tl_a_opcode_i.value = 0
        self.dut.tl_a_address_i.value = 0
        self.dut.tl_a_data_i.value = 0

        if not d_seen:
            for _ in range(100):
                await RisingEdge(self.clk)
                await ReadOnly()
                if int(self.dut.tl_d_valid_o.value) == 1:
                    d_seen = True
                    break
            if not d_seen:
                raise RuntimeError("TL-UL write response not observed")

        await NextTimeStep()
        self.dut.tl_d_ready_i.value = 0

    async def read_reg(self, addr, source=0):
        """Read a 32-bit value from a CSR address via TL-UL Get."""
        self.dut.tl_a_valid_i.value = 1
        self.dut.tl_a_opcode_i.value = 4  # Get
        self.dut.tl_a_address_i.value = addr
        self.dut.tl_a_data_i.value = 0
        self.dut.tl_a_mask_i.value = 0xF
        self.dut.tl_a_source_i.value = source
        self.dut.tl_a_size_i.value = 2  # 4 bytes
        self.dut.tl_d_ready_i.value = 1

        accepted = False
        data = None
        for _ in range(100):
            await RisingEdge(self.clk)
            await ReadOnly()
            if int(self.dut.tl_a_ready_o.value) == 1:
                accepted = True
            if int(self.dut.tl_d_valid_o.value) == 1:
                data = int(self.dut.tl_d_data_o.value)
            if accepted and data is not None:
                break

        if not accepted:
            raise RuntimeError("TL-UL read request not accepted")

        # Drop A-channel request without waiting for another clock edge
        # to avoid re-issuing the same request on the next cycle.
        await NextTimeStep()
        self.dut.tl_a_valid_i.value = 0
        self.dut.tl_a_opcode_i.value = 0
        self.dut.tl_a_address_i.value = 0

        if data is None:
            for _ in range(100):
                await RisingEdge(self.clk)
                await ReadOnly()
                if int(self.dut.tl_d_valid_o.value) == 1:
                    data = int(self.dut.tl_d_data_o.value)
                    break
            if data is None:
                raise RuntimeError("TL-UL read response not observed")

        await NextTimeStep()
        self.dut.tl_d_ready_i.value = 0
        return data

    def idle_a_channel(self):
        """Set all A-channel signals to idle state."""
        self.dut.tl_a_valid_i.value = 0
        self.dut.tl_a_opcode_i.value = 0
        self.dut.tl_a_address_i.value = 0
        self.dut.tl_a_data_i.value = 0
        self.dut.tl_a_mask_i.value = 0
        self.dut.tl_a_source_i.value = 0
        self.dut.tl_a_size_i.value = 0
        self.dut.tl_d_ready_i.value = 0
