#!/usr/bin/env bash
set -euo pipefail

SIM="both"
QUICK=false
KEEP_WORKDIR=false
TIMEOUT=""

usage() {
  cat <<'EOF'
verify-4.3-readiness.sh

Usage:
  bash scripts/verify-4.3-readiness.sh [options]

Options:
  --sim {icarus|verilator|both}   Compatibility option (default: both)
  --quick                         Compatibility option (currently informational)
  --timeout SECONDS               Compatibility option (currently informational)
  -k, --keep-workdir              Keep output directory from API-backed dry run
  -h, --help                      Show this help
EOF
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sim)
      SIM="$2"
      shift 2
      ;;
    --quick)
      QUICK=true
      shift
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    -k|--keep-workdir)
      KEEP_WORKDIR=true
      shift
      ;;
    -h|--help)
      usage 0
      ;;
    *)
      usage 2
      ;;
  esac
done

if [[ "$SIM" != "icarus" && "$SIM" != "verilator" && "$SIM" != "both" ]]; then
  echo "[FAIL] Invalid --sim value '$SIM' (expected: icarus|verilator|both)" >&2
  exit 1
fi

if [[ -n "$TIMEOUT" ]] && ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]]; then
  echo "[FAIL] Invalid --timeout value '$TIMEOUT' (must be integer seconds)" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUB_DIR="${ROOT_DIR}/submissions/task-4.3/submission-4.3"

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
  "${SUB_DIR}/agent/requirements.txt"
  "${SUB_DIR}/agent/src"
  "${SUB_DIR}/run_spec_interpreter.py"
  "${SUB_DIR}/requirements.txt"
  "${SUB_DIR}/sample_spec.md"
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
  "01_task43_requirements_audit_prompt.md"
  "02_task43_contract_resolution_prompt.md"
  "03_task43_orchestrator_design_prompt.md"
  "04_task43_generation_quality_prompt.md"
  "05_task43_readiness_packaging_prompt.md"
)

for prompt_file in "${expected_prompt_files[@]}"; do
  if [[ ! -f "${SUB_DIR}/prompts/${prompt_file}" ]]; then
    echo "[FAIL] Missing prompt evidence file: ${SUB_DIR}/prompts/${prompt_file}" >&2
    exit 1
  fi
  echo "[PASS] prompts/${prompt_file}"
done

prompt_count=$(find "${SUB_DIR}/prompts" -maxdepth 1 -type f -name "*.md" | wc -l | tr -d ' ')
if [[ "${prompt_count}" -lt 6 ]]; then
  echo "[FAIL] prompts/ must contain at least 6 markdown evidence files; found ${prompt_count}" >&2
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

for arg in --spec --output_dir; do
  if ! "${PYTHON_BIN}" "${SUB_DIR}/agent/run_agent.py" --help | grep -q -- "${arg}"; then
    echo "[FAIL] run_agent.py --help missing ${arg}" >&2
    exit 1
  fi
  echo "[PASS] run_agent.py --help includes ${arg}"
done

NO_API_SPEND="${NO_API_SPEND:-1}"
if [[ "${NO_API_SPEND}" == "1" ]]; then
  echo "[INFO] NO_API_SPEND=1 -> skipping API-backed dry run"
else
  echo "[INFO] Running API-backed dry run"
  OUTDIR="output_verify_spec"
  (
    cd "${SUB_DIR}"
    "${PYTHON_BIN}" agent/run_agent.py \
      --spec "sample_spec.md" \
      --output_dir "${OUTDIR}" >/dev/null
  )

  "${PYTHON_BIN}" - <<PY
import py_compile
from pathlib import Path
import yaml

out = Path(r"${SUB_DIR}/output_verify_spec")
assert out.exists(), "output directory missing"

required = [
    out / "vplan.yaml",
    out / "coverage_model.yaml",
    out / "assertions.yaml",
    out / "report.md",
    out / "agent_log.json",
    out / "test_stubs",
]
for path in required:
    assert path.exists(), f"missing output artifact: {path}"

# Task-page compatibility mirrors
compat_required = [
    out / "tests",
    out / "coverage" / "coverage_model.yaml",
    out / "assertions" / "assertions.yaml",
]
for path in compat_required:
    assert path.exists(), f"missing compatibility artifact: {path}"

for yaml_file in [out / "vplan.yaml", out / "coverage_model.yaml", out / "assertions.yaml"]:
    payload = yaml.safe_load(yaml_file.read_text())
    assert payload is not None, f"empty yaml: {yaml_file}"

stub_files = sorted((out / "test_stubs").glob("*.py"))
assert stub_files, "no generated test stubs"
for stub in stub_files:
    py_compile.compile(str(stub), doraise=True)
print("[PASS] API-backed dry run artifact and syntax checks")
PY

  if [[ "${KEEP_WORKDIR}" == "true" ]]; then
    echo "[INFO] Keeping API dry-run output at ${SUB_DIR}/${OUTDIR}"
  else
    rm -rf "${SUB_DIR}/${OUTDIR}"
  fi
fi

echo "[INFO] Verifying prompt evidence inclusion in zip payload"
if ! command -v unzip >/dev/null 2>&1; then
  echo "[FAIL] unzip is required for zip payload validation" >&2
  exit 1
fi

ZIP_DIR="${ROOT_DIR}/submissions/zips-4.3"
ZIP_FILE="${ZIP_DIR}/submission-4.3.zip"
mkdir -p "${ZIP_DIR}"

if [[ -f "${ZIP_FILE}" ]]; then
  ZIP_TO_CHECK="${ZIP_FILE}"
  echo "[INFO] Using existing zip: ${ZIP_TO_CHECK}"
else
  if ! command -v zip >/dev/null 2>&1; then
    echo "[FAIL] zip is required to create canonical archive for validation" >&2
    exit 1
  fi
  (
    cd "${ROOT_DIR}/submissions/task-4.3"
    zip -qr "${ZIP_FILE}" "submission-4.3"
  )
  ZIP_TO_CHECK="${ZIP_FILE}"
  echo "[INFO] Created canonical zip for validation: ${ZIP_TO_CHECK}"
fi

for prompt_file in "${expected_prompt_files[@]}"; do
  zip_path="submission-4.3/prompts/${prompt_file}"
  if ! unzip -Z1 "${ZIP_TO_CHECK}" | grep -Fxq "${zip_path}"; then
    echo "[FAIL] Zip payload missing prompt evidence file: ${zip_path}" >&2
    exit 1
  fi
  echo "[PASS] zip contains ${zip_path}"
done

extra_expected=(
  "submission-4.3/sample_spec.md"
  "submission-4.3/run_spec_interpreter.py"
  "submission-4.3/requirements.txt"
)

for zip_path in "${extra_expected[@]}"; do
  if ! unzip -Z1 "${ZIP_TO_CHECK}" | grep -Fxq "${zip_path}"; then
    echo "[FAIL] Zip payload missing expected file: ${zip_path}" >&2
    exit 1
  fi
  echo "[PASS] zip contains ${zip_path}"
done

echo "[PASS] Task 4.3 readiness checks completed"
