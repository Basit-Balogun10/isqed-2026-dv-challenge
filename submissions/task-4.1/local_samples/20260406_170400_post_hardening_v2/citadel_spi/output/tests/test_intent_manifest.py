# Auto-generated test intent summary
#
# Directed tests:
# - reset_and_csr_smoke: Apply reset, verify all readable CSRs return legal defaults, confirm TL-UL read/write access, and check idle pin states for sclk_o, csn_o, mosi_o, intr_o, and alert_o.
# - spi_mode_matrix_basic: Program CPOL/CPHA across modes 0-3 with a short transfer in each mode, verifying SCLK idle polarity, edge alignment, and MOSI/MISO sampling behavior.
# - single_byte_tx_rx_loopback: Write one TX byte, issue a one-byte bidirectional command, loop MOSI to MISO in the testbench, and confirm RXDATA matches the transmitted pattern.
# - cs_select_and_idle_timing: Select each chip-select index 0-3, verify only the chosen csn_o line asserts low, and confirm CSN_LEAD/TRAIl/IDLE programming affects observable gaps at a coarse functional level.
# - multi_segment_csaat_chain: Queue two or more commands with CSAAT set on the first segment, verify chip-select remains asserted across segments, and confirm the controller continues the same transaction without deasserting CS.
# - tx_underflow_error: Issue a transmit or bidirectional command without sufficient TX FIFO data, verify underflow indication and associated interrupt/error behavior, and ensure the controller does not falsely complete the transfer.
# - rx_overflow_error: Drive repeated receive data into a full RX FIFO, verify overflow indication and status behavior, and confirm readable data is preserved up to FIFO depth.
# - fifo_depth_and_status: Fill TX FIFO to depth 16 and RX FIFO to depth 16, verify STATUS TXLVL/RXLVL and full/empty flags transition correctly at boundaries.
#
# Random tests:
# - constrained_register_fuzz: Randomize legal CSR writes for CONFIGOPTS, CSID, timing fields, and command descriptors while checking TL-UL readback, register side effects, and no illegal bus responses.
# - mixed_segment_stream: Generate short random sequences of transmit-only, receive-only, and bidirectional segments with random lengths 1-8 bytes, random CSAAT usage, and loopback MISO stimulus to validate sequencing.
# - fifo_pressure_random: Randomly interleave TXDATA writes, RXDATA reads, and command launches to stress FIFO level tracking, underflow/overflow detection, and command FIFO backpressure behavior.
# - spi_mode_and_divider_random: Randomly sweep CPOL/CPHA and small divider values while running short transfers to catch edge-alignment bugs, idle polarity mistakes, and divider off-by-one errors.
