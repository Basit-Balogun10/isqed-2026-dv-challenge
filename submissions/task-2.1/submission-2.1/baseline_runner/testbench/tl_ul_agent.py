import cocotb
from cocotb.triggers import RisingEdge


class TlUlDriver:
    """Flat-signal TileLink-UL driver for broad simulator compatibility."""

    def __init__(self, dut, clk_signal='clk_i'):
        self.dut = dut
        self.clk = getattr(dut, clk_signal)

    async def reset(self, rst_signal='rst_ni', cycles=5):
        rst = getattr(self.dut, rst_signal)
        rst.value = 0
        for _ in range(cycles):
            await RisingEdge(self.clk)
        rst.value = 1
        await RisingEdge(self.clk)

    async def write_reg(self, addr, data, mask=0xF, source=0):
        self.dut.tl_a_valid_i.value = 1
        self.dut.tl_a_opcode_i.value = 0
        self.dut.tl_a_address_i.value = addr
        self.dut.tl_a_data_i.value = data
        self.dut.tl_a_mask_i.value = mask
        self.dut.tl_a_source_i.value = source
        self.dut.tl_a_size_i.value = 2
        self.dut.tl_d_ready_i.value = 1

        await RisingEdge(self.clk)
        for _ in range(200):
            if int(self.dut.tl_a_ready_o.value) == 1:
                break
            await RisingEdge(self.clk)

        self.dut.tl_a_valid_i.value = 0
        self.dut.tl_a_opcode_i.value = 0
        self.dut.tl_a_address_i.value = 0
        self.dut.tl_a_data_i.value = 0

        for _ in range(200):
            if int(self.dut.tl_d_valid_o.value) == 1:
                break
            await RisingEdge(self.clk)

        await RisingEdge(self.clk)
        self.dut.tl_d_ready_i.value = 0

    async def read_reg(self, addr, source=0):
        self.dut.tl_a_valid_i.value = 1
        self.dut.tl_a_opcode_i.value = 4
        self.dut.tl_a_address_i.value = addr
        self.dut.tl_a_data_i.value = 0
        self.dut.tl_a_mask_i.value = 0xF
        self.dut.tl_a_source_i.value = source
        self.dut.tl_a_size_i.value = 2
        self.dut.tl_d_ready_i.value = 1

        await RisingEdge(self.clk)
        for _ in range(200):
            if int(self.dut.tl_a_ready_o.value) == 1:
                break
            await RisingEdge(self.clk)

        self.dut.tl_a_valid_i.value = 0
        self.dut.tl_a_opcode_i.value = 0
        self.dut.tl_a_address_i.value = 0

        for _ in range(200):
            if int(self.dut.tl_d_valid_o.value) == 1:
                break
            await RisingEdge(self.clk)

        data = int(self.dut.tl_d_data_o.value)
        await RisingEdge(self.clk)
        self.dut.tl_d_ready_i.value = 0
        return data

    def idle_a_channel(self):
        self.dut.tl_a_valid_i.value = 0
        self.dut.tl_a_opcode_i.value = 0
        self.dut.tl_a_address_i.value = 0
        self.dut.tl_a_data_i.value = 0
        self.dut.tl_a_mask_i.value = 0
        self.dut.tl_a_source_i.value = 0
        self.dut.tl_a_size_i.value = 0
        self.dut.tl_d_ready_i.value = 0
