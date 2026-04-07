# Verification Plan

## Features
- TL-UL register access smoke and protocol compliance on citadel_spi CSR block
- Reset behavior and default register/IO state validation
- SPI mode coverage across CPOL/CPHA combinations (modes 0-3)
- Clock divider programming and SCLK idle/toggle behavior
- Chip-select selection and active-low behavior across 4 CS lines
- CS lead/trail/idle timing programming and observable spacing
- TX FIFO enqueue/dequeue behavior and STATUS level tracking
- RX FIFO fill/read behavior and STATUS level tracking
- Command FIFO enqueue and segment execution sequencing
- Transmit-only, receive-only, and bidirectional segment execution
- CSAAT multi-segment chaining and CS hold behavior
- Error detection for TX underflow, RX overflow, and command FIFO full conditions
- Interrupt and alert output sanity for error/event conditions
- MISO/MOSI data path integrity with byte ordering MSB-first
- Idle-state behavior when no transaction is active
- Back-to-back transaction behavior with inter-CS idle timing
- Basic stress of FIFO boundaries within a 60-minute autonomous run

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_and_csr_smoke: Apply reset, verify all CS lines deasserted, SCLK idle at CPOL default, MOSI quiescent, interrupts cleared, and perform TL-UL reads/writes to all discovered CSRs for accessibility and reset-value sanity.
- spi_mode_matrix_basic: Program CPOL/CPHA for all four SPI modes and run a one-byte transfer in each mode to confirm idle polarity, edge alignment, and basic MOSI/MISO sampling behavior.
- clock_divider_sweep: Program representative divider values including minimum, mid, and large settings; measure SCLK period ratio against the system clock and confirm 50% duty cycle and idle polarity retention.
- cs_selection_and_timing: Select each CS index 0-3, verify only the chosen active-low line asserts, and check lead/trail/idle timing fields produce observable spacing between CS assertion, SCLK start, CS deassertion, and next transaction.
- tx_rx_fifo_basic: Fill TX FIFO with a small burst, execute transmit and bidirectional segments, read RX FIFO data back, and confirm STATUS TXLVL/RXLVL updates and data ordering.
- segment_chain_csaat: Queue two or more command segments with CSAAT set on the first segment and verify CS remains asserted across the boundary, then deasserts only after the final segment when CSAAT is cleared.
- tx_underflow_error: Issue a transmit or bidirectional command with insufficient TX FIFO data to force underflow and check error indication, interrupt behavior, and safe recovery after refill.
- rx_overflow_error: Drive more received bytes than RX FIFO can hold without draining it, verify overflow error reporting, and confirm subsequent reads return the expected retained data behavior.
- command_fifo_full_and_stall: Push command FIFO to capacity, verify full indication or backpressure, then attempt one additional command and confirm graceful handling without corrupting queued commands.
- back_to_back_transactions: Run consecutive transactions with different CS targets and idle timing settings to validate inter-CS delay, CS handoff, and no unintended overlap between chip-selects.

## Random Tests
- tlul_csr_fuzz_light: Constrained-random TL-UL read/write sequences over the 12 CSRs with scoreboarded mirror model, focusing on legal accesses, reset recovery, and readback consistency.
- spi_segment_random_short: Generate random short SPI transactions with randomized direction, length, CSAAT, CSID, and mode settings, bounded to small byte counts for fast autonomous execution and broad branch coverage.
- fifo_pressure_random: Randomly interleave TXDATA writes, RXDATA reads, and command submissions to exercise FIFO level transitions, near-full/near-empty states, and error recovery paths.

## Risk Areas
- SPI mode edge alignment and sampling (high): CPOL/CPHA combinations are a common source of off-by-one edge bugs and directly affect data integrity across all transfers.
- FIFO underflow/overflow handling (high): The design has independent TX/RX FIFOs and command FIFO; boundary conditions are likely and can corrupt transactions or hang the controller.
- CSAAT multi-segment sequencing (high): Keeping CS asserted across segments requires correct command FIFO handoff and state retention, which is a high-risk FSM interaction.
- Clock divider and timing generation (high): SCLK frequency, duty cycle, and CS lead/trail/idle timing depend on counters and FSM timing, making them prone to off-by-one errors.
- Chip-select exclusivity (medium): Only one of four active-low CS outputs may assert at a time; decode or arbitration bugs can cause illegal simultaneous selection.
- TL-UL register access and reset values (medium): CSR map correctness is foundational and quick to verify, but less risky than the SPI datapath once basic access is proven.
- Interrupt and alert signaling (medium): Event/error signaling is important for software integration, but can be sampled with limited directed checks within the time budget.
- Long transaction stress (low): The spec allows up to 512-byte segments, but autonomous budget is limited; long-run stress is lower priority than boundary and sequencing coverage.
