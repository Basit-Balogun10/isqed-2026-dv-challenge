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
else
  MASTER_TASK11_URL="(unable to derive from origin remote)"
  MASTER_TASK12_URL="(unable to derive from origin remote)"
fi

TMP11="/tmp/task11-prompt-chunks"
TMP12="/tmp/task12-prompt-chunks"
rm -rf "$TMP11" "$TMP12"
mkdir -p "$TMP11/raw" "$TMP12/raw"

# Split full transcripts into six readable chunks each.
split -l 1500 -d -a 2 submissions/task-1.1/prompts.md "$TMP11/raw/chunk_"
split -l 2300 -d -a 2 submissions/task-1.2/prompts.md "$TMP12/raw/chunk_"

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

echo "Prompt evidence regenerated for all Task 1.1 and Task 1.2 DUT submissions."
