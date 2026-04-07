# Auto-generated test intent summary
#
# Directed tests:
# - reset_and_csr_smoke: Apply reset, verify TL-UL accessibility, confirm all readable CSRs return sane defaults, and check idle outputs: all csn_o high, SCLK at CPOL-defined idle, intr_o deasserted, alert_o low.
# - config_mode_sweep: Program CONFIGOPTS across all four SPI modes and a small set of divider values; verify idle SCLK polarity, active SCLK toggling, and mode-dependent MOSI launch/sample edge behavior with a simple loopback MISO model.
# - single_byte_tx_transfer: Write one TX byte, issue a transmit segment of length 1, and verify MOSI bit order, CS assertion/deassertion, TX level decrement, and completion status/interrupt behavior.
# - single_byte_rx_transfer: Issue a receive-only segment while driving a known MISO byte pattern, then read RXDATA and verify byte capture, RX level increment/decrement, and correct CS timing.
# - bidirectional_transfer: Queue matching TX data and MISO stimulus for a bidirectional segment, verify simultaneous transmit/receive operation, FIFO consumption, and no protocol deadlock.
# - csaat_two_segment_chain: Execute a two-segment transaction with CSAAT set on the first segment and clear on the second; verify CS remains asserted across the boundary, command FIFO chaining works, and final deassertion occurs only after the last segment.
# - fifo_boundary_and_underflow: Fill TX FIFO to depth, attempt one extra write, then run a transmit segment with insufficient TX data to provoke underflow and confirm error/interrupt reporting.
# - rx_overflow_protection: Drive more received bytes than RX FIFO depth without draining it, verify overflow detection, status flags, and that subsequent reads return the oldest valid data only.
# - command_fifo_overflow: Push more than four command descriptors, verify command FIFO full handling, backpressure or error indication, and that accepted commands still execute in order.
# - cs_timing_programming: Program nonzero and zero lead/trail/idle timing values for one chip-select, then measure relative CS-to-SCLK and inter-transaction gaps to confirm minimum-delay behavior when fields are zero.
#
# Random tests:
# - tlul_csr_fuzz_with_scoreboard: Constrained-random TL-UL register reads/writes over the documented CSR map with a lightweight mirror model, focusing on legal field values, status polling, and interrupt clear/set sequences.
# - spi_segment_random_stream: Generate random legal segment descriptors, lengths, directions, CSAAT settings, and chip-select selections; drive randomized MISO data and compare TX/RX FIFO effects against a Python reference model.
# - mode_and_divider_randomization: Randomly sweep CPOL/CPHA and divider values within a bounded set while checking SCLK polarity, edge placement, and transaction completion under varying clock ratios.
# - fifo_pressure_random: Apply randomized bursts of TX writes, RX reads, and command submissions to stress FIFO level accounting, full/empty transitions, and error recovery without exceeding the 60-minute runtime budget.
