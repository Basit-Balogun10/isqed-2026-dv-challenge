#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

ORIGIN_URL="$(git remote get-url origin 2>/dev/null || true)"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"
REPO_PATH=""

if [[ "$ORIGIN_URL" =~ ^git@github.com:(.+)\.git$ ]]; then
  REPO_PATH="${BASH_REMATCH[1]}"
elif [[ "$ORIGIN_URL" =~ ^https://github.com/(.+)\.git$ ]]; then
  REPO_PATH="${BASH_REMATCH[1]}"
elif [[ "$ORIGIN_URL" =~ ^https://github.com/(.+)$ ]]; then
  REPO_PATH="${BASH_REMATCH[1]}"
fi

if [[ -n "$REPO_PATH" ]]; then
  MASTER_TASK11_URL="https://github.com/${REPO_PATH}/blob/${BRANCH}/submissions/task-1.1/prompts.md"
  MASTER_TASK12_URL="https://github.com/${REPO_PATH}/blob/${BRANCH}/submissions/task-1.2/prompts.md"
  MASTER_TASK13_URL="https://github.com/${REPO_PATH}/blob/${BRANCH}/submissions/task-1.3/prompts.md"
  MASTER_TASK14_URL="https://github.com/${REPO_PATH}/blob/${BRANCH}/submissions/task-1.4/prompts.md"
  MASTER_TASK22_URL="https://github.com/${REPO_PATH}/blob/${BRANCH}/submissions/task-2.2/prompts.md"
  MASTER_TASK23_URL="https://github.com/${REPO_PATH}/blob/${BRANCH}/submissions/task-2.3/prompts.md"
  MASTER_TASK31_URL="https://github.com/${REPO_PATH}/blob/${BRANCH}/submissions/task-3.1/prompts.md"
  MASTER_TASK32_URL="https://github.com/${REPO_PATH}/blob/${BRANCH}/submissions/task-3.2/prompts.md"
  MASTER_TASK33_URL="https://github.com/${REPO_PATH}/blob/${BRANCH}/submissions/task-3.3/prompts.md"
else
  MASTER_TASK11_URL="(unable to derive from origin remote)"
  MASTER_TASK12_URL="(unable to derive from origin remote)"
  MASTER_TASK13_URL="(unable to derive from origin remote)"
  MASTER_TASK14_URL="(unable to derive from origin remote)"
  MASTER_TASK22_URL="(unable to derive from origin remote)"
  MASTER_TASK23_URL="(unable to derive from origin remote)"
  MASTER_TASK31_URL="(unable to derive from origin remote)"
  MASTER_TASK32_URL="(unable to derive from origin remote)"
  MASTER_TASK33_URL="(unable to derive from origin remote)"
fi

TMP11="/tmp/task11-prompt-chunks"
TMP12="/tmp/task12-prompt-chunks"
TMP13="/tmp/task13-prompt-chunks"
TMP14="/tmp/task14-prompt-chunks"
TMP22="/tmp/task22-prompt-chunks"
TMP23="/tmp/task23-prompt-chunks"
TMP31="/tmp/task31-prompt-chunks"
TMP32="/tmp/task32-prompt-chunks"
TMP33="/tmp/task33-prompt-chunks"
rm -rf "$TMP11" "$TMP12" "$TMP13" "$TMP14" "$TMP22" "$TMP23" "$TMP31" "$TMP32" "$TMP33"
mkdir -p "$TMP11/raw" "$TMP12/raw" "$TMP13/raw" "$TMP14/raw" "$TMP22/raw" "$TMP23/raw" "$TMP31/raw" "$TMP32/raw" "$TMP33/raw"

# Split full transcripts into six readable chunks each.
split -l 1500 -d -a 2 submissions/task-1.1/prompts.md "$TMP11/raw/chunk_"
split -l 2300 -d -a 2 submissions/task-1.2/prompts.md "$TMP12/raw/chunk_"
split -l 350 -d -a 2 submissions/task-1.3/prompts.md "$TMP13/raw/chunk_"

# Task 1.4 uses dynamic chunk sizing to guarantee six equally distributed chunks.
TASK14_LINES="$(wc -l < submissions/task-1.4/prompts.md)"
TASK14_CHUNK_SIZE=$(( (TASK14_LINES + 5) / 6 ))
split -l "$TASK14_CHUNK_SIZE" -d -a 2 submissions/task-1.4/prompts.md "$TMP14/raw/chunk_"
for i in 00 01 02 03 04 05; do
  [[ -f "$TMP14/raw/chunk_${i}" ]] || : > "$TMP14/raw/chunk_${i}"
done

# Task 2.2 dynamic chunking into six segments.
TASK22_LINES="$(wc -l < submissions/task-2.2/prompts.md)"
TASK22_CHUNK_SIZE=$(( (TASK22_LINES + 5) / 6 ))
split -l "$TASK22_CHUNK_SIZE" -d -a 2 submissions/task-2.2/prompts.md "$TMP22/raw/chunk_"
for i in 00 01 02 03 04 05; do
  [[ -f "$TMP22/raw/chunk_${i}" ]] || : > "$TMP22/raw/chunk_${i}"
done

# Task 2.3 dynamic chunking into six segments.
TASK23_LINES="$(wc -l < submissions/task-2.3/prompts.md)"
TASK23_CHUNK_SIZE=$(( (TASK23_LINES + 5) / 6 ))
split -l "$TASK23_CHUNK_SIZE" -d -a 2 submissions/task-2.3/prompts.md "$TMP23/raw/chunk_"
for i in 00 01 02 03 04 05; do
  [[ -f "$TMP23/raw/chunk_${i}" ]] || : > "$TMP23/raw/chunk_${i}"
done

# Task 3.1 dynamic chunking into six segments.
TASK31_LINES="$(wc -l < submissions/task-3.1/prompts.md)"
TASK31_CHUNK_SIZE=$(( (TASK31_LINES + 5) / 6 ))
split -l "$TASK31_CHUNK_SIZE" -d -a 2 submissions/task-3.1/prompts.md "$TMP31/raw/chunk_"
for i in 00 01 02 03 04 05; do
  [[ -f "$TMP31/raw/chunk_${i}" ]] || : > "$TMP31/raw/chunk_${i}"
done

# Task 3.2 dynamic chunking into six segments.
TASK32_LINES="$(wc -l < submissions/task-3.2/prompts.md)"
TASK32_CHUNK_SIZE=$(( (TASK32_LINES + 5) / 6 ))
split -l "$TASK32_CHUNK_SIZE" -d -a 2 submissions/task-3.2/prompts.md "$TMP32/raw/chunk_"
for i in 00 01 02 03 04 05; do
  [[ -f "$TMP32/raw/chunk_${i}" ]] || : > "$TMP32/raw/chunk_${i}"
done

# Task 3.3 dynamic chunking into six segments.
TASK33_LINES="$(wc -l < submissions/task-3.3/prompts.md)"
TASK33_CHUNK_SIZE=$(( (TASK33_LINES + 5) / 6 ))
split -l "$TASK33_CHUNK_SIZE" -d -a 2 submissions/task-3.3/prompts.md "$TMP33/raw/chunk_"
for i in 00 01 02 03 04 05; do
  [[ -f "$TMP33/raw/chunk_${i}" ]] || : > "$TMP33/raw/chunk_${i}"
done

# Task 1.1 chunk labels.
cp "$TMP11/raw/chunk_00" "$TMP11/01_beginning_and_context_discovery.md"
cp "$TMP11/raw/chunk_01" "$TMP11/02_agent_setup_and_instruction_tuning.md"
cp "$TMP11/raw/chunk_02" "$TMP11/03_task11_buildout_and_rework.md"
cp "$TMP11/raw/chunk_03" "$TMP11/04_compliance_alignment_and_fixes.md"
cp "$TMP11/raw/chunk_04" "$TMP11/05_dual_sim_validation_and_packaging.md"
cp "$TMP11/raw/chunk_05" "$TMP11/06_final_audits_and_handoffs.md"

cat > "$TMP11/README.md" <<EOF
# Prompt Evidence Index - Task 1.1

This directory contains the full contents of submissions/task-1.1/prompts.md,
split into six files for easier judge navigation.

Master/original transcript source:
- submissions/task-1.1/prompts.md
- ${MASTER_TASK11_URL}

Why the original file is not duplicated here:
- These six chunk files already contain the entire transcript content.
- Avoiding a second full copy keeps submission payloads minimal.

1. 01_beginning_and_context_discovery.md
2. 02_agent_setup_and_instruction_tuning.md
3. 03_task11_buildout_and_rework.md
4. 04_compliance_alignment_and_fixes.md
5. 05_dual_sim_validation_and_packaging.md
6. 06_final_audits_and_handoffs.md
EOF

# Task 1.2 chunk labels.
cp "$TMP12/raw/chunk_00" "$TMP12/01_task12_kickoff_and_scoping.md"
cp "$TMP12/raw/chunk_01" "$TMP12/02_generation_pipeline_and_scaffolding.md"
cp "$TMP12/raw/chunk_02" "$TMP12/03_execution_runs_and_initial_packaging.md"
cp "$TMP12/raw/chunk_03" "$TMP12/04_requirement_audit_and_gap_closure.md"
cp "$TMP12/raw/chunk_04" "$TMP12/05_prompt_evidence_and_script_hardening.md"
cp "$TMP12/raw/chunk_05" "$TMP12/06_final_checklists_and_scaling.md"

cat > "$TMP12/README.md" <<EOF
# Prompt Evidence Index - Task 1.2

This directory contains the full contents of submissions/task-1.2/prompts.md,
split into six files for easier judge navigation.

Master/original transcript source:
- submissions/task-1.2/prompts.md
- ${MASTER_TASK12_URL}

Why the original file is not duplicated here:
- These six chunk files already contain the entire transcript content.
- Avoiding a second full copy keeps submission payloads minimal.

1. 01_task12_kickoff_and_scoping.md
2. 02_generation_pipeline_and_scaffolding.md
3. 03_execution_runs_and_initial_packaging.md
4. 04_requirement_audit_and_gap_closure.md
5. 05_prompt_evidence_and_script_hardening.md
6. 06_final_checklists_and_scaling.md
EOF

# Task 1.3 chunk labels.
cp "$TMP13/raw/chunk_00" "$TMP13/01_task13_kickoff_and_scope.md"
cp "$TMP13/raw/chunk_01" "$TMP13/02_baseline_implementation.md"
cp "$TMP13/raw/chunk_02" "$TMP13/03_failure_analysis_and_debug.md"
cp "$TMP13/raw/chunk_03" "$TMP13/04_remediation_and_matrix_reruns.md"
cp "$TMP13/raw/chunk_04" "$TMP13/05_readiness_validation.md"
cp "$TMP13/raw/chunk_05" "$TMP13/06_final_questions_and_signoff.md"

cat > "$TMP13/README.md" <<EOF
# Prompt Evidence Index - Task 1.3

This directory contains the full contents of submissions/task-1.3/prompts.md,
split into six files for easier judge navigation.

Master/original transcript source:
- submissions/task-1.3/prompts.md
- ${MASTER_TASK13_URL}

Why the original file is not duplicated here:
- These six chunk files already contain the entire transcript content.
- Avoiding a second full copy keeps submission payloads minimal.

1. 01_task13_kickoff_and_scope.md
2. 02_baseline_implementation.md
3. 03_failure_analysis_and_debug.md
4. 04_remediation_and_matrix_reruns.md
5. 05_readiness_validation.md
6. 06_final_questions_and_signoff.md
EOF

# Task 1.4 chunk labels.
cp "$TMP14/raw/chunk_00" "$TMP14/01_task14_audit_and_planning.md"
cp "$TMP14/raw/chunk_01" "$TMP14/02_scaffolding_and_initial_assertions.md"
cp "$TMP14/raw/chunk_02" "$TMP14/03_simulator_compatibility_rework.md"
cp "$TMP14/raw/chunk_03" "$TMP14/04_temporal_debug_and_dual_sim_pass.md"
cp "$TMP14/raw/chunk_04" "$TMP14/05_packaging_and_readiness_automation.md"
cp "$TMP14/raw/chunk_05" "$TMP14/06_final_verification_and_signoff.md"

cat > "$TMP14/README.md" <<EOF
# Prompt Evidence Index - Task 1.4

This directory contains the full contents of submissions/task-1.4/prompts.md,
split into six files for easier judge navigation.

Master/original transcript source:
- submissions/task-1.4/prompts.md
- ${MASTER_TASK14_URL}

Why the original file is not duplicated here:
- These six chunk files already contain the entire transcript content.
- Avoiding a second full copy keeps submission payloads minimal.

1. 01_task14_audit_and_planning.md
2. 02_scaffolding_and_initial_assertions.md
3. 03_simulator_compatibility_rework.md
4. 04_temporal_debug_and_dual_sim_pass.md
5. 05_packaging_and_readiness_automation.md
6. 06_final_verification_and_signoff.md
EOF

# Task 2.2 chunk labels.
cp "$TMP22/raw/chunk_00" "$TMP22/01_task22_audit_and_planning.md"
cp "$TMP22/raw/chunk_01" "$TMP22/02_stimulus_scaffolding_and_baseline_split.md"
cp "$TMP22/raw/chunk_02" "$TMP22/03_coverage_execution_and_makefile_alignment.md"
cp "$TMP22/raw/chunk_03" "$TMP22/04_gap_closure_and_debug_iterations.md"
cp "$TMP22/raw/chunk_04" "$TMP22/05_packaging_and_readiness_automation.md"
cp "$TMP22/raw/chunk_05" "$TMP22/06_final_audit_and_submission_signoff.md"

cat > "$TMP22/README.md" <<EOF
# Prompt Evidence Index - Task 2.2

This directory contains the full contents of submissions/task-2.2/prompts.md,
split into six files for easier judge navigation.

Master/original transcript source:
- submissions/task-2.2/prompts.md
- ${MASTER_TASK22_URL}

Why the original file is not duplicated here:
- These six chunk files already contain the entire transcript content.
- Avoiding a second full copy keeps submission payloads minimal.

1. 01_task22_audit_and_planning.md
2. 02_stimulus_scaffolding_and_baseline_split.md
3. 03_coverage_execution_and_makefile_alignment.md
4. 04_gap_closure_and_debug_iterations.md
5. 05_packaging_and_readiness_automation.md
6. 06_final_audit_and_submission_signoff.md
EOF

# Task 2.3 chunk labels.
cp "$TMP23/raw/chunk_00" "$TMP23/01_task23_audit_and_requirements.md"
cp "$TMP23/raw/chunk_01" "$TMP23/02_strategy_selection_b_plus_c.md"
cp "$TMP23/raw/chunk_02" "$TMP23/03_cdg_architecture_and_interfaces.md"
cp "$TMP23/raw/chunk_03" "$TMP23/04_loop_execution_and_coverage_parsing.md"
cp "$TMP23/raw/chunk_04" "$TMP23/05_packaging_and_compliance_automation.md"
cp "$TMP23/raw/chunk_05" "$TMP23/06_validation_and_signoff.md"

cat > "$TMP23/README.md" <<EOF
# Prompt Evidence Index - Task 2.3

This directory contains the full contents of submissions/task-2.3/prompts.md,
split into six files for easier judge navigation.

Master/original transcript source:
- submissions/task-2.3/prompts.md
- ${MASTER_TASK23_URL}

Why the original file is not duplicated here:
- These six chunk files already contain the entire transcript content.
- Avoiding a second full copy keeps submission payloads minimal.

1. 01_task23_audit_and_requirements.md
2. 02_strategy_selection_b_plus_c.md
3. 03_cdg_architecture_and_interfaces.md
4. 04_loop_execution_and_coverage_parsing.md
5. 05_packaging_and_compliance_automation.md
6. 06_validation_and_signoff.md
EOF

# Task 3.1 chunk labels.
cp "$TMP31/raw/chunk_00" "$TMP31/01_task31_audit_and_requirements.md"
cp "$TMP31/raw/chunk_01" "$TMP31/02_log_taxonomy_and_triage_strategy.md"
cp "$TMP31/raw/chunk_02" "$TMP31/03_root_cause_mapping_and_classification.md"
cp "$TMP31/raw/chunk_03" "$TMP31/04_yaml_authoring_and_evidence_binding.md"
cp "$TMP31/raw/chunk_04" "$TMP31/05_packaging_and_readiness_automation.md"
cp "$TMP31/raw/chunk_05" "$TMP31/06_final_validation_and_signoff.md"

cat > "$TMP31/README.md" <<EOF
# Prompt Evidence Index - Task 3.1

This directory contains the full contents of submissions/task-3.1/prompts.md,
split into six files for easier judge navigation.

Master/original transcript source:
- submissions/task-3.1/prompts.md
- ${MASTER_TASK31_URL}

Why the original file is not duplicated here:
- These six chunk files already contain the entire transcript content.
- Avoiding a second full copy keeps submission payloads minimal.

1. 01_task31_audit_and_requirements.md
2. 02_log_taxonomy_and_triage_strategy.md
3. 03_root_cause_mapping_and_classification.md
4. 04_yaml_authoring_and_evidence_binding.md
5. 05_packaging_and_readiness_automation.md
6. 06_final_validation_and_signoff.md
EOF

# Task 3.2 chunk labels.
cp "$TMP32/raw/chunk_00" "$TMP32/01_task32_audit_and_requirements.md"
cp "$TMP32/raw/chunk_01" "$TMP32/02_trace_inventory_and_signal_windows.md"
cp "$TMP32/raw/chunk_02" "$TMP32/03_root_cause_mapping_and_cycle_alignment.md"
cp "$TMP32/raw/chunk_03" "$TMP32/04_reproduction_test_authoring.md"
cp "$TMP32/raw/chunk_04" "$TMP32/05_packaging_and_readiness_automation.md"
cp "$TMP32/raw/chunk_05" "$TMP32/06_final_validation_and_signoff.md"

cat > "$TMP32/README.md" <<EOF
# Prompt Evidence Index - Task 3.2

This directory contains the full contents of submissions/task-3.2/prompts.md,
split into six files for easier judge navigation.

Master/original transcript source:
- submissions/task-3.2/prompts.md
- ${MASTER_TASK32_URL}

Why the original file is not duplicated here:
- These six chunk files already contain the entire transcript content.
- Avoiding a second full copy keeps submission payloads minimal.

1. 01_task32_audit_and_requirements.md
2. 02_trace_inventory_and_signal_windows.md
3. 03_root_cause_mapping_and_cycle_alignment.md
4. 04_reproduction_test_authoring.md
5. 05_packaging_and_readiness_automation.md
6. 06_final_validation_and_signoff.md
EOF

# Task 3.3 chunk labels.
cp "$TMP33/raw/chunk_00" "$TMP33/01_task33_audit_and_requirements.md"
cp "$TMP33/raw/chunk_01" "$TMP33/02_input_inventory_and_failure_taxonomy.md"
cp "$TMP33/raw/chunk_02" "$TMP33/03_bucketing_and_root_cause_mapping.md"
cp "$TMP33/raw/chunk_03" "$TMP33/04_priority_and_patch_validation.md"
cp "$TMP33/raw/chunk_04" "$TMP33/05_packaging_and_readiness_automation.md"
cp "$TMP33/raw/chunk_05" "$TMP33/06_final_validation_and_signoff.md"

cat > "$TMP33/README.md" <<EOF
# Prompt Evidence Index - Task 3.3

This directory contains the full contents of submissions/task-3.3/prompts.md,
split into six files for easier judge navigation.

Master/original transcript source:
- submissions/task-3.3/prompts.md
- ${MASTER_TASK33_URL}

Why the original file is not duplicated here:
- These six chunk files already contain the entire transcript content.
- Avoiding a second full copy keeps submission payloads minimal.

1. 01_task33_audit_and_requirements.md
2. 02_input_inventory_and_failure_taxonomy.md
3. 03_bucketing_and_root_cause_mapping.md
4. 04_priority_and_patch_validation.md
5. 05_packaging_and_readiness_automation.md
6. 06_final_validation_and_signoff.md
EOF

# Replace prompts for all Task 1.1 DUT submissions.
for dut in aegis_aes rampart_i2c sentinel_hmac; do
  dst="submissions/task-1.1/submission-1.1-${dut}/prompts"
  mkdir -p "$dst"
  find "$dst" -mindepth 1 -maxdepth 1 -type f -delete
  cp "$TMP11"/*.md "$dst"/
done

# Replace prompts for all Task 1.2 DUT submissions.
for dut in aegis_aes rampart_i2c sentinel_hmac; do
  dst="submissions/task-1.2/submission-1.2-${dut}/prompts"
  mkdir -p "$dst"
  find "$dst" -mindepth 1 -maxdepth 1 -type f -delete
  cp "$TMP12"/*.md "$dst"/
done

# Replace prompts for Task 1.3 submission.
dst="submissions/task-1.3/submission-1.3/prompts"
mkdir -p "$dst"
find "$dst" -mindepth 1 -maxdepth 1 -type f -delete
cp "$TMP13"/*.md "$dst"/

# Replace prompts for all Task 1.4 DUT submissions.
for dut in rampart_i2c sentinel_hmac; do
  dst="submissions/task-1.4/submission-1.4-${dut}/prompts"
  mkdir -p "$dst"
  find "$dst" -mindepth 1 -maxdepth 1 -type f -delete
  cp "$TMP14"/*.md "$dst"/
done

# Replace prompts for all Task 2.2 DUT submissions.
for dut in aegis_aes sentinel_hmac rampart_i2c warden_timer; do
  dst="submissions/task-2.2/submission-2.2-${dut}/prompts"
  mkdir -p "$dst"
  find "$dst" -mindepth 1 -maxdepth 1 -type f -delete
  cp "$TMP22"/*.md "$dst"/
done

# Replace prompts for Task 2.3 submission.
dst="submissions/task-2.3/submission-2.3/prompts"
mkdir -p "$dst"
find "$dst" -mindepth 1 -maxdepth 1 -type f -delete
cp "$TMP23"/*.md "$dst"/

# Replace prompts for Task 3.1 submission.
dst="submissions/task-3.1/submission-3.1/prompts"
mkdir -p "$dst"
find "$dst" -mindepth 1 -maxdepth 1 -type f -delete
cp "$TMP31"/*.md "$dst"/

# Replace prompts for Task 3.2 submission.
dst="submissions/task-3.2/submission-3.2/prompts"
mkdir -p "$dst"
find "$dst" -mindepth 1 -maxdepth 1 -type f -delete
cp "$TMP32"/*.md "$dst"/

# Replace prompts for Task 3.3 submission.
dst="submissions/task-3.3/submission-3.3/prompts"
mkdir -p "$dst"
find "$dst" -mindepth 1 -maxdepth 1 -type f -delete
cp "$TMP33"/*.md "$dst"/

echo "Prompt evidence regenerated for Task 1.1, Task 1.2, Task 1.3, Task 1.4, Task 2.2, Task 2.3, Task 3.1, Task 3.2, and Task 3.3 submissions."
