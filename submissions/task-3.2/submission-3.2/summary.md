# Task 3.2 Trace Summary

## Failure Overview

| Failure | DUT | Manifestation Cycle | Root Cause Cycle | Latency | One-line Diagnosis |
|---|---|---:|---:|---:|---|
| Trace 01 | warden_timer | 150 | 142 | 8 | Split MTIMECMP write is compared non-atomically, causing early timer interrupt set |
| Trace 02 | nexus_uart | 500 | 490 | 10 | TX overflow write corrupts FIFO payload despite full-state pointer freeze |
| Trace 03 | citadel_spi | 300 | 300 | 0 | CS hold completion condition fires one SCLK tick too early |
| Trace 04 | aegis_aes | 200 | 173 | 27 | CBC block1 uses stale IV rather than C0 chain value |
| Trace 05 | rampart_i2c | 400 | 397 | 3 | Repeated START setup momentarily matches STOP signature |

## Debug Methodology

1. Started from the failing assertion cycle in each description file and aligned it with the provided signal CSV window.
2. Built a backward causal chain from symptom to source by tracing both data path signals and control path signals.
3. Cross-referenced each candidate mechanism against RTL implementation with exact file/line anchoring.
4. Selected root-cause cycles at the first divergence point (not at later downstream corruption points).
5. Wrote dedicated reproduction tests that check the violated property directly and fail with targeted assertion text.

## Difficulty Assessment

- Trace 04 (AES CBC chain) was the hardest because manifestation is late and depends on internal round-state chaining semantics.
- Trace 05 (I2C repeated START) required temporal bus-event ordering (START/STOP edge semantics), not just FSM state checks.
- Trace 01/02/03 were more direct because their failure signatures were tightly correlated with single control-path events.
