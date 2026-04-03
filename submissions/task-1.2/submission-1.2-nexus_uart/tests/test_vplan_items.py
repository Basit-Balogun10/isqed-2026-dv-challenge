"""
Task 1.2: Verification Plan Tests for NEXUS_UART

This file contains 20 test functions,
one per verification plan item.

Each test is derived from the vplan YAML and implements:
1. Register configuration
2. Stimulus application
3. Expected behavior checks
4. Coverage bin hitting
"""

import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge

# ============================================================================
# TEST FUNCTIONS - One per vplan item
# ============================================================================

@cocotb.test()
async def test_vp_uart_001(dut):
    """
    Basic TX single byte
    
    Verification Plan Item: VP-UART-001
    Priority: high
    Coverage Target: cp_tx_data cross cp_baud_div.mid
    
    Description:
    Enable TX path, write one byte to TXDATA, and verify correct serial frame on uart_tx_o including start bit, 8 data bits LSB-first, and stop bit at the configured baud rate.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-001")
    
    # TODO: Implement stimulus and checks for VP-UART-001
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-001: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_002(dut):
    """
    Basic RX single byte
    
    Verification Plan Item: VP-UART-002
    Priority: high
    Coverage Target: cp_rx_data cross cp_baud_div.mid
    
    Description:
    Enable RX path, drive a valid serial frame on uart_rx_i, and verify the byte appears in RXDATA with correct value. Confirm STATUS.rx_fifo_empty deasserts.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-002")
    
    # TODO: Implement stimulus and checks for VP-UART-002
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-002: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_003(dut):
    """
    Baud rate low divisor
    
    Verification Plan Item: VP-UART-003
    Priority: high
    Coverage Target: cp_baud_div.low
    
    Description:
    Configure baud_divisor to a low value (e.g. 1-3), perform TX and RX transfers, and verify correct bit timing. Checks edge-case divisor behavior.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-003")
    
    # TODO: Implement stimulus and checks for VP-UART-003
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-003: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_004(dut):
    """
    Baud rate mid divisor
    
    Verification Plan Item: VP-UART-004
    Priority: medium
    Coverage Target: cp_baud_div.mid
    
    Description:
    Configure baud_divisor to a mid-range value (e.g. 100-500), perform TX and RX transfers, and verify correct bit timing matches expected baud rate.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-004")
    
    # TODO: Implement stimulus and checks for VP-UART-004
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-004: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_005(dut):
    """
    Baud rate high divisor
    
    Verification Plan Item: VP-UART-005
    Priority: high
    Coverage Target: cp_baud_div.high cross cp_data_val
    
    Description:
    Configure baud_divisor to a high value (e.g. 10000+), perform TX and RX transfers, and verify correct bit timing. Stresses 16x oversampling at slow baud rates.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-005")
    
    # TODO: Implement stimulus and checks for VP-UART-005
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-005: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_006(dut):
    """
    Even parity mode
    
    Verification Plan Item: VP-UART-006
    Priority: high
    Coverage Target: cp_parity_mode.even cross cp_data_val
    
    Description:
    Set parity_mode to 01 (even), transmit and receive bytes with known data patterns, and verify the parity bit is the XOR reduction of the 8 data bits.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-006")
    
    # TODO: Implement stimulus and checks for VP-UART-006
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-006: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_007(dut):
    """
    Odd parity mode
    
    Verification Plan Item: VP-UART-007
    Priority: high
    Coverage Target: cp_parity_mode.odd cross cp_data_val
    
    Description:
    Set parity_mode to 10 (odd), transmit and receive bytes, and verify the parity bit is the complement of the even parity value.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-007")
    
    # TODO: Implement stimulus and checks for VP-UART-007
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-007: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_008(dut):
    """
    RX FIFO full and overflow
    
    Verification Plan Item: VP-UART-008
    Priority: high
    Coverage Target: cp_rx_fifo_level.full, cp_rx_overflow
    
    Description:
    Fill the 32-byte RX FIFO completely by sending 32 bytes without reading RXDATA. Send one more byte and verify STATUS.rx_fifo_full asserts, STATUS.rx_overrun sets, and the rx_overflow interrupt fires.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-008")
    
    # TODO: Implement stimulus and checks for VP-UART-008
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-008: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_009(dut):
    """
    TX FIFO empty interrupt
    
    Verification Plan Item: VP-UART-009
    Priority: medium
    Coverage Target: cp_intr.tx_empty
    
    Description:
    Enable tx_empty interrupt, write one byte to TXDATA, wait for transmission to complete, and verify the tx_empty interrupt fires when the TX FIFO drains.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-009")
    
    # TODO: Implement stimulus and checks for VP-UART-009
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-009: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_010(dut):
    """
    TX and RX watermark interrupts
    
    Verification Plan Item: VP-UART-010
    Priority: high
    Coverage Target: cp_tx_watermark cross cp_rx_watermark
    
    Description:
    Program tx_watermark and rx_watermark levels in FIFO_CTRL. Fill/drain FIFOs past the watermark thresholds and verify the corresponding watermark interrupts fire at the correct FIFO levels.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-010")
    
    # TODO: Implement stimulus and checks for VP-UART-010
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-010: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_011(dut):
    """
    RX parity error injection
    
    Verification Plan Item: VP-UART-011
    Priority: high
    Coverage Target: cp_intr.rx_parity_err, cp_parity_mode.even
    
    Description:
    Enable even parity, drive an RX frame with intentionally wrong parity bit, and verify STATUS.rx_parity_err sets (sticky) and the rx_parity_err interrupt fires.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-011")
    
    # TODO: Implement stimulus and checks for VP-UART-011
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-011: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_012(dut):
    """
    RX framing error injection
    
    Verification Plan Item: VP-UART-012
    Priority: high
    Coverage Target: cp_intr.rx_frame_err
    
    Description:
    Drive an RX frame with a low stop bit (framing error), and verify STATUS.rx_frame_err sets and the rx_frame_err interrupt fires.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-012")
    
    # TODO: Implement stimulus and checks for VP-UART-012
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-012: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_013(dut):
    """
    RX break condition
    
    Verification Plan Item: VP-UART-013
    Priority: medium
    Coverage Target: cp_intr.rx_frame_err
    
    Description:
    Drive uart_rx_i low for an extended period (break condition) and verify the controller detects the framing error and recovers to IDLE after the break is released.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-013")
    
    # TODO: Implement stimulus and checks for VP-UART-013
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-013: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_014(dut):
    """
    Loopback mode basic
    
    Verification Plan Item: VP-UART-014
    Priority: high
    Coverage Target: cp_loopback cross cp_data_val
    
    Description:
    Enable loopback_en with both TX and RX paths enabled. Write a byte to TXDATA and verify it appears in RXDATA via the internal loopback path. Confirm uart_rx_i is ignored.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-014")
    
    # TODO: Implement stimulus and checks for VP-UART-014
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-014: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_015(dut):
    """
    RX timeout interrupt
    
    Verification Plan Item: VP-UART-015
    Priority: high
    Coverage Target: cp_intr.rx_timeout
    
    Description:
    Receive one byte, then leave the RX line idle. Verify the rx_timeout interrupt fires after the idle timeout period. Clear the interrupt and verify it does not re-fire while the line remains idle.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-015")
    
    # TODO: Implement stimulus and checks for VP-UART-015
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-015: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_016(dut):
    """
    Back-to-back TX transfers
    
    Verification Plan Item: VP-UART-016
    Priority: medium
    Coverage Target: cp_tx_fifo_level cross cp_baud_div
    
    Description:
    Fill the TX FIFO with multiple bytes and verify frames are transmitted back-to-back with minimal inter-frame gap. Check timing between stop bit of one frame and start bit of the next.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-016")
    
    # TODO: Implement stimulus and checks for VP-UART-016
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-016: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_017(dut):
    """
    Two stop bits configuration
    
    Verification Plan Item: VP-UART-017
    Priority: medium
    Coverage Target: cp_stop_bits.two
    
    Description:
    Set stop_bits to 1 (2 stop bits), transmit a byte, and verify the TX output holds high for two bit periods after the data (and parity, if enabled). Receive a frame with 2 stop bits and verify acceptance.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-017")
    
    # TODO: Implement stimulus and checks for VP-UART-017
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-017: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_018(dut):
    """
    FIFO reset functionality
    
    Verification Plan Item: VP-UART-018
    Priority: medium
    Coverage Target: cp_fifo_rst
    
    Description:
    Fill both TX and RX FIFOs with data, then assert tx_fifo_rst and rx_fifo_rst in FIFO_CTRL. Verify both FIFOs are flushed (levels go to 0, empty flags assert) and the reset bits self-clear.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-018")
    
    # TODO: Implement stimulus and checks for VP-UART-018
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-018: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_019(dut):
    """
    All interrupt sources via INTR_TEST
    
    Verification Plan Item: VP-UART-019
    Priority: medium
    Coverage Target: cp_intr_test cross cp_intr_enable
    
    Description:
    For each of the 7 interrupt sources, write the corresponding bit in INTR_TEST and verify INTR_STATE sets. Enable the interrupt in INTR_ENABLE and verify intr_o asserts. Clear via W1C and verify deassertion.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-019")
    
    # TODO: Implement stimulus and checks for VP-UART-019
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-019: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_uart_020(dut):
    """
    Loopback with parity interaction
    
    Verification Plan Item: VP-UART-020
    Priority: high
    Coverage Target: cp_loopback cross cp_parity_mode cross cp_data_val
    
    Description:
    Enable loopback mode with parity (even and odd). Transmit bytes with various data patterns and verify the parity bit is correctly generated, transmitted, and checked on the loopback receive path.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-UART-020")
    
    # TODO: Implement stimulus and checks for VP-UART-020
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-UART-020: PLACEHOLDER - implement stimulus and checks")


