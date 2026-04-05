#!/usr/bin/env bash
#
# verify-3.2-readiness.sh
#
# ZIP-first readiness verification for Task 3.2 submission.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SIM="both"
QUICK=false
KEEP_WORKDIR=false
TIMEOUT=600
WORKDIR="${PROJECT_ROOT}/.tmp/verify-3.2-$$"
EXTRACT_DIR="${WORKDIR}/extracted"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

section() {
  echo
  echo -e "${BLUE}======================================================================${NC}"
  echo -e "${BLUE}$*${NC}"
  echo -e "${BLUE}======================================================================${NC}"
}

ok() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
die() { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

usage() {
  cat <<'EOF'
verify-3.2-readiness.sh

Usage:
  bash scripts/verify-3.2-readiness.sh [options]

Options:
  --sim {icarus|verilator|both}   Simulator selection for compile checks (default: both)
  --quick                         Skip non-essential checks
  --timeout SECONDS               Per command timeout (default: 600)
  -k, --keep-workdir              Keep temporary verification directory
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
  die "Invalid --sim value '${SIM}' (expected: icarus|verilator|both)"
fi

if ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]]; then
  die "Invalid --timeout value '${TIMEOUT}' (must be integer seconds)"
fi

cleanup() {
  if [[ "$KEEP_WORKDIR" == "true" ]]; then
    warn "Keeping workdir: ${WORKDIR}"
  else
    rm -rf "$WORKDIR"
  fi
}
trap cleanup EXIT

mkdir -p "$EXTRACT_DIR"
cd "$PROJECT_ROOT"

section "Environment"
if [[ -f "${PROJECT_ROOT}/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${PROJECT_ROOT}/.venv/bin/activate"
  ok "Python virtual environment activated"
else
  die "Missing expected venv at ${PROJECT_ROOT}/.venv"
fi

section "Task 3.2 - Package ZIP"
bash "${SCRIPT_DIR}/manage-3.2-submissions.sh" package
ok "Task 3.2 ZIP package created"

section "Task 3.2 - Extract ZIP"
ZIP_FILE="${PROJECT_ROOT}/submissions/zips-3.2/submission-3.2.zip"
[[ -f "$ZIP_FILE" ]] || die "Missing ZIP: $ZIP_FILE"
unzip -q "$ZIP_FILE" -d "$EXTRACT_DIR"
SUBMISSION_EXTRACTED="${EXTRACT_DIR}/submission-3.2"
[[ -d "$SUBMISSION_EXTRACTED" ]] || die "Extracted submission root missing"
ok "ZIP extracted to $SUBMISSION_EXTRACTED"

section "Task 3.2 - Structure Validation"
required_files=(
  "Makefile"
  "metadata.yaml"
  "methodology.md"
  "summary.md"
  "preprocessing/trace_validator.py"
  "testbench/tl_ul_agent.py"
  "analysis/trace_01.yaml"
  "analysis/trace_02.yaml"
  "analysis/trace_03.yaml"
  "analysis/trace_04.yaml"
  "analysis/trace_05.yaml"
  "reproduction_tests/repro_01.py"
  "reproduction_tests/repro_02.py"
  "reproduction_tests/repro_03.py"
  "reproduction_tests/repro_04.py"
  "reproduction_tests/repro_05.py"
  "prompts/README.md"
  "prompts/01_task32_audit_and_requirements.md"
  "prompts/02_trace_inventory_and_signal_windows.md"
  "prompts/03_root_cause_mapping_and_cycle_alignment.md"
  "prompts/04_reproduction_test_authoring.md"
  "prompts/05_packaging_and_readiness_automation.md"
  "prompts/06_final_validation_and_signoff.md"
)

for rel in "${required_files[@]}"; do
  [[ -f "${SUBMISSION_EXTRACTED}/${rel}" ]] || die "Missing required file: ${rel}"
done

[[ -d "${SUBMISSION_EXTRACTED}/prompts" ]] || die "Missing prompts/ directory"
prompt_count="$(find "${SUBMISSION_EXTRACTED}/prompts" -maxdepth 1 -type f -name '*.md' | wc -l)"
[[ "$prompt_count" -eq 7 ]] || die "Need exactly 7 prompt markdown files, found ${prompt_count}"

grep -q 'submissions/task-3.2/prompts.md' "${SUBMISSION_EXTRACTED}/prompts/README.md" || die "prompts/README.md must reference submissions/task-3.2/prompts.md"
grep -q 'https://github.com/' "${SUBMISSION_EXTRACTED}/prompts/README.md" || die "prompts/README.md must include GitHub master transcript URL"

grep -Eq 'task_id:[[:space:]]*"3\.2"' "${SUBMISSION_EXTRACTED}/metadata.yaml" || die "metadata.yaml task_id must be 3.2"

for target in compile simulate coverage clean run_repro; do
  grep -Eq "^${target}:" "${SUBMISSION_EXTRACTED}/Makefile" || die "Makefile missing target ${target}"
done

ok "Structure checks passed (analysis=5, repro=5, prompts=${prompt_count})"

section "Task 3.2 - Analysis Validation"
VALIDATION_LOG="${WORKDIR}/task32_validate.log"
pushd "$SUBMISSION_EXTRACTED" >/dev/null
if timeout "$TIMEOUT" python preprocessing/trace_validator.py --validate analysis >"$VALIDATION_LOG" 2>&1; then
  ok "analysis YAML validation passed"
else
  cat "$VALIDATION_LOG" | sed 's/^/    /'
  die "analysis YAML validation failed"
fi

if timeout "$TIMEOUT" make compile SIM="$SIM" >"${WORKDIR}/task32_make_compile.log" 2>&1; then
  ok "make compile passed (SIM=${SIM})"
else
  cat "${WORKDIR}/task32_make_compile.log" | sed 's/^/    /'
  die "make compile failed"
fi
popd >/dev/null

if [[ "$QUICK" == "true" ]]; then
  warn "Quick mode enabled: runtime repro execution intentionally skipped"
fi

forbidden_count="$(find "${SUBMISSION_EXTRACTED}" -type f \( -name '*.vcd' -o -name '*.fst' -o -name '*.vpd' -o -name '*.fsdb' \) | wc -l)"
[[ "$forbidden_count" -eq 0 ]] || die "Found forbidden waveform files in package (count=${forbidden_count})"

ok "Forbidden artifact check passed"

section "Task 3.2 - ZIP Status"
bash "${SCRIPT_DIR}/manage-3.2-submissions.sh" status

section "Done"
ok "Task 3.2 readiness verification completed"
