#!/usr/bin/env bash
#
# verify-2.2-readiness.sh
#
# ZIP-first readiness verification for Task 2.2 submissions.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SIM="both"
QUICK=false
KEEP_WORKDIR=false
TIMEOUT=600
WORKDIR="/tmp/verify-2.2-$$"
EXTRACT_DIR="${WORKDIR}/extracted"
DUTS=(aegis_aes sentinel_hmac rampart_i2c warden_timer)

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

section() {
  echo
  echo -e "${BLUE}======================================================================${NC}"
  echo -e "${BLUE}$*${NC}"
  echo -e "${BLUE}======================================================================${NC}"
}

ok() { echo -e "${GREEN}[OK]${NC} $*"; }
info() { echo -e "${CYAN}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
die() { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

usage() {
  cat <<'EOF'
verify-2.2-readiness.sh

Usage:
  bash scripts/verify-2.2-readiness.sh [options]

Options:
  --sim {icarus|verilator|both}   Simulator selection (default: both)
  --quick                         Skip runtime smoke checks
  --timeout SECONDS               Per simulation timeout (default: 600)
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

validate_structure() {
  local submission_dir="$1"
  local dut="$2"

  local required_files=(
    "Makefile"
    "metadata.yaml"
    "methodology.md"
    "testbench/__init__.py"
    "testbench/tl_ul_agent.py"
    "tests/__init__.py"
    "tests/test_reference.py"
    "results/coverage_before.txt"
    "results/coverage_after.txt"
  )

  for rel in "${required_files[@]}"; do
    [[ -f "${submission_dir}/${rel}" ]] || die "${dut}: missing required file ${rel}"
  done

  [[ -d "${submission_dir}/prompts" ]] || die "${dut}: missing prompts/ directory"

  local required_prompt_files=(
    "README.md"
    "01_task22_audit_and_planning.md"
    "02_stimulus_scaffolding_and_baseline_split.md"
    "03_coverage_execution_and_makefile_alignment.md"
    "04_gap_closure_and_debug_iterations.md"
    "05_packaging_and_readiness_automation.md"
    "06_final_audit_and_submission_signoff.md"
  )

  for rel in "${required_prompt_files[@]}"; do
    [[ -f "${submission_dir}/prompts/${rel}" ]] || die "${dut}: missing prompts/${rel}"
  done

  prompts_md_count="$(find "${submission_dir}/prompts" -maxdepth 1 -type f -name '*.md' | wc -l)"
  [[ "$prompts_md_count" -ge 7 ]] || die "${dut}: need >=7 markdown files in prompts/, found ${prompts_md_count}"

  grep -q 'submissions/task-2.2/prompts.md' "${submission_dir}/prompts/README.md" || \
    die "${dut}: prompts/README.md must reference submissions/task-2.2/prompts.md"

  grep -q 'https://github.com/' "${submission_dir}/prompts/README.md" || \
    die "${dut}: prompts/README.md must include a GitHub master transcript URL"

  coverage_test_count="$(find "${submission_dir}/tests" -maxdepth 1 -type f -name 'test_coverage_*.py' | wc -l)"
  [[ "$coverage_test_count" -ge 1 ]] || die "${dut}: missing tests/test_coverage_*.py"

  grep -Eq 'task_id:[[:space:]]*"2\.2"' "${submission_dir}/metadata.yaml" || die "${dut}: metadata task_id must be 2.2"
  grep -Eq "dut_id:[[:space:]]*\"${dut}\"" "${submission_dir}/metadata.yaml" || die "${dut}: metadata dut_id mismatch"

  for target in compile simulate coverage clean; do
    grep -Eq "^${target}:" "${submission_dir}/Makefile" || die "${dut}: Makefile missing target ${target}"
  done

  if ! grep -Eq '^line_coverage:' "${submission_dir}/results/coverage_before.txt"; then
    die "${dut}: coverage_before.txt missing line_coverage"
  fi
  if ! grep -Eq '^functional_coverage:' "${submission_dir}/results/coverage_after.txt"; then
    die "${dut}: coverage_after.txt missing functional_coverage"
  fi

  ok "${dut}: structure checks passed (coverage tests=${coverage_test_count}, prompts=${prompts_md_count})"
}

run_smoke() {
  local submission_dir="$1"
  local dut="$2"
  local sim="$3"
  local log_file="${WORKDIR}/task22_${dut}_${sim}.log"

  pushd "$submission_dir" >/dev/null
  rm -rf sim_build obj_dir

  if timeout "$TIMEOUT" make clean >"$log_file" 2>&1 && \
     timeout "$TIMEOUT" make SIM="$sim" compile DUT_PATH="${PROJECT_ROOT}/duts" >>"$log_file" 2>&1; then
    summary_line="$(grep -E '\*\* TESTS=' "$log_file" | tail -1 || true)"
    tests="$(echo "$summary_line" | sed -n 's/.*TESTS=\([0-9]\+\).*/\1/p')"
    fail="$(echo "$summary_line" | sed -n 's/.*FAIL=\([0-9]\+\).*/\1/p')"

    if [[ -n "$tests" && -n "$fail" && "$tests" -gt 0 && "$fail" -eq 0 ]]; then
      ok "${dut}@${sim} smoke passed (TESTS=${tests}, FAIL=${fail})"
    else
      tail -n 120 "$log_file" | sed 's/^/    /'
      die "${dut}@${sim} smoke missing clean summary"
    fi
  else
    tail -n 120 "$log_file" | sed 's/^/    /'
    die "${dut}@${sim} smoke failed or timed out"
  fi

  popd >/dev/null
}

section "Environment"
if [[ -f "${PROJECT_ROOT}/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${PROJECT_ROOT}/.venv/bin/activate"
  ok "Python virtual environment activated"
else
  die "Missing expected venv at ${PROJECT_ROOT}/.venv"
fi

section "Task 2.2 - Package ZIPs"
bash "${SCRIPT_DIR}/manage-2.2-submissions.sh" package-all
ok "Task 2.2 ZIP packages created"

section "Task 2.2 - Extract ZIPs"
for dut in "${DUTS[@]}"; do
  zip_file="${PROJECT_ROOT}/submissions/zips-2.2/submission-2.2-${dut}.zip"
  [[ -f "$zip_file" ]] || die "Missing ZIP: ${zip_file}"
  unzip -q "$zip_file" -d "$EXTRACT_DIR"
  [[ -d "${EXTRACT_DIR}/submission-2.2-${dut}" ]] || die "Missing extracted folder for ${dut}"
  ok "Extracted submission-2.2-${dut}"
done

section "Task 2.2 - Structure Validation"
for dut in "${DUTS[@]}"; do
  validate_structure "${EXTRACT_DIR}/submission-2.2-${dut}" "$dut"
done

section "Task 2.2 - Runtime Smoke"
if [[ "$QUICK" == "true" ]]; then
  warn "Quick mode enabled: skipping runtime smoke"
else
  if [[ "$SIM" == "both" ]]; then
    SIMULATORS=(icarus verilator)
  else
    SIMULATORS=("$SIM")
  fi

  for dut in "${DUTS[@]}"; do
    for sim in "${SIMULATORS[@]}"; do
      info "Running ${dut} smoke on ${sim}"
      run_smoke "${EXTRACT_DIR}/submission-2.2-${dut}" "$dut" "$sim"
    done
  done
fi

section "Task 2.2 - ZIP Status"
bash "${SCRIPT_DIR}/manage-2.2-submissions.sh" status

section "Done"
ok "Task 2.2 readiness verification completed"
