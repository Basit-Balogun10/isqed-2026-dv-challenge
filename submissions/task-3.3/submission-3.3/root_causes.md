# Root Causes

## Bucket 1 - nexus_uart RX oversampling phase drift

### What is broken
RX sampling phase drifts, causing byte corruption, stop-bit frame errors, parity side effects, and occasional start-bit timing failures.

### Where it is broken
- Module: `nexus_uart`
- Approximate lines: 456-466
- Signals and logic: `rx_os_divisor`, `rx_os_tick`, `ctrl_baud_divisor`, `rx_baud_cnt`

### Why it is broken
Oversampling divisor derivation uses truncation-only behavior for baud division and lacks robust minimum-period behavior in edge conditions. This introduces timing bias in the oversampling clock and misaligns receive sampling points.

### Impact scope
- Affected tests: 7 failures (`test_003`, `test_017`, `test_041`, `test_089`, `test_058`, `test_025`, `test_112`)
- Feature areas: RX robustness, baud mismatch tolerance, frame/parity integrity.

### Severity assessment
High to critical. It causes direct receive-path data integrity failures and protocol violations.

## Bucket 2 - warden_timer watchdog off-by-one bark/bite

### What is broken
Watchdog bark/bite interrupts assert one cycle earlier than expected.

### Where it is broken
- Module: `warden_timer`
- Approximate lines: 124-131
- Signals and logic: `wd_bark`, `wd_bite`, `wd_count_q`, `wd_bark_thresh_q`, `wd_bite_thresh_q`

### Why it is broken
Comparator uses `>=` instead of strict `>` for interval completion semantics, so threshold equality triggers too early.

### Impact scope
- Affected tests: 8 failures (`test_007`, `test_023`, `test_056`, `test_078`, `test_099`, `test_134`, `test_167`, `test_188`)
- Feature areas: watchdog timing guarantees, bark/bite precision, boundary behavior.

### Severity assessment
Medium to high. It breaks timing contracts and can cause premature resets/interrupts.

## Bucket 3 - citadel_spi CPHA edge mapping inversion

### What is broken
SPI receive path samples on the wrong edge in CPHA=1 configurations, producing stale-bit and RX byte mismatches.

### Where it is broken
- Module: `citadel_spi`
- Approximate lines: 162-171
- Signals and logic: `sample_edge`, `output_edge`, `leading_edge`, `trailing_edge`, `reg_cpha`

### Why it is broken
For CPHA=1, sample/output edge assignment is inverted relative to SPI timing requirements.

### Impact scope
- Affected tests: 6 failures (`test_011`, `test_034`, `test_145`, `test_067`, `test_101`, `test_178`)
- Feature areas: mode-specific RX reliability, burst transfers, monitor/scoreboard alignment.

### Severity assessment
High. This is protocol-level functional breakage in a common SPI operating mode.

## Bucket 4 - bastion_gpio masked write suppression

### What is broken
Masked output writes do not reliably update `DATA_OUT`/`gpio_o`, causing persistent readback and pin-state mismatches.

### Where it is broken
- Module: `bastion_gpio`
- Approximate lines: 215-230
- Signals and logic: `reg_data_out`, masked write handlers for `ADDR_MASKED_OUT_LOWER/UPPER`, `tl_wdata`, `tl_a_mask_i`

### Why it is broken
Per-bit write gating interacts incorrectly with TL-UL byte enables, suppressing writes that should commit under valid mask/data combinations.

### Impact scope
- Affected tests: 8 failures (`test_171`, `test_082`, `test_009`, `test_108`, `test_195`, `test_028`, `test_055`, `test_143`)
- Feature areas: masked writes, output control, GPIO readback consistency.

### Severity assessment
High. It breaks deterministic GPIO programming semantics and can silently disable output control.

## Bucket 5 - sentinel_hmac padding length endianness/order error

### What is broken
Final digest values diverge from reference for multi-block messages, often with broad word-level mismatches.

### Where it is broken
- Module: `sentinel_hmac`
- Approximate lines: 310-323
- Signals and logic: `pad_block`, `msg_length_q`, `pad_state == PAD_LENGTH`

### Why it is broken
The 64-bit message-length field appended in final padding uses incorrect byte/word ordering, violating SHA-256 padding conventions.

### Impact scope
- Affected tests: 6 failures (`test_126`, `test_015`, `test_073`, `test_044`, `test_098`, `test_159`)
- Feature areas: multi-block SHA/HMAC correctness, digest validity.

### Severity assessment
Critical. Cryptographic outputs are functionally wrong and cannot be trusted.
