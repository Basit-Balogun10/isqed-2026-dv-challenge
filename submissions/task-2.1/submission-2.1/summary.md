# Task 2.1 Executive Summary

This report consolidates gap analysis across all seven DUTs and maps each gap to actionable stimulus intent.

## Highest Priority Gaps

- GAP-018 (aegis_aes): sbox_inverse_lookup_space [critical, hard]
- GAP-017 (aegis_aes): sbox_forward_lookup_space [critical, hard]
- GAP-025 (rampart_i2c): host_addr_shift_and_arbitration [critical, hard]
- GAP-021 (sentinel_hmac): sha_done_transition_mux [critical, hard]
- GAP-028 (rampart_i2c): target_clock_stretch_release [critical, hard]
- GAP-027 (rampart_i2c): host_repeated_start_timing [high, medium]
- GAP-019 (aegis_aes): key_expansion_roundkey_cases [high, medium]
- GAP-026 (rampart_i2c): host_write_ack_command_chaining [high, medium]
- GAP-013 (citadel_spi): active_command_context [high, medium]
- GAP-022 (sentinel_hmac): block_source_select_hmac_paths [high, medium]
- GAP-001 (nexus_uart): rx_oversample_start_path [high, medium]
- GAP-020 (aegis_aes): cbc_iv_control_programming [high, medium]

## Coverage Baseline

| DUT | Line % | Branch % |
|-----|--------|----------|
| nexus_uart | 60.08 | 14.49 |
| bastion_gpio | 73.21 | 13.77 |
| warden_timer | 71.28 | 20.66 |
| citadel_spi | 57.17 | 22.08 |
| aegis_aes | 34.33 | 8.11 |
| sentinel_hmac | 47.49 | 6.58 |
| rampart_i2c | 49.33 | 23.49 |
