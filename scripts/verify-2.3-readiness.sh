#!/usr/bin/env bash
#
# verify-2.3-readiness.sh
#
# ZIP-first readiness verification for Task 2.3 submission.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SIM="both"
QUICK=false
KEEP_WORKDIR=false
TIMEOUT=1200
WORKDIR="/tmp/verify-2.3-$$"
EXTRACT_DIR="${WORKDIR}/extracted"

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
verify-2.3-readiness.sh

Usage:
  bash scripts/verify-2.3-readiness.sh [options]

Options:
  --sim {icarus|verilator|both}   Simulator selection (default: both)
  --quick                         Skip run_cdg execution
  --timeout SECONDS               Per command timeout (default: 1200)
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

section "Task 2.3 - Package ZIP"
bash "${SCRIPT_DIR}/manage-2.3-submissions.sh" package
ok "Task 2.3 ZIP package created"

section "Task 2.3 - Extract ZIP"
ZIP_FILE="${PROJECT_ROOT}/submissions/zips-2.3/submission-2.3.zip"
[[ -f "$ZIP_FILE" ]] || die "Missing ZIP: $ZIP_FILE"
unzip -q "$ZIP_FILE" -d "$EXTRACT_DIR"
SUBMISSION_EXTRACTED="${EXTRACT_DIR}/submission-2.3"
[[ -d "$SUBMISSION_EXTRACTED" ]] || die "Extracted submission root missing"
ok "ZIP extracted to $SUBMISSION_EXTRACTED"

section "Task 2.3 - Structure Validation"
required_files=(
  "Makefile"
  "metadata.yaml"
  "methodology.md"
  "cdg_system/cdg_engine.py"
  "cdg_system/coverage_analyzer.py"
  "cdg_system/constraint_tuner.py"
  "cdg_system/config.yaml"
  "cdg_system/cdg.py"
  "cdg_system/analyzer.py"
  "cdg_system/strategy.py"
  "cdg_system/generator.py"
  "tests/test_reference.py"
  "tests/test_cdg_generated.py"
  "testbench/tl_ul_agent.py"
  "prompts/README.md"
  "prompts/01_task23_audit_and_requirements.md"
  "prompts/02_strategy_selection_b_plus_c.md"
  "prompts/03_cdg_architecture_and_interfaces.md"
  "prompts/04_loop_execution_and_coverage_parsing.md"
  "prompts/05_packaging_and_compliance_automation.md"
  "prompts/06_validation_and_signoff.md"
)

for rel in "${required_files[@]}"; do
  [[ -f "${SUBMISSION_EXTRACTED}/${rel}" ]] || die "Missing required file: ${rel}"
done

[[ -d "${SUBMISSION_EXTRACTED}/prompts" ]] || die "Missing prompts/ directory"
prompt_count="$(find "${SUBMISSION_EXTRACTED}/prompts" -maxdepth 1 -type f -name '*.md' | wc -l)"
[[ "$prompt_count" -eq 7 ]] || die "Need exactly 7 prompt markdown files, found ${prompt_count}"

grep -q 'submissions/task-2.3/prompts.md' "${SUBMISSION_EXTRACTED}/prompts/README.md" || die "prompts/README.md must reference submissions/task-2.3/prompts.md"
grep -q 'https://github.com/' "${SUBMISSION_EXTRACTED}/prompts/README.md" || die "prompts/README.md must include GitHub master transcript URL"

grep -Eq 'task_id:[[:space:]]*"2\.3"' "${SUBMISSION_EXTRACTED}/metadata.yaml" || die "metadata.yaml task_id must be 2.3"

for target in compile simulate coverage run_cdg clean; do
  grep -Eq "^${target}:" "${SUBMISSION_EXTRACTED}/Makefile" || die "Makefile missing target ${target}"
done

ok "Structure checks passed (prompts=${prompt_count})"

forbidden_count="$(find "${SUBMISSION_EXTRACTED}" -type f \( -name '*.vcd' -o -name '*.fst' -o -name '*.vpd' -o -name '*.fsdb' -o -name '*.dat' -o -name '*.info' \) | wc -l)"
[[ "$forbidden_count" -eq 0 ]] || die "Found forbidden dump/intermediate files in package (count=${forbidden_count})"

ok "Forbidden artifact check passed"

section "Task 2.3 - Compile Smoke"
if [[ "$SIM" == "both" ]]; then
  SIMULATORS=(icarus verilator)
else
  SIMULATORS=("$SIM")
fi

for sim in "${SIMULATORS[@]}"; do
  info "Compiling reference test on ${sim}"
  pushd "$SUBMISSION_EXTRACTED" >/dev/null
  LOG_FILE="${WORKDIR}/task23_compile_${sim}.log"
  if timeout "$TIMEOUT" make SIM="$sim" compile DUT_PATH="${PROJECT_ROOT}/duts" >"$LOG_FILE" 2>&1; then
    ok "compile passed on ${sim}"
  else
    tail -n 120 "$LOG_FILE" | sed 's/^/    /'
    die "compile failed or timed out on ${sim}"
  fi
  popd >/dev/null
done

section "Task 2.3 - run_cdg"
if [[ "$QUICK" == "true" ]]; then
  warn "Quick mode enabled: skipping run_cdg"
else
  pushd "$SUBMISSION_EXTRACTED" >/dev/null
  LOG_FILE="${WORKDIR}/task23_run_cdg.log"

  # Keep readiness runtime practical while still meeting >=10 autonomous iterations.
  if [[ "$SIM" == "icarus" ]]; then
    CDG_SIM_RUN="icarus"
  else
    CDG_SIM_RUN="verilator"
  fi

  if timeout "$TIMEOUT" make run_cdg DUT_NAME=sentinel_hmac CDG_SIM="$CDG_SIM_RUN" CDG_BUDGET=20000 CDG_ITERATIONS=10 >"$LOG_FILE" 2>&1; then
    ok "run_cdg completed"
  else
    tail -n 160 "$LOG_FILE" | sed 's/^/    /'
    die "run_cdg failed or timed out"
  fi
  popd >/dev/null
fi

section "Task 2.3 - Artifact Validation"
for rel in \
  "results/convergence_log.csv" \
  "results/final_coverage.txt" \
  "logs/coverage_curve.csv" \
  "logs/iteration_log.yaml" \
  "logs/strategy_evolution.yaml"; do
  [[ -f "${SUBMISSION_EXTRACTED}/${rel}" ]] || die "Missing generated artifact: ${rel}"
done

rows="$(tail -n +2 "${SUBMISSION_EXTRACTED}/results/convergence_log.csv" | wc -l)"
[[ "$rows" -ge 10 ]] || die "convergence_log.csv must contain >=10 data rows, found ${rows}"

expected_header="iteration,cycles_used,line_coverage,branch_coverage,functional_coverage"
actual_header="$(head -n 1 "${SUBMISSION_EXTRACTED}/results/convergence_log.csv" | tr -d '\r')"
[[ "$actual_header" == "$expected_header" ]] || die "convergence_log.csv header mismatch (expected: ${expected_header})"

ok "Generated artifacts validated (convergence rows=${rows})"

section "Task 2.3 - ZIP Status"
bash "${SCRIPT_DIR}/manage-2.3-submissions.sh" status

section "Done"
ok "Task 2.3 readiness verification completed"
