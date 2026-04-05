# Task 3.1 Summary

## Failure Triage Table

| Failure | Classification | Root Module | One-line Summary |
|---|---|---|---|
| failure_01 | testbench_bug | uart_driver | Stimulus parity generation drives invalid even-parity bits on specific frames. |
| failure_02 | functional_bug | nexus_uart | RX overflow scenario corrupts FIFO tail entry instead of drop-only behavior. |
| failure_03 | testbench_bug | gpio_scoreboard | Checker treats sticky INTR_STATE bit as edge counter during rapid toggling. |
| failure_04 | configuration_error | timer_driver | Comparator programmed with unsafe split-write ordering in non-atomic register model. |
| failure_05 | timing_issue | citadel_spi | Dynamic CPHA transition causes one-bit receive phase slip (0xB7 -> 0x5B). |
| failure_06 | functional_bug | aegis_aes | Decrypt inverse datapath corrupts one word in encrypt/decrypt roundtrip. |
| failure_07 | functional_bug | sentinel_hmac | Multi-block digest path corrupts late digest words on 128-byte workload. |
| failure_08 | protocol_violation | rampart_i2c | Host continues data transfer after address NACK instead of immediate STOP. |
| failure_09 | testbench_bug | timer_scoreboard | Checker expects bark one cycle later than inclusive threshold semantics. |
| failure_10 | configuration_error | i2c_driver | Timeout test does not enable timeout logic and checks wrong INTR_STATE bit. |

## Bug Clustering

- UART receive-path robustness cluster: failure_01, failure_02
  - One timing-sensitive parity issue and one full-boundary overflow integrity issue.
- Timer setup/expectation cluster: failure_04, failure_09
  - One unsafe comparator programming sequence and one checker off-by-one expectation.
- I2C host control/timeout cluster: failure_08, failure_10
  - Address-NACK policy violation plus timeout test setup/mapping mismatch.
- Cryptographic datapath cluster: failure_06, failure_07
  - Decrypt inverse transform issue and multi-block digest schedule/state issue.
- Verification infrastructure issue: failure_03
  - Checker model mismatch against sticky interrupt semantics.
- SPI phase-transition issue: failure_05
  - Edge/phase timing sensitivity after configuration transitions.

## Cross-Cutting Observations

- Boundary transitions are dominant risk points.
  - Full/empty FIFO edges, split-word register programming, threshold equality boundaries, and
    mode transitions repeatedly produce failures.
- Several bugs are not random-data bugs; they are policy/timing bugs.
  - NACK policy and timeout IRQ mapping are control-path correctness defects.
- Timing warnings are not always benign.
  - In failure_01 and failure_05, timing-edge behavior aligns with functional mismatch signatures.

## Confidence Assessment

- Highest confidence: failure_03, failure_04, failure_09, failure_10
  - Logs and spec semantics align tightly with sticky-bit, non-atomic-write, and threshold rules.
- Medium confidence: failure_02, failure_06, failure_08
  - Strong evidence with clear effect, but exact internal trigger sequence has multiple paths.
- Lower confidence: failure_05, failure_07
  - Symptoms are clear, but multiple plausible internal mechanisms remain.
