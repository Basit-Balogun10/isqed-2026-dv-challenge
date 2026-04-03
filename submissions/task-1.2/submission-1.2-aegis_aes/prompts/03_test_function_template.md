# Key Prompt 3: Cocotb Test Function Structure

## Prompt (to Copilot)

```
For Task 1.2, what should each cocotb test function look like to satisfy requirements?

Requirements:
- Must use @cocotb.test() decorator
- Must have comprehensive docstring showing:
  - VP-ID it covers
  - Description of what it tests
  - Coverage bins it targets
- Must compile and RUN on clean RTL (no failures allowed, -10pts per failure)
- Placeholder TODOs acceptable (actual stimulus implementation is Phase 2)
- Use cocotb.start_soon() for concurrent tasks, await RisingEdge() for sync

Structure example needed.
```

## Response (Copilot)

```python
@cocotb.test()
async def test_vp_uart_001_basic_tx(dut):
    """
    Test case: VP-UART-001 - Basic TX single byte
    
    Description:
    Enable TX path, write one byte to TXDATA, and verify correct serial 
    frame on uart_tx_o including start bit, 8 data bits LSB-first, and 
    stop bit at the configured baud rate.
    
    Verification Plan Mapping:
    - VP-ID: VP-UART-001
    - Priority: high
    - Coverage: cp_tx_data cross cp_baud_div.mid
    """
    # Setup
    clk = dut.clk_i
    rst_n = dut.rst_ni
    
    # Initial reset
    rst_n.value = 0
    await Timer(100, "ns")
    rst_n.value = 1
    await RisingEdge(clk)
    
    dut._log.info(f"Starting test: VP-UART-001 - Basic TX single byte")
    
    # TODO: Implement stimulus:
    #   1. Configure TX_CTRL register
    #   2. Write 0x42 to TXDATA
    #   3. Monitor uart_tx_o for correct serial frame
    #   4. Hit coverage bins: cp_tx_data, cp_baud_div.mid
    
    # Placeholder: minimal stimulus to ensure test compiles/runs
    await RisingEdge(clk)
    await Timer(10, "us")
    
    dut._log.info(f"✓ Test VP-UART-001 completed successfully")
```

Key points:
- @cocotb.test() enables framework discovery
- Docstring ties test to VP-ID  
- TODO section documents intent (Phase 2 implementation)
- Base structure always runs (won't fail)
- Coverage bins explicitly noted for evaluator
```
