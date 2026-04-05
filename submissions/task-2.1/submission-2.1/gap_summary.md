# Gap Summary

## Per-DUT Coverage Snapshot

| DUT | Line % | Target Line % | Branch % | Target Branch % |
|-----|--------|---------------|----------|------------------|
| nexus_uart | 60.08 | 85.00 | 14.49 | 75.00 |
| bastion_gpio | 73.21 | 85.00 | 13.77 | 75.00 |
| warden_timer | 71.28 | 85.00 | 20.66 | 75.00 |
| citadel_spi | 57.17 | 85.00 | 22.08 | 75.00 |
| aegis_aes | 34.33 | 85.00 | 8.11 | 75.00 |
| sentinel_hmac | 47.49 | 85.00 | 6.58 | 75.00 |
| rampart_i2c | 49.33 | 85.00 | 23.49 | 75.00 |

## Top 10 Gaps By Severity

| Rank | Gap ID | DUT | Block | Severity | Difficulty | Range |
|------|--------|-----|-------|----------|------------|-------|
| 1 | GAP-018 | aegis_aes | sbox_inverse_lookup_space | critical | hard | 96-162 |
| 2 | GAP-017 | aegis_aes | sbox_forward_lookup_space | critical | hard | 28-92 |
| 3 | GAP-025 | rampart_i2c | host_addr_shift_and_arbitration | critical | hard | 748-775 |
| 4 | GAP-021 | sentinel_hmac | sha_done_transition_mux | critical | hard | 542-558 |
| 5 | GAP-028 | rampart_i2c | target_clock_stretch_release | critical | hard | 1205-1218 |
| 6 | GAP-027 | rampart_i2c | host_repeated_start_timing | high | medium | 953-970 |
| 7 | GAP-019 | aegis_aes | key_expansion_roundkey_cases | high | medium | 530-546 |
| 8 | GAP-026 | rampart_i2c | host_write_ack_command_chaining | high | medium | 851-867 |
| 9 | GAP-013 | citadel_spi | active_command_context | high | medium | 126-141 |
| 10 | GAP-022 | sentinel_hmac | block_source_select_hmac_paths | high | medium | 730-741 |

## Coverage Heat Map

| DUT | Uncovered Lines | Worst Region | Rationale |
|-----|------------------|--------------|-----------|
| rampart_i2c | 493 | 748-775 | Protocol corner-state transitions need adversarial bus timing |
| aegis_aes | 350 | 96-162 | Lookup-table and key schedule diversity is limited |
| sentinel_hmac | 282 | 45-77 | HMAC multi-stage FSM paths are only partially traversed |
| citadel_spi | 263 | 126-141 | Control-path mode combinations under-tested |
| nexus_uart | 188 | 523-533 | Control-path mode combinations under-tested |
| warden_timer | 83 | 56-65 | Control-path mode combinations under-tested |
| bastion_gpio | 56 | 42-48 | Control-path mode combinations under-tested |

## Effort Estimation

| Bucket | Gap Count | Typical Work |
|--------|-----------|--------------|
| easy | 8 | Directed CSR stimuli and simple protocol permutations |
| medium | 13 | New constrained sequences with scoreboard extensions |
| hard | 7 | Timing-sensitive scenarios and deeper protocol modeling |
| very_hard | 0 | Architectural corner modeling and cross-agent orchestration |
