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
else
  MASTER_TASK11_URL="(unable to derive from origin remote)"
  MASTER_TASK12_URL="(unable to derive from origin remote)"
  MASTER_TASK13_URL="(unable to derive from origin remote)"
  MASTER_TASK14_URL="(unable to derive from origin remote)"
  MASTER_TASK22_URL="(unable to derive from origin remote)"
fi

TMP11="/tmp/task11-prompt-chunks"
TMP12="/tmp/task12-prompt-chunks"
TMP13="/tmp/task13-prompt-chunks"
TMP14="/tmp/task14-prompt-chunks"
TMP22="/tmp/task22-prompt-chunks"
rm -rf "$TMP11" "$TMP12" "$TMP13" "$TMP14" "$TMP22"
mkdir -p "$TMP11/raw" "$TMP12/raw" "$TMP13/raw" "$TMP14/raw" "$TMP22/raw"

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

echo "Prompt evidence regenerated for Task 1.1, Task 1.2, Task 1.3, Task 1.4, and Task 2.2 submissions."
