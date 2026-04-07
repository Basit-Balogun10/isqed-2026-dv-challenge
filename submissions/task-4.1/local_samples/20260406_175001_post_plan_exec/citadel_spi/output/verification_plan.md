# Verification Plan

## Features
- TL-UL register access smoke and protocol sanity
- Reset behavior and default register state
- SPI mode coverage across CPOL/CPHA combinations
- Clock divider programming and SCLK idle/active polarity
- Chip-select decode and single-active-CS behavior
- TX FIFO enqueue/dequeue and level tracking
- RX FIFO capture and readback
- Segment command execution for TX, RX, and bidirectional transfers
- CSAAT multi-segment chaining and CS hold behavior
- Error reporting for TX underflow, RX overflow, and command FIFO overflow
- Interrupt assertion/clear behavior
- Per-chip-select timing knobs: lead, trail, idle
- Basic back-to-back transaction sequencing
- MOSI/MISO bit ordering and byte ordering
- Stall behavior when command chaining waits for next descriptor

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_and_csr_smoke: Apply reset, verify TL-UL accessibility, confirm all readable CSRs return sane defaults, and check idle outputs: all csn_o high, SCLK at CPOL-defined idle, intr_o deasserted, alert_o low.
- config_mode_sweep: Program CONFIGOPTS across all four SPI modes and a small set of divider values; verify idle SCLK polarity, active SCLK toggling, and mode-dependent MOSI launch/sample edge behavior with a simple loopback MISO model.
- single_byte_tx_transfer: Write one TX byte, issue a transmit segment of length 1, and verify MOSI bit order, CS assertion/deassertion, TX level decrement, and completion status/interrupt behavior.
- single_byte_rx_transfer: Issue a receive-only segment while driving a known MISO byte pattern, then read RXDATA and verify byte capture, RX level increment/decrement, and correct CS timing.
- bidirectional_transfer: Queue matching TX data and MISO stimulus for a bidirectional segment, verify simultaneous transmit/receive operation, FIFO consumption, and no protocol deadlock.
- csaat_two_segment_chain: Execute a two-segment transaction with CSAAT set on the first segment and clear on the second; verify CS remains asserted across the boundary, command FIFO chaining works, and final deassertion occurs only after the last segment.
- fifo_boundary_and_underflow: Fill TX FIFO to depth, attempt one extra write, then run a transmit segment with insufficient TX data to provoke underflow and confirm error/interrupt reporting.
- rx_overflow_protection: Drive more received bytes than RX FIFO depth without draining it, verify overflow detection, status flags, and that subsequent reads return the oldest valid data only.
- command_fifo_overflow: Push more than four command descriptors, verify command FIFO full handling, backpressure or error indication, and that accepted commands still execute in order.
- cs_timing_programming: Program nonzero and zero lead/trail/idle timing values for one chip-select, then measure relative CS-to-SCLK and inter-transaction gaps to confirm minimum-delay behavior when fields are zero.

## Random Tests
- tlul_csr_fuzz_with_scoreboard: Constrained-random TL-UL register reads/writes over the documented CSR map with a lightweight mirror model, focusing on legal field values, status polling, and interrupt clear/set sequences.
- spi_segment_random_stream: Generate random legal segment descriptors, lengths, directions, CSAAT settings, and chip-select selections; drive randomized MISO data and compare TX/RX FIFO effects against a Python reference model.
- mode_and_divider_randomization: Randomly sweep CPOL/CPHA and divider values within a bounded set while checking SCLK polarity, edge placement, and transaction completion under varying clock ratios.
- fifo_pressure_random: Apply randomized bursts of TX writes, RX reads, and command submissions to stress FIFO level accounting, full/empty transitions, and error recovery without exceeding the 60-minute runtime budget.

## Risk Areas
- Segment command sequencing and CSAAT chaining (high): Estimated FSM complexity is high and multi-segment behavior is a common source of off-by-one, stall, and CS hold bugs; this is the highest functional risk.
- FIFO boundary conditions and error handling (high): 16-entry TX/RX FIFOs and 4-entry command FIFO create multiple overflow/underflow edges that can break status, interrupts, or transaction progress.
- SPI mode timing correctness (high): CPOL/CPHA edge alignment, idle polarity, and first-bit launch/sample behavior are easy to implement incorrectly and directly affect interoperability.
- Chip-select timing parameters (medium): Lead, trail, and idle timing are parameterized and may have special zero-value minimum-delay behavior that is prone to corner-case bugs.
- TL-UL register access and CSR field decoding (medium): The design is bus-controlled; incorrect register decode or write side effects can block all higher-level functionality, but basic smoke tests usually catch this quickly.
- Interrupt and alert signaling (medium): Interrupts are often under-tested in short schedules; they are important for software integration but lower risk than core data-path and FSM behavior.
- Receive-only MOSI behavior (low): The specification leaves MOSI unspecified during receive-only segments, so this area is lower priority and should only be checked for non-X/stability if the implementation exposes a defined behavior.
