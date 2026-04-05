# sentinel_hmac Coverage Gaps

## Coverage Snapshot

- Line coverage: 47.49%
- Branch coverage: 6.58%

## Uncovered Code Regions

| Gap ID | File | Line Range | Reason Uncovered |
|--------|------|------------|------------------|
| GAP-021 | duts/sentinel_hmac/sentinel_hmac.sv | 542-558 | Baseline tests do not fully combine pad-return flags with HMAC mode transitions, so done-state routing branches remain unhit. |
| GAP-022 | duts/sentinel_hmac/sentinel_hmac.sv | 730-741 | HMAC-specific block source multiplexing (ipad/opad/outer/padlen) is not comprehensively traversed. |
| GAP-023 | duts/sentinel_hmac/sentinel_hmac.sv | 746-753 | Round pipeline updates are executed but not under varied enough data/control conditions to cover all update branches and shift scheduling. |
| GAP-024 | duts/sentinel_hmac/sentinel_hmac.sv | 307-315 | CSR negative accesses and extended status reads are not included, leaving decode default/error paths uncovered. |

## Unhit Functional Coverage Bins (Estimated From VPlan)

| Gap ID | Coverpoint | Bin Name | Required Stimulus |
|--------|------------|----------|-------------------|
| GAP-021 | vp_scenario_id | VP-HMAC-009, VP-HMAC-010, VP-HMAC-014 | Create directed sequences for every ST_SHA_DONE_BLOCK return path (plain SHA, HMAC inner, HMAC outer). |
| GAP-022 | vp_scenario_id | VP-HMAC-004, VP-HMAC-011, VP-HMAC-016 | Exercise all SHA block source selections and verify injected block contents for each HMAC stage. |
| GAP-023 | vp_scenario_id | VP-HMAC-006, VP-HMAC-007, VP-HMAC-017 | Stress SHA round pipeline with varied message block patterns and verify state register evolution per round. |
| GAP-024 | vp_scenario_id | VP-HMAC-001, VP-HMAC-013 | Issue valid and invalid CSR reads during idle/busy states and validate returned data plus error flag behavior. |

## Root Cause And Intent

### GAP-021 - sha_done_transition_mux
- Root cause: Baseline tests do not fully combine pad-return flags with HMAC mode transitions, so done-state routing branches remain unhit.
- Test intent: Create directed sequences for every ST_SHA_DONE_BLOCK return path (plain SHA, HMAC inner, HMAC outer).

### GAP-022 - block_source_select_hmac_paths
- Root cause: HMAC-specific block source multiplexing (ipad/opad/outer/padlen) is not comprehensively traversed.
- Test intent: Exercise all SHA block source selections and verify injected block contents for each HMAC stage.

### GAP-023 - sha_round_pipeline_update
- Root cause: Round pipeline updates are executed but not under varied enough data/control conditions to cover all update branches and shift scheduling.
- Test intent: Stress SHA round pipeline with varied message block patterns and verify state register evolution per round.

### GAP-024 - status_and_error_read_decode
- Root cause: CSR negative accesses and extended status reads are not included, leaving decode default/error paths uncovered.
- Test intent: Issue valid and invalid CSR reads during idle/busy states and validate returned data plus error flag behavior.
