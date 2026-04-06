#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUB_DIR="${ROOT_DIR}/submissions/task-4.1/submission-4.1"

if [[ ! -d "${SUB_DIR}" ]]; then
  echo "[FAIL] Missing submission directory: ${SUB_DIR}" >&2
  exit 1
fi

PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python3"
fi

echo "[INFO] Checking required submission files"
required=(
  "${SUB_DIR}/agent/run_agent.py"
  "${SUB_DIR}/agent/agent_config.yaml"
  "${SUB_DIR}/agent/src"
  "${SUB_DIR}/methodology.md"
  "${SUB_DIR}/README.md"
  "${SUB_DIR}/metadata.yaml"
  "${SUB_DIR}/Makefile"
)

for f in "${required[@]}"; do
  if [[ ! -e "${f}" ]]; then
    echo "[FAIL] Missing required item: ${f}" >&2
    exit 1
  fi
  echo "[PASS] ${f}"
done

echo "[INFO] Checking prompt evidence payload"
if [[ ! -d "${SUB_DIR}/prompts" ]]; then
  echo "[FAIL] Missing prompts directory: ${SUB_DIR}/prompts" >&2
  exit 1
fi

expected_prompt_files=(
  "README.md"
  "01_task41_audit_and_requirements.md"
  "02_hosted_api_design_and_scaffold.md"
  "03_orchestrator_build_and_debugging.md"
  "04_full_compliance_audits_and_fixes.md"
  "05_readiness_validation_and_packaging.md"
  "06_prompt_restructure_and_signoff.md"
)

for prompt_file in "${expected_prompt_files[@]}"; do
  if [[ ! -f "${SUB_DIR}/prompts/${prompt_file}" ]]; then
    echo "[FAIL] Missing prompt evidence file: ${SUB_DIR}/prompts/${prompt_file}" >&2
    exit 1
  fi
  echo "[PASS] prompts/${prompt_file}"
done

prompt_count=$(find "${SUB_DIR}/prompts" -maxdepth 1 -type f -name "*.md" | wc -l | tr -d ' ')
if [[ "${prompt_count}" -lt 7 ]]; then
  echo "[FAIL] prompts/ must contain at least 7 markdown evidence files; found ${prompt_count}" >&2
  exit 1
fi
echo "[PASS] prompts markdown files: ${prompt_count}"

echo "[INFO] Checking Makefile targets"
for target in compile simulate coverage run_agent clean; do
  if ! grep -q "^${target}:" "${SUB_DIR}/Makefile"; then
    echo "[FAIL] Makefile missing target: ${target}" >&2
    exit 1
  fi
  echo "[PASS] target ${target}"
done

echo "[INFO] Checking CLI interface"
"${PYTHON_BIN}" "${SUB_DIR}/agent/run_agent.py" --help >/dev/null
echo "[PASS] run_agent.py --help"

echo "[INFO] Checking simulator CLI options"
if ! "${PYTHON_BIN}" "${SUB_DIR}/agent/run_agent.py" --help | grep -q -- "--simulator"; then
  echo "[FAIL] run_agent.py --help does not expose --simulator option" >&2
  exit 1
fi
echo "[PASS] run_agent.py --help includes --simulator"

run_dry() {
  local dut="$1"
  local outdir="output_verify_${dut}"

  echo "[INFO] Dry-run on ${dut}"
  (
    cd "${SUB_DIR}"
    make compile \
      RTL="../../../duts/${dut}" \
      SPEC="../../../specs/${dut}_spec.md" \
      CSR_MAP="../../../csr_maps/${dut}_csr.hjson" \
      output_dir="${outdir}" \
      SIMULATOR="both" >/dev/null
  )

  "${PYTHON_BIN}" - <<PY
import json 
from pathlib import Path
out = Path(r"${SUB_DIR}/${outdir}")
log = json.loads((out / "agent_log.json").read_text())
meta = log.get("metadata", {})
assert meta.get("llm_provider") == "openai", "llm_provider must be openai"
assert len(log.get("llm_api_calls", [])) > 0, "llm_api_calls must be non-empty"
assert not any(a.get("stage") == "llm_fallback" for a in log.get("actions", [])), "llm_fallback action must not appear"
res = json.loads((out / "test_results.json").read_text())
assert bool(res.get("syntax_passed", False)), "generated tests must pass syntax check"
print("[PASS]", r"${dut}", "provider=openai", "llm_calls=", len(log.get("llm_api_calls", [])))
PY

  rm -rf "${SUB_DIR}/${outdir}"
}

NO_API_SPEND="${NO_API_SPEND:-0}"
if [[ "${NO_API_SPEND}" == "1" ]]; then
  echo "[INFO] NO_API_SPEND=1 -> skipping API-backed dry-runs (nexus_uart, bastion_gpio)"
else
  run_dry "nexus_uart"
  run_dry "bastion_gpio"
fi

echo "[INFO] Verifying prompt evidence inclusion in zip payload"
if ! command -v unzip >/dev/null 2>&1; then
  echo "[FAIL] unzip is required for zip payload validation" >&2
  exit 1
fi

ZIP_FILE="${ROOT_DIR}/submissions/task-4.1/submission-4.1.zip"
TEMP_ZIP=""

if [[ -f "${ZIP_FILE}" ]]; then
  ZIP_TO_CHECK="${ZIP_FILE}"
  echo "[INFO] Using existing zip: ${ZIP_TO_CHECK}"
else
  if ! command -v zip >/dev/null 2>&1; then
    echo "[FAIL] zip is required to create a temporary archive for validation" >&2
    exit 1
  fi
  TEMP_ZIP="$(mktemp /tmp/submission-4.1.XXXXXX.zip)"
  (
    cd "${ROOT_DIR}/submissions/task-4.1"
    zip -qr "${TEMP_ZIP}" "submission-4.1"
  )
  ZIP_TO_CHECK="${TEMP_ZIP}"
  echo "[INFO] Created temporary zip for validation: ${ZIP_TO_CHECK}"
fi

for prompt_file in "${expected_prompt_files[@]}"; do
  zip_path="submission-4.1/prompts/${prompt_file}"
  if ! unzip -Z1 "${ZIP_TO_CHECK}" | grep -Fxq "${zip_path}"; then
    echo "[FAIL] Zip payload missing prompt evidence file: ${zip_path}" >&2
    [[ -n "${TEMP_ZIP}" ]] && rm -f "${TEMP_ZIP}"
    exit 1
  fi
  echo "[PASS] zip contains ${zip_path}"
done

if [[ -n "${TEMP_ZIP}" ]]; then
  rm -f "${TEMP_ZIP}"
fi

echo "[PASS] Task 4.1 readiness checks completed"
