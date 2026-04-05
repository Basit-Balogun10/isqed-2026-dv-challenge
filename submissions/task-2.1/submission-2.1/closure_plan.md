# Prioritized Closure Plan

## Quick Wins

- GAP-006 (bastion_gpio): masked_out_lower_update -> Validate masked lower-half writes with sparse and dense mask patterns while preserving untouched bits.
- GAP-007 (bastion_gpio): masked_out_upper_update -> Exercise MASKED_OUT_UPPER with mixed masks and verify independent control of upper 16 output bits.
- GAP-024 (sentinel_hmac): status_and_error_read_decode -> Issue valid and invalid CSR reads during idle/busy states and validate returned data plus error flag behavior.
- GAP-005 (bastion_gpio): interrupt_mode_register_bank -> Program all edge/level interrupt control banks and confirm each mode can independently assert per-pin interrupts.
- GAP-003 (nexus_uart): tx_parity_branch_select -> Run directed TX bursts in parity disabled/even/odd modes and verify transmitted parity bit policy.
- GAP-004 (nexus_uart): tx_stop_bit_mode_select -> Toggle stop-bit configuration and confirm stop-bit count on the serial line for consecutive frames.
- GAP-011 (warden_timer): mtimecmp1_low_partial_write -> Program MTIMECMP1 low word via masked writes and verify timer1 expiry behavior follows merged value.
- GAP-012 (warden_timer): mtimecmp1_high_partial_write -> Apply partial high-word writes and validate 64-bit compare behavior around rollover boundaries.

## Moderate Effort

- GAP-027 (rampart_i2c): host_repeated_start_timing -> Generate repeated-start command sequences and validate timing counters for tsu_sta/thd_sta transitions.
- GAP-019 (aegis_aes): key_expansion_roundkey_cases -> Drive full key expansion through all round-key indices and validate generated keys against software model.
- GAP-026 (rampart_i2c): host_write_ack_command_chaining -> Exercise write-ack branch fanout including restart, read-command follow-up, and additional write commands.
- GAP-013 (citadel_spi): active_command_context -> Issue command segments across TX/RX/BIDIR directions, speed modes, and CSAAT settings to validate active command bookkeeping.
- GAP-022 (sentinel_hmac): block_source_select_hmac_paths -> Exercise all SHA block source selections and verify injected block contents for each HMAC stage.
- GAP-001 (nexus_uart): rx_oversample_start_path -> Drive randomized baud divisors with phase-offset start bits and verify RX state transitions and sampled data alignment.
- GAP-020 (aegis_aes): cbc_iv_control_programming -> Exercise mode/op/control permutations and verify IV updates for CBC encrypt/decrypt across consecutive blocks.
- GAP-002 (nexus_uart): rx_stop2_and_error_latch -> Exercise 2-stop-bit mode with bad stop levels and near-full RX FIFO to validate frame-error and overflow behavior.
- GAP-014 (citadel_spi): command_decode_write_path -> Drive command writes that exercise valid and invalid direction/length combinations under FIFO pressure.
- GAP-009 (warden_timer): watchdog_lock_gating -> Lock watchdog control and verify subsequent writes cannot disable lock or mutate protected control fields.

## Hard Targets

- GAP-018 (aegis_aes): sbox_inverse_lookup_space -> Expand CBC/ECB decrypt regressions with randomized ciphertext/key sets to drive inverse substitution diversity.
- GAP-017 (aegis_aes): sbox_forward_lookup_space -> Use coverage-directed plaintext/key generation to maximize S-box input diversity during encryption rounds.
- GAP-025 (rampart_i2c): host_addr_shift_and_arbitration -> Run multi-master contention scenarios to trigger host arbitration loss during address transmission.
- GAP-021 (sentinel_hmac): sha_done_transition_mux -> Create directed sequences for every ST_SHA_DONE_BLOCK return path (plain SHA, HMAC inner, HMAC outer).
- GAP-028 (rampart_i2c): target_clock_stretch_release -> Force target clock stretching and validate both release paths: TX data arrival and ACQ space availability.
- GAP-015 (citadel_spi): data_transfer_bit_edge_logic -> Execute transfers in all SPI modes and verify sample/output edge behavior at bit boundaries.
- GAP-023 (sentinel_hmac): sha_round_pipeline_update -> Stress SHA round pipeline with varied message block patterns and verify state register evolution per round.

## Dependency Map

- GAP-017 depends on functional coverage bins for S-box index diversity.
- GAP-025 depends on a second-master contention model.
- GAP-021 depends on FSM transition instrumentation across HMAC return paths.
- GAP-004 depends on timing-check monitor support for stop-bit counting.
- GAP-011 depends on 64-bit timer rollover stimulus helper.

## Execution Order

1. Close all easy gaps first to lift baseline quickly and stabilize infrastructure.
2. Address medium gaps by extending existing drivers/sequences with mode permutations.
3. Tackle hard gaps last with dedicated protocol stress agents and model enhancements.
