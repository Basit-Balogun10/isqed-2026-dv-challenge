#!/usr/bin/env python3
"""Generate Task 2.1 deliverables from baseline coverage plus curated gap data."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "baseline_artifacts"
SUMMARY_JSON = ART / "coverage_summary.json"

PRIMARY_GAP_YAML = ROOT / "gap_analysis.yaml"
PRIMARY_SUMMARY_MD = ROOT / "gap_summary.md"
PRIMARY_PLAN_MD = ROOT / "closure_plan.md"

COMPAT_GAP_DIR = ROOT / "gap_analysis"
COMPAT_SUMMARY_MD = ROOT / "summary.md"
COMPAT_PRIORITY_YAML = ROOT / "priority_table.yaml"

TARGET_LINE = 85.0
TARGET_BRANCH = 75.0

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}
DIFFICULTY_ORDER = {"easy": 1, "medium": 2, "hard": 3, "very_hard": 4}

GAP_TEMPLATES = [
    {
        "dut": "nexus_uart",
        "coverage_type": "line",
        "line_range": "523-533",
        "module": "nexus_uart",
        "block": "rx_oversample_start_path",
        "severity": "high",
        "difficulty": "medium",
        "root_cause": "Reference smoke runs do not vary baud divisors and sample-phase stress, so the RX start-bit qualification and oversampling transitions remain mostly untouched.",
        "test_intent": "Drive randomized baud divisors with phase-offset start bits and verify RX state transitions and sampled data alignment.",
        "recommended_stimulus": [
            "Sweep CTRL.BAUD_DIVISOR across low/nominal/high values",
            "Inject start-bit phase offsets around oversample midpoint",
            "Check RX FIFO byte correctness with monitor timestamps",
        ],
        "dependencies": ["RX line driver with cycle-accurate timing control"],
        "vplan_items": ["VP-UART-001", "VP-UART-003", "VP-UART-011"],
    },
    {
        "dut": "nexus_uart",
        "coverage_type": "line",
        "line_range": "587-595",
        "module": "nexus_uart",
        "block": "rx_stop2_and_error_latch",
        "severity": "high",
        "difficulty": "medium",
        "root_cause": "Current tests avoid malformed stop sequences and FIFO pressure, so STOP2 frame-error and overflow interactions are rarely exercised.",
        "test_intent": "Exercise 2-stop-bit mode with bad stop levels and near-full RX FIFO to validate frame-error and overflow behavior.",
        "recommended_stimulus": [
            "Enable two stop bits and drive invalid second stop",
            "Fill RX FIFO to depth-1 before final stop sampling",
            "Read STATUS and INTR_STATE after each error event",
        ],
        "dependencies": ["Scoreboard support for sticky error semantics"],
        "vplan_items": ["VP-UART-007", "VP-UART-010", "VP-UART-014"],
    },
    {
        "dut": "nexus_uart",
        "coverage_type": "line",
        "line_range": "401-406",
        "module": "nexus_uart",
        "block": "tx_parity_branch_select",
        "severity": "medium",
        "difficulty": "easy",
        "root_cause": "TX tests stay on one parity setting, leaving parity/no-parity branch selection under-covered.",
        "test_intent": "Run directed TX bursts in parity disabled/even/odd modes and verify transmitted parity bit policy.",
        "recommended_stimulus": [
            "Program CTRL.PARITY_MODE through all legal values",
            "Transmit diverse byte patterns per mode",
            "Sample uart_tx_o and decode parity in monitor",
        ],
        "dependencies": ["Parity-aware serial monitor"],
        "vplan_items": ["VP-UART-004", "VP-UART-005"],
    },
    {
        "dut": "nexus_uart",
        "coverage_type": "line",
        "line_range": "422-426",
        "module": "nexus_uart",
        "block": "tx_stop_bit_mode_select",
        "severity": "medium",
        "difficulty": "easy",
        "root_cause": "One-stop-bit default stimulus bypasses stop-bit mode muxing and TX_STOP2 entry conditions.",
        "test_intent": "Toggle stop-bit configuration and confirm stop-bit count on the serial line for consecutive frames.",
        "recommended_stimulus": [
            "Alternate CTRL.STOP_BITS between 0 and 1 each frame",
            "Capture serial waveform and count stop bit durations",
            "Correlate frame timing against programmed baud divisor",
        ],
        "dependencies": ["Timing checker for frame boundary detection"],
        "vplan_items": ["VP-UART-006", "VP-UART-012"],
    },
    {
        "dut": "bastion_gpio",
        "coverage_type": "line",
        "line_range": "42-48",
        "module": "bastion_gpio",
        "block": "interrupt_mode_register_bank",
        "severity": "medium",
        "difficulty": "easy",
        "root_cause": "Reference traffic only validates basic data/dir behavior and does not iterate through all interrupt mode control CSRs.",
        "test_intent": "Program all edge/level interrupt control banks and confirm each mode can independently assert per-pin interrupts.",
        "recommended_stimulus": [
            "Write INTR_CTRL_EN_RISING/FALLING/LVLHIGH/LVLLOW with pin masks",
            "Drive GPIO transitions per enabled mode",
            "Check INTR_STATE bit accumulation and clear behavior",
        ],
        "dependencies": ["Pin-level GPIO event sequencer"],
        "vplan_items": ["VP-GPIO-004", "VP-GPIO-005", "VP-GPIO-006"],
    },
    {
        "dut": "bastion_gpio",
        "coverage_type": "line",
        "line_range": "217-220",
        "module": "bastion_gpio",
        "block": "masked_out_lower_update",
        "severity": "high",
        "difficulty": "easy",
        "root_cause": "Masked output lower-half writes are not explicitly used, so per-bit write-enable loops are largely untouched.",
        "test_intent": "Validate masked lower-half writes with sparse and dense mask patterns while preserving untouched bits.",
        "recommended_stimulus": [
            "Apply walking-1 and walking-0 masks on MASKED_OUT_LOWER",
            "Preload DATA_OUT and verify only selected lower bits mutate",
            "Cross-check GPIO outputs after each write",
        ],
        "dependencies": ["CSR mirror model for bit-preservation checks"],
        "vplan_items": ["VP-GPIO-011", "VP-GPIO-012"],
    },
    {
        "dut": "bastion_gpio",
        "coverage_type": "line",
        "line_range": "224-227",
        "module": "bastion_gpio",
        "block": "masked_out_upper_update",
        "severity": "high",
        "difficulty": "easy",
        "root_cause": "Upper-half masked writes are missing from baseline tests, leaving the mirrored write loop under-covered.",
        "test_intent": "Exercise MASKED_OUT_UPPER with mixed masks and verify independent control of upper 16 output bits.",
        "recommended_stimulus": [
            "Program alternating masks on MASKED_OUT_UPPER",
            "Compare pre/post DATA_OUT upper half",
            "Run with concurrent interrupt enable traffic",
        ],
        "dependencies": ["Bit-accurate register scoreboard"],
        "vplan_items": ["VP-GPIO-013", "VP-GPIO-014"],
    },
    {
        "dut": "bastion_gpio",
        "coverage_type": "line",
        "line_range": "50-52",
        "module": "bastion_gpio",
        "block": "input_synchronizer_pipeline",
        "severity": "medium",
        "difficulty": "medium",
        "root_cause": "Input toggles are not timed to stress synchronizer pipeline latency and previous-sample edge comparisons.",
        "test_intent": "Create back-to-back asynchronous GPIO transitions to validate q1/q2/prev synchronization and edge detection latency.",
        "recommended_stimulus": [
            "Toggle selected GPIO pins near clock edges",
            "Measure detection latency across synchronizer stages",
            "Check rising/falling detectors against expected cycles",
        ],
        "dependencies": ["Asynchronous pin driver with sub-cycle scheduling"],
        "vplan_items": ["VP-GPIO-002", "VP-GPIO-003"],
    },
    {
        "dut": "warden_timer",
        "coverage_type": "line",
        "line_range": "293-297",
        "module": "warden_timer",
        "block": "watchdog_lock_gating",
        "severity": "high",
        "difficulty": "medium",
        "root_cause": "Watchdog lock escalation and post-lock write attempts are not attempted in baseline flows.",
        "test_intent": "Lock watchdog control and verify subsequent writes cannot disable lock or mutate protected control fields.",
        "recommended_stimulus": [
            "Set WATCHDOG_CTRL.lock then issue conflicting writes",
            "Read back WATCHDOG_CTRL after each blocked write",
            "Assert lock monotonicity across resets and transactions",
        ],
        "dependencies": ["CSR negative-test sequence support"],
        "vplan_items": ["VP-TIMER-009", "VP-TIMER-010"],
    },
    {
        "dut": "warden_timer",
        "coverage_type": "line",
        "line_range": "316-319",
        "module": "warden_timer",
        "block": "watchdog_bark_threshold_bytes",
        "severity": "high",
        "difficulty": "medium",
        "root_cause": "Partial-byte writes to bark threshold are not covered, missing byte-mask corner cases on threshold programming.",
        "test_intent": "Use partial TL-UL masks to program bark threshold bytes and check bark interrupt timing consistency.",
        "recommended_stimulus": [
            "Write bark threshold with all 16 byte-mask combinations",
            "Run timer until bark condition and observe intr_o",
            "Compare expected threshold with reconstructed CSR value",
        ],
        "dependencies": ["Timer cycle prediction helper"],
        "vplan_items": ["VP-TIMER-012", "VP-TIMER-013"],
    },
    {
        "dut": "warden_timer",
        "coverage_type": "line",
        "line_range": "250-253",
        "module": "warden_timer",
        "block": "mtimecmp1_low_partial_write",
        "severity": "medium",
        "difficulty": "easy",
        "root_cause": "Comparator-1 tests are sparse and do not apply partial low-word writes with byte masks.",
        "test_intent": "Program MTIMECMP1 low word via masked writes and verify timer1 expiry behavior follows merged value.",
        "recommended_stimulus": [
            "Perform low-word writes with selective tl_a_mask",
            "Read back MTIMECMP1_LOW after each write",
            "Observe timer1 interrupt trigger timing",
        ],
        "dependencies": ["Dual-timer interrupt checker"],
        "vplan_items": ["VP-TIMER-004", "VP-TIMER-005"],
    },
    {
        "dut": "warden_timer",
        "coverage_type": "line",
        "line_range": "257-260",
        "module": "warden_timer",
        "block": "mtimecmp1_high_partial_write",
        "severity": "medium",
        "difficulty": "easy",
        "root_cause": "Upper-word programming of MTIMECMP1 is not deeply exercised, leaving masked high-byte paths uncovered.",
        "test_intent": "Apply partial high-word writes and validate 64-bit compare behavior around rollover boundaries.",
        "recommended_stimulus": [
            "Program MTIMECMP1_HIGH with varying byte masks",
            "Force mtime near 32-bit rollover points",
            "Check compare-trigger correctness across high-word changes",
        ],
        "dependencies": ["64-bit timer rollover stimulus"],
        "vplan_items": ["VP-TIMER-006", "VP-TIMER-014"],
    },
    {
        "dut": "citadel_spi",
        "coverage_type": "line",
        "line_range": "126-141",
        "module": "citadel_spi",
        "block": "active_command_context",
        "severity": "high",
        "difficulty": "medium",
        "root_cause": "Baseline traffic does not vary command direction/speed/csaat combinations enough to activate full command-context handling.",
        "test_intent": "Issue command segments across TX/RX/BIDIR directions, speed modes, and CSAAT settings to validate active command bookkeeping.",
        "recommended_stimulus": [
            "Generate command matrix over direction x speed x csaat",
            "Queue back-to-back mixed command segments",
            "Track active_cmd fields in monitor against command FIFO",
        ],
        "dependencies": ["SPI command-segment sequence generator"],
        "vplan_items": ["VP-SPI-003", "VP-SPI-005", "VP-SPI-009"],
    },
    {
        "dut": "citadel_spi",
        "coverage_type": "line",
        "line_range": "452-459",
        "module": "citadel_spi",
        "block": "command_decode_write_path",
        "severity": "high",
        "difficulty": "medium",
        "root_cause": "Command CSR writes are not stressed under full/near-full FIFO and invalid command combinations.",
        "test_intent": "Drive command writes that exercise valid and invalid direction/length combinations under FIFO pressure.",
        "recommended_stimulus": [
            "Fill CMD FIFO to boundary then push one extra command",
            "Mix zero/non-zero segment lengths and direction fields",
            "Check error_status and intr_state signaling",
        ],
        "dependencies": ["Error scoreboard for cmd_invalid events"],
        "vplan_items": ["VP-SPI-007", "VP-SPI-011"],
    },
    {
        "dut": "citadel_spi",
        "coverage_type": "line",
        "line_range": "757-765",
        "module": "citadel_spi",
        "block": "data_transfer_bit_edge_logic",
        "severity": "high",
        "difficulty": "hard",
        "root_cause": "CPOL/CPHA edge combinations are under-sampled, so edge-aligned bit transfer and first-bit-out handling remain partially uncovered.",
        "test_intent": "Execute transfers in all SPI modes and verify sample/output edge behavior at bit boundaries.",
        "recommended_stimulus": [
            "Sweep CPOL/CPHA through modes 0-3",
            "Capture MOSI/MISO around first and last bit edges",
            "Compare sampled bytes with external SPI model",
        ],
        "dependencies": ["Cycle-accurate SPI edge monitor"],
        "vplan_items": ["VP-SPI-001", "VP-SPI-002", "VP-SPI-015"],
    },
    {
        "dut": "citadel_spi",
        "coverage_type": "line",
        "line_range": "773-780",
        "module": "citadel_spi",
        "block": "segment_chaining_csaat",
        "severity": "medium",
        "difficulty": "medium",
        "root_cause": "Few multi-segment CSAAT chains are executed, limiting coverage of command pop and continuation logic.",
        "test_intent": "Run long CSAAT command chains and verify continuous chip-select behavior across segment boundaries.",
        "recommended_stimulus": [
            "Queue 3+ contiguous CSAAT segments",
            "Alternate TX-only and BIDIR segments",
            "Check chip-select continuity and byte counters",
        ],
        "dependencies": ["Segment-level transaction scoreboard"],
        "vplan_items": ["VP-SPI-010", "VP-SPI-016"],
    },
    {
        "dut": "aegis_aes",
        "coverage_type": "line",
        "line_range": "28-92",
        "module": "aegis_aes",
        "block": "sbox_forward_lookup_space",
        "severity": "critical",
        "difficulty": "hard",
        "root_cause": "A narrow plaintext/key corpus touches only a small subset of S-box indices, leaving most lookup arms unvisited.",
        "test_intent": "Use coverage-directed plaintext/key generation to maximize S-box input diversity during encryption rounds.",
        "recommended_stimulus": [
            "Run large randomized KAT campaign with diverse byte entropy",
            "Bias input generation toward unseen S-box indices",
            "Track per-byte substitution hit coverage",
        ],
        "dependencies": ["Functional coverage model for S-box index bins"],
        "vplan_items": ["VP-AES-001", "VP-AES-002", "VP-AES-015"],
    },
    {
        "dut": "aegis_aes",
        "coverage_type": "line",
        "line_range": "96-162",
        "module": "aegis_aes",
        "block": "sbox_inverse_lookup_space",
        "severity": "critical",
        "difficulty": "hard",
        "root_cause": "Decrypt-mode campaigns are minimal, so inverse S-box table arms remain broadly uncovered.",
        "test_intent": "Expand CBC/ECB decrypt regressions with randomized ciphertext/key sets to drive inverse substitution diversity.",
        "recommended_stimulus": [
            "Enable decrypt mode in both ECB and CBC",
            "Run randomized ciphertext suites with varying IVs",
            "Collect inverse S-box index hit distribution",
        ],
        "dependencies": ["Reference AES decrypt model in scoreboard"],
        "vplan_items": ["VP-AES-003", "VP-AES-004", "VP-AES-016"],
    },
    {
        "dut": "aegis_aes",
        "coverage_type": "line",
        "line_range": "530-546",
        "module": "aegis_aes",
        "block": "key_expansion_roundkey_cases",
        "severity": "high",
        "difficulty": "medium",
        "root_cause": "Short test runs often terminate before full key schedule progression, missing later key-expansion case arms.",
        "test_intent": "Drive full key expansion through all round-key indices and validate generated keys against software model.",
        "recommended_stimulus": [
            "Start operation and wait through complete key expansion",
            "Mirror expanded keys in software and compare",
            "Repeat for multiple random base keys",
        ],
        "dependencies": ["Round-key reference checker"],
        "vplan_items": ["VP-AES-006", "VP-AES-007", "VP-AES-017"],
    },
    {
        "dut": "aegis_aes",
        "coverage_type": "line",
        "line_range": "456-466",
        "module": "aegis_aes",
        "block": "cbc_iv_control_programming",
        "severity": "high",
        "difficulty": "medium",
        "root_cause": "Mode/op register permutations and IV update paths are under-tested, especially around CBC decrypt transitions.",
        "test_intent": "Exercise mode/op/control permutations and verify IV updates for CBC encrypt/decrypt across consecutive blocks.",
        "recommended_stimulus": [
            "Alternate ctrl_mode and ctrl_op between blocks",
            "Check IV chaining rules for encrypt and decrypt",
            "Validate key/data clear side-effects with STATUS reads",
        ],
        "dependencies": ["CBC chaining scoreboard support"],
        "vplan_items": ["VP-AES-010", "VP-AES-011", "VP-AES-018"],
    },
    {
        "dut": "sentinel_hmac",
        "coverage_type": "line",
        "line_range": "542-558",
        "module": "sentinel_hmac",
        "block": "sha_done_transition_mux",
        "severity": "critical",
        "difficulty": "hard",
        "root_cause": "Baseline tests do not fully combine pad-return flags with HMAC mode transitions, so done-state routing branches remain unhit.",
        "test_intent": "Create directed sequences for every ST_SHA_DONE_BLOCK return path (plain SHA, HMAC inner, HMAC outer).",
        "recommended_stimulus": [
            "Run SHA-only and HMAC flows with and without extra pad block",
            "Force each returning_from_* flag combination",
            "Check next-state transitions against expected FSM graph",
        ],
        "dependencies": ["FSM transition coverage collector"],
        "vplan_items": ["VP-HMAC-009", "VP-HMAC-010", "VP-HMAC-014"],
    },
    {
        "dut": "sentinel_hmac",
        "coverage_type": "line",
        "line_range": "730-741",
        "module": "sentinel_hmac",
        "block": "block_source_select_hmac_paths",
        "severity": "high",
        "difficulty": "medium",
        "root_cause": "HMAC-specific block source multiplexing (ipad/opad/outer/padlen) is not comprehensively traversed.",
        "test_intent": "Exercise all SHA block source selections and verify injected block contents for each HMAC stage.",
        "recommended_stimulus": [
            "Start HMAC flow with known key/message vectors",
            "Checkpoint w_reg preload source at each stage",
            "Compare staged blocks against software-constructed values",
        ],
        "dependencies": ["Internal stage probe or mirrored block model"],
        "vplan_items": ["VP-HMAC-004", "VP-HMAC-011", "VP-HMAC-016"],
    },
    {
        "dut": "sentinel_hmac",
        "coverage_type": "line",
        "line_range": "746-753",
        "module": "sentinel_hmac",
        "block": "sha_round_pipeline_update",
        "severity": "high",
        "difficulty": "hard",
        "root_cause": "Round pipeline updates are executed but not under varied enough data/control conditions to cover all update branches and shift scheduling.",
        "test_intent": "Stress SHA round pipeline with varied message block patterns and verify state register evolution per round.",
        "recommended_stimulus": [
            "Generate high-entropy and structured message blocks",
            "Record round-by-round a..h values for spot checks",
            "Verify W schedule update after round 15",
        ],
        "dependencies": ["Round-state reference trace checker"],
        "vplan_items": ["VP-HMAC-006", "VP-HMAC-007", "VP-HMAC-017"],
    },
    {
        "dut": "sentinel_hmac",
        "coverage_type": "line",
        "line_range": "307-315",
        "module": "sentinel_hmac",
        "block": "status_and_error_read_decode",
        "severity": "medium",
        "difficulty": "easy",
        "root_cause": "CSR negative accesses and extended status reads are not included, leaving decode default/error paths uncovered.",
        "test_intent": "Issue valid and invalid CSR reads during idle/busy states and validate returned data plus error flag behavior.",
        "recommended_stimulus": [
            "Read all status/digest addresses plus invalid offsets",
            "Toggle digest_swap/endian_swap and compare outputs",
            "Confirm tl_d_error_o behavior for bad accesses",
        ],
        "dependencies": ["CSR protocol checker for d_error expectations"],
        "vplan_items": ["VP-HMAC-001", "VP-HMAC-013"],
    },
    {
        "dut": "rampart_i2c",
        "coverage_type": "line",
        "line_range": "748-775",
        "module": "rampart_i2c",
        "block": "host_addr_shift_and_arbitration",
        "severity": "critical",
        "difficulty": "hard",
        "root_cause": "Single-host happy-path tests do not create arbitration-loss races during address bit drive/sample windows.",
        "test_intent": "Run multi-master contention scenarios to trigger host arbitration loss during address transmission.",
        "recommended_stimulus": [
            "Inject competing master pulls on SDA during HOST_ADDR_BYTE",
            "Vary contention bit positions and timing",
            "Check host_arb_lost and host state recovery to IDLE",
        ],
        "dependencies": ["Second-master bus contender model"],
        "vplan_items": ["VP-I2C-012", "VP-I2C-013", "VP-I2C-022"],
    },
    {
        "dut": "rampart_i2c",
        "coverage_type": "line",
        "line_range": "851-867",
        "module": "rampart_i2c",
        "block": "host_write_ack_command_chaining",
        "severity": "high",
        "difficulty": "medium",
        "root_cause": "ACK-driven command chaining through write->read/restart branches is only lightly exercised.",
        "test_intent": "Exercise write-ack branch fanout including restart, read-command follow-up, and additional write commands.",
        "recommended_stimulus": [
            "Queue mixed command FIFO patterns after each ACK",
            "Toggle NAKOK behavior and slave ACK responses",
            "Verify selected next state and FIFO pop behavior",
        ],
        "dependencies": ["Host command sequencer with branch expectations"],
        "vplan_items": ["VP-I2C-007", "VP-I2C-015", "VP-I2C-018"],
    },
    {
        "dut": "rampart_i2c",
        "coverage_type": "line",
        "line_range": "953-970",
        "module": "rampart_i2c",
        "block": "host_repeated_start_timing",
        "severity": "high",
        "difficulty": "medium",
        "root_cause": "Repeated-start timing path is under-covered because command sequences rarely chain restart immediately after prior transactions.",
        "test_intent": "Generate repeated-start command sequences and validate timing counters for tsu_sta/thd_sta transitions.",
        "recommended_stimulus": [
            "Drive restart commands with minimal inter-command spacing",
            "Check timing counter loads per RSTART_SETUP sub-phase",
            "Observe address phase entry after restart",
        ],
        "dependencies": ["Timing assertion helper for start/restart windows"],
        "vplan_items": ["VP-I2C-004", "VP-I2C-010", "VP-I2C-020"],
    },
    {
        "dut": "rampart_i2c",
        "coverage_type": "line",
        "line_range": "1205-1218",
        "module": "rampart_i2c",
        "block": "target_clock_stretch_release",
        "severity": "critical",
        "difficulty": "hard",
        "root_cause": "Target-mode stretch release depends on FIFO availability races that are not created by baseline target tests.",
        "test_intent": "Force target clock stretching and validate both release paths: TX data arrival and ACQ space availability.",
        "recommended_stimulus": [
            "Trigger TGT_STRETCH in read and write target transactions",
            "Delay TX FIFO refill and ACQ draining independently",
            "Check tgt_stretch_needed deassertion and state resume",
        ],
        "dependencies": ["Target traffic generator plus coordinated FIFO backpressure"],
        "vplan_items": ["VP-I2C-016", "VP-I2C-017", "VP-I2C-024"],
    },
]


def parse_range_len(line_range: str) -> int:
    if "-" in line_range:
        start_s, end_s = line_range.split("-", 1)
        start = int(start_s)
        end = int(end_s)
        return max(1, end - start + 1)
    return 1


def estimated_gain(gap: dict) -> str:
    sev = gap["severity"]
    if sev == "critical":
        return "6-10% line + branch in module"
    if sev == "high":
        return "4-7% line + branch in module"
    if sev == "medium":
        return "2-4% line in module"
    return "1-2% line in module"


def build_gap_records(summary: dict) -> list[dict]:
    gaps = []
    for idx, tmpl in enumerate(GAP_TEMPLATES, start=1):
        dut = tmpl["dut"]
        dut_cov = summary[dut]
        line_cov = dut_cov.get("line_coverage", 0.0) / 100.0
        record = {
            "id": f"GAP-{idx:03d}",
            "dut": dut,
            "coverage_type": tmpl["coverage_type"],
            "location": {
                "file": f"duts/{dut}/{dut}.sv",
                "line_range": tmpl["line_range"],
                "module": tmpl["module"],
                "block": tmpl["block"],
            },
            "metric": {
                "current_coverage": 0.0 if tmpl["coverage_type"] == "line" else round(line_cov, 2),
                "target_coverage": 0.85,
                "uncovered_items": parse_range_len(str(tmpl["line_range"])),
            },
            "severity": tmpl["severity"],
            "difficulty": tmpl["difficulty"],
            "root_cause": tmpl["root_cause"],
            "test_intent": tmpl["test_intent"],
            "recommended_stimulus": tmpl["recommended_stimulus"],
            "dependencies": tmpl["dependencies"],
            "vplan_items": tmpl["vplan_items"],
        }
        gaps.append(record)
    return gaps


def sort_priority(gaps: list[dict]) -> list[dict]:
    return sorted(
        gaps,
        key=lambda g: (
            -SEVERITY_ORDER[g["severity"]],
            -g["metric"]["uncovered_items"],
            DIFFICULTY_ORDER[g["difficulty"]],
            g["id"],
        ),
    )


def write_gap_analysis_yaml(gaps: list[dict]) -> None:
    payload = {"gaps": gaps}
    PRIMARY_GAP_YAML.write_text(yaml.safe_dump(payload, sort_keys=False, width=100), encoding="utf-8")


def write_gap_summary_md(summary: dict, gaps: list[dict], ranked: list[dict]) -> None:
    lines = []
    lines.append("# Gap Summary")
    lines.append("")
    lines.append("## Per-DUT Coverage Snapshot")
    lines.append("")
    lines.append("| DUT | Line % | Target Line % | Branch % | Target Branch % |")
    lines.append("|-----|--------|---------------|----------|------------------|")
    for dut, row in summary.items():
        lines.append(
            f"| {dut} | {row['line_coverage']:.2f} | {TARGET_LINE:.2f} | {row['branch_coverage']:.2f} | {TARGET_BRANCH:.2f} |"
        )

    lines.append("")
    lines.append("## Top 10 Gaps By Severity")
    lines.append("")
    lines.append("| Rank | Gap ID | DUT | Block | Severity | Difficulty | Range |")
    lines.append("|------|--------|-----|-------|----------|------------|-------|")
    for rank, gap in enumerate(ranked[:10], start=1):
        lines.append(
            f"| {rank} | {gap['id']} | {gap['dut']} | {gap['location']['block']} | {gap['severity']} | {gap['difficulty']} | {gap['location']['line_range']} |"
        )

    lines.append("")
    lines.append("## Coverage Heat Map")
    lines.append("")
    lines.append("| DUT | Uncovered Lines | Worst Region | Rationale |")
    lines.append("|-----|------------------|--------------|-----------|")
    for dut, row in sorted(summary.items(), key=lambda x: x[1]["line_total"] - x[1]["line_hit"], reverse=True):
        unc = row["line_total"] - row["line_hit"]
        worst = row["top_uncovered"][0]["ranges"][0] if row["top_uncovered"] and row["top_uncovered"][0]["ranges"] else "n/a"
        reason = "Control-path mode combinations under-tested"
        if dut == "aegis_aes":
            reason = "Lookup-table and key schedule diversity is limited"
        elif dut == "rampart_i2c":
            reason = "Protocol corner-state transitions need adversarial bus timing"
        elif dut == "sentinel_hmac":
            reason = "HMAC multi-stage FSM paths are only partially traversed"
        lines.append(f"| {dut} | {unc} | {worst} | {reason} |")

    counts: dict[str, int] = defaultdict(int)
    for gap in gaps:
        counts[gap["difficulty"]] += 1

    lines.append("")
    lines.append("## Effort Estimation")
    lines.append("")
    lines.append("| Bucket | Gap Count | Typical Work |")
    lines.append("|--------|-----------|--------------|")
    lines.append(f"| easy | {counts['easy']} | Directed CSR stimuli and simple protocol permutations |")
    lines.append(f"| medium | {counts['medium']} | New constrained sequences with scoreboard extensions |")
    lines.append(f"| hard | {counts['hard']} | Timing-sensitive scenarios and deeper protocol modeling |")
    lines.append(f"| very_hard | {counts['very_hard']} | Architectural corner modeling and cross-agent orchestration |")

    PRIMARY_SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_closure_plan_md(gaps: list[dict], ranked: list[dict]) -> None:
    by_id = {g["id"]: g for g in gaps}
    quick = [g for g in ranked if g["difficulty"] == "easy"]
    moderate = [g for g in ranked if g["difficulty"] == "medium"]
    hard = [g for g in ranked if g["difficulty"] in {"hard", "very_hard"}]

    lines = []
    lines.append("# Prioritized Closure Plan")
    lines.append("")
    lines.append("## Quick Wins")
    lines.append("")
    for g in quick[:10]:
        lines.append(f"- {g['id']} ({g['dut']}): {g['location']['block']} -> {g['test_intent']}")

    lines.append("")
    lines.append("## Moderate Effort")
    lines.append("")
    for g in moderate[:10]:
        lines.append(f"- {g['id']} ({g['dut']}): {g['location']['block']} -> {g['test_intent']}")

    lines.append("")
    lines.append("## Hard Targets")
    lines.append("")
    for g in hard[:12]:
        lines.append(f"- {g['id']} ({g['dut']}): {g['location']['block']} -> {g['test_intent']}")

    lines.append("")
    lines.append("## Dependency Map")
    lines.append("")
    lines.append(f"- {by_id['GAP-017']['id']} depends on functional coverage bins for S-box index diversity.")
    lines.append(f"- {by_id['GAP-025']['id']} depends on a second-master contention model.")
    lines.append(f"- {by_id['GAP-021']['id']} depends on FSM transition instrumentation across HMAC return paths.")
    lines.append(f"- {by_id['GAP-004']['id']} depends on timing-check monitor support for stop-bit counting.")
    lines.append(f"- {by_id['GAP-011']['id']} depends on 64-bit timer rollover stimulus helper.")

    lines.append("")
    lines.append("## Execution Order")
    lines.append("")
    lines.append("1. Close all easy gaps first to lift baseline quickly and stabilize infrastructure.")
    lines.append("2. Address medium gaps by extending existing drivers/sequences with mode permutations.")
    lines.append("3. Tackle hard gaps last with dedicated protocol stress agents and model enhancements.")

    PRIMARY_PLAN_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_compat_per_dut(summary: dict, gaps: list[dict]) -> None:
    COMPAT_GAP_DIR.mkdir(parents=True, exist_ok=True)
    by_dut = defaultdict(list)
    for gap in gaps:
        by_dut[gap["dut"]].append(gap)

    for dut, d_gaps in by_dut.items():
        row = summary[dut]
        lines = []
        lines.append(f"# {dut} Coverage Gaps")
        lines.append("")
        lines.append("## Coverage Snapshot")
        lines.append("")
        lines.append(f"- Line coverage: {row['line_coverage']:.2f}%")
        lines.append(f"- Branch coverage: {row['branch_coverage']:.2f}%")
        lines.append("")
        lines.append("## Uncovered Code Regions")
        lines.append("")
        lines.append("| Gap ID | File | Line Range | Reason Uncovered |")
        lines.append("|--------|------|------------|------------------|")
        for g in d_gaps:
            lines.append(
                f"| {g['id']} | {g['location']['file']} | {g['location']['line_range']} | {g['root_cause']} |"
            )

        lines.append("")
        lines.append("## Unhit Functional Coverage Bins (Estimated From VPlan)")
        lines.append("")
        lines.append("| Gap ID | Coverpoint | Bin Name | Required Stimulus |")
        lines.append("|--------|------------|----------|-------------------|")
        for g in d_gaps:
            vp = ", ".join(g["vplan_items"])
            lines.append(f"| {g['id']} | vp_scenario_id | {vp} | {g['test_intent']} |")

        lines.append("")
        lines.append("## Root Cause And Intent")
        lines.append("")
        for g in d_gaps:
            lines.append(f"### {g['id']} - {g['location']['block']}")
            lines.append(f"- Root cause: {g['root_cause']}")
            lines.append(f"- Test intent: {g['test_intent']}")
            lines.append("")

        (COMPAT_GAP_DIR / f"{dut}_gaps.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_compat_summary(summary: dict, ranked: list[dict]) -> None:
    lines = []
    lines.append("# Task 2.1 Executive Summary")
    lines.append("")
    lines.append("This report consolidates gap analysis across all seven DUTs and maps each gap to actionable stimulus intent.")
    lines.append("")
    lines.append("## Highest Priority Gaps")
    lines.append("")
    for g in ranked[:12]:
        lines.append(f"- {g['id']} ({g['dut']}): {g['location']['block']} [{g['severity']}, {g['difficulty']}]")
    lines.append("")
    lines.append("## Coverage Baseline")
    lines.append("")
    lines.append("| DUT | Line % | Branch % |")
    lines.append("|-----|--------|----------|")
    for dut, row in summary.items():
        lines.append(f"| {dut} | {row['line_coverage']:.2f} | {row['branch_coverage']:.2f} |")

    COMPAT_SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_priority_table(ranked: list[dict]) -> None:
    priorities = []
    for rank, g in enumerate(ranked, start=1):
        priorities.append(
            {
                "rank": rank,
                "dut": g["dut"],
                "gap": f"{g['id']}:{g['location']['block']}",
                "severity": g["severity"],
                "difficulty": g["difficulty"],
                "estimated_coverage_gain": estimated_gain(g),
                "test_intent": g["test_intent"],
            }
        )

    payload = {"priorities": priorities}
    COMPAT_PRIORITY_YAML.write_text(yaml.safe_dump(payload, sort_keys=False, width=100), encoding="utf-8")


def main() -> int:
    if not SUMMARY_JSON.exists():
        raise FileNotFoundError(f"Missing coverage summary: {SUMMARY_JSON}")

    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    gaps = build_gap_records(summary)
    ranked = sort_priority(gaps)

    write_gap_analysis_yaml(gaps)
    write_gap_summary_md(summary, gaps, ranked)
    write_closure_plan_md(gaps, ranked)

    write_compat_per_dut(summary, gaps)
    write_compat_summary(summary, ranked)
    write_priority_table(ranked)

    print(f"Generated {len(gaps)} gaps at {datetime.now(timezone.utc).isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
