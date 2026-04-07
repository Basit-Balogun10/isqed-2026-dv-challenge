# Verification Plan

## Features
- TL-UL register access smoke and decode checks for all 12 CSRs
- Reset behavior and default register state validation
- SPI mode configuration coverage for CPOL/CPHA modes 0-3
- Clock divider programming and SCLK idle/active polarity checks
- Chip-select selection and one-hot active-low csn_o[3:0] behavior
- TX FIFO enqueue/dequeue behavior via TXDATA and STATUS level tracking
- RX FIFO fill/read behavior via RXDATA and STATUS level tracking
- Command FIFO enqueue and segment execution sequencing
- Segment length handling for 1-byte and multi-byte transfers
- CSAAT multi-segment transaction continuity and CS hold behavior
- Transmit-only, receive-only, and bidirectional segment coverage
- Interrupt and error flag observation for underflow/overflow/basic completion events
- Basic timing parameter programming for CSN_LEAD, CSN_TRAIL, and CSN_IDLE
- MOSI/MISO bit ordering and byte ordering checks
- Idle-to-active and active-to-idle transaction transitions

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_and_csr_smoke: Apply reset, verify all readable CSRs return legal defaults, confirm TL-UL read/write access, and check idle pin states for sclk_o, csn_o, mosi_o, intr_o, and alert_o.
- spi_mode_matrix_basic: Program CPOL/CPHA across modes 0-3 with a short transfer in each mode, verifying SCLK idle polarity, edge alignment, and MOSI/MISO sampling behavior.
- single_byte_tx_rx_loopback: Write one TX byte, issue a one-byte bidirectional command, loop MOSI to MISO in the testbench, and confirm RXDATA matches the transmitted pattern.
- cs_select_and_idle_timing: Select each chip-select index 0-3, verify only the chosen csn_o line asserts low, and confirm CSN_LEAD/TRAIl/IDLE programming affects observable gaps at a coarse functional level.
- multi_segment_csaat_chain: Queue two or more commands with CSAAT set on the first segment, verify chip-select remains asserted across segments, and confirm the controller continues the same transaction without deasserting CS.
- tx_underflow_error: Issue a transmit or bidirectional command without sufficient TX FIFO data, verify underflow indication and associated interrupt/error behavior, and ensure the controller does not falsely complete the transfer.
- rx_overflow_error: Drive repeated receive data into a full RX FIFO, verify overflow indication and status behavior, and confirm readable data is preserved up to FIFO depth.
- fifo_depth_and_status: Fill TX FIFO to depth 16 and RX FIFO to depth 16, verify STATUS TXLVL/RXLVL and full/empty flags transition correctly at boundaries.

## Random Tests
- constrained_register_fuzz: Randomize legal CSR writes for CONFIGOPTS, CSID, timing fields, and command descriptors while checking TL-UL readback, register side effects, and no illegal bus responses.
- mixed_segment_stream: Generate short random sequences of transmit-only, receive-only, and bidirectional segments with random lengths 1-8 bytes, random CSAAT usage, and loopback MISO stimulus to validate sequencing.
- fifo_pressure_random: Randomly interleave TXDATA writes, RXDATA reads, and command launches to stress FIFO level tracking, underflow/overflow detection, and command FIFO backpressure behavior.
- spi_mode_and_divider_random: Randomly sweep CPOL/CPHA and small divider values while running short transfers to catch edge-alignment bugs, idle polarity mistakes, and divider off-by-one errors.

## Risk Areas
- SPI mode edge alignment and sampling (high): CPOL/CPHA combinations are a common source of off-by-one edge bugs, and the design has multiple FSM blocks controlling launch/sample timing.
- FIFO boundary and status correctness (high): TX/RX FIFO depth, full/empty flags, and level counters are high-risk for integration bugs and are directly observable through software.
- CSAAT multi-segment sequencing (high): Keeping chip-select asserted across command boundaries exercises command FIFO interaction and stall behavior, which is likely to contain corner-case bugs.
- Underflow and overflow error handling (high): Error paths often have incomplete coverage and can affect interrupt generation, status reporting, and transaction termination.
- Chip-select timing parameters (medium): CSN_LEAD, CSN_TRAIL, and CSN_IDLE are timing-sensitive and may have implementation-specific minimum-delay behavior.
- TL-UL register decode and reset defaults (medium): Basic bus access is essential but lower risk than protocol timing; still needed to unblock all other tests.
- Alert and interrupt pin behavior (low): These outputs are important for system integration, but can be partially validated with limited autonomous time.
