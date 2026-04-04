#!/usr/bin/env bash
#
# verify-1.3-readiness.sh
#
# ZIP-first readiness verification for Task 1.3 submission.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SIM="both"
QUICK=false
KEEP_WORKDIR=false
TIMEOUT=600
SMOKE_DUT="bastion_gpio"
WORKDIR="/tmp/verify-1.3-$$"
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
verify-1.3-readiness.sh

Usage:
  bash scripts/verify-1.3-readiness.sh [options]

Options:
  --sim {icarus|verilator|both}   Simulator selection (default: both)
  --smoke-dut DUT                 DUT for runtime smoke (default: bastion_gpio)
  --quick                         Skip simulation smoke checks
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
    --smoke-dut)
      SMOKE_DUT="$2"
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
  die "Invalid --sim value '$SIM' (expected: icarus|verilator|both)"
fi

if ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]]; then
  die "Invalid --timeout value '$TIMEOUT' (must be integer seconds)"
fi

cleanup() {
  if [[ "$KEEP_WORKDIR" == "true" ]]; then
    warn "Keeping workdir: $WORKDIR"
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

section "Task 1.3 - Package ZIP"
bash "${SCRIPT_DIR}/manage-1.3-submissions.sh" package
ok "Task 1.3 ZIP package created"

section "Task 1.3 - Extract ZIP"
ZIP_FILE="${PROJECT_ROOT}/submissions/zips-1.3/submission-1.3.zip"
[[ -f "$ZIP_FILE" ]] || die "Missing ZIP: $ZIP_FILE"
unzip -q "$ZIP_FILE" -d "$EXTRACT_DIR"
SUBMISSION_EXTRACTED="${EXTRACT_DIR}/submission-1.3"
[[ -d "$SUBMISSION_EXTRACTED" ]] || die "Extracted submission root missing"
ok "ZIP extracted to $SUBMISSION_EXTRACTED"

section "Task 1.3 - Structure Validation"
required_files=(
  "Makefile"
  "metadata.yaml"
  "methodology.md"
  "generator/csr_test_generator.py"
  "generated_tests/__init__.py"
)

for rel in "${required_files[@]}"; do
  [[ -f "${SUBMISSION_EXTRACTED}/${rel}" ]] || die "Missing required file: ${rel}"
done

generated_count="$(find "${SUBMISSION_EXTRACTED}/generated_tests" -maxdepth 1 -type f -name 'test_csr_*.py' | wc -l)"
[[ "$generated_count" -ge 3 ]] || die "Need >=3 generated test files, found ${generated_count}"

prompt_count="$(find "${SUBMISSION_EXTRACTED}/prompts" -maxdepth 1 -type f -name '*.md' | wc -l)"
[[ "$prompt_count" -ge 6 ]] || die "Need >=6 prompt markdown files (README + chunk files), found ${prompt_count}"
[[ -f "${SUBMISSION_EXTRACTED}/prompts/README.md" ]] || die "Missing prompts/README.md"

prompt_chunk_count="$(find "${SUBMISSION_EXTRACTED}/prompts" -maxdepth 1 -type f -name '[0-9][0-9]_*.md' | wc -l)"
[[ "$prompt_chunk_count" -ge 5 ]] || die "Need >=5 chunked prompt files named 00_prefix.md style, found ${prompt_chunk_count}"

map_count="$(find "${SUBMISSION_EXTRACTED}/csr_maps" -maxdepth 1 -type f -name '*_csr.hjson' | wc -l)"
[[ "$map_count" -ge 3 ]] || die "Need >=3 CSR maps in submission, found ${map_count}"

ok "Structure checks passed (generated tests=${generated_count}, prompts=${prompt_count}, prompt chunks=${prompt_chunk_count}, maps=${map_count})"

section "Task 1.3 - Generator Smoke"
pushd "$SUBMISSION_EXTRACTED" >/dev/null
timeout "$TIMEOUT" make generate >/tmp/task13_generate.log 2>&1 || {
  tail -n 80 /tmp/task13_generate.log | sed 's/^/    /'
  die "Generator smoke failed"
}
popd >/dev/null
ok "make generate passed in extracted ZIP"

section "Task 1.3 - Runtime Smoke"
if [[ "$QUICK" == "true" ]]; then
  warn "Quick mode enabled: skipping simulation smoke"
else
  if [[ "$SIM" == "both" ]]; then
    SIMULATORS=(icarus verilator)
  else
    SIMULATORS=("$SIM")
  fi

  for sim in "${SIMULATORS[@]}"; do
    info "Running ${SMOKE_DUT} smoke on ${sim}"
    pushd "$SUBMISSION_EXTRACTED" >/dev/null
    rm -rf sim_build obj_dir
    LOG_FILE="${WORKDIR}/task13_${SMOKE_DUT}_${sim}.log"

    if timeout "$TIMEOUT" make simulate DUT="$SMOKE_DUT" SIM="$sim" DUT_PATH="${PROJECT_ROOT}/duts" >"$LOG_FILE" 2>&1; then
      summary_line="$(grep -E "\*\* TESTS=" "$LOG_FILE" | tail -1 || true)"
      tests="$(echo "$summary_line" | sed -n 's/.*TESTS=\([0-9]\+\).*/\1/p')"
      fail="$(echo "$summary_line" | sed -n 's/.*FAIL=\([0-9]\+\).*/\1/p')"
      if [[ -n "$tests" && -n "$fail" && "$tests" -gt 0 && "$fail" -eq 0 ]]; then
        ok "${SMOKE_DUT}@${sim} smoke passed (TESTS=${tests}, FAIL=${fail})"
      else
        tail -n 120 "$LOG_FILE" | sed 's/^/    /'
        die "${SMOKE_DUT}@${sim} smoke missing clean summary"
      fi
    else
      tail -n 120 "$LOG_FILE" | sed 's/^/    /'
      die "${SMOKE_DUT}@${sim} smoke failed or timed out"
    fi
    popd >/dev/null
  done
fi

section "Task 1.3 - ZIP Status"
bash "${SCRIPT_DIR}/manage-1.3-submissions.sh" status

section "Done"
ok "Task 1.3 readiness verification completed"
