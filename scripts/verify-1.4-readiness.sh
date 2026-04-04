#!/usr/bin/env bash
#
# verify-1.4-readiness.sh
#
# ZIP-first readiness verification for Task 1.4 submissions.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SIM="both"
QUICK=false
KEEP_WORKDIR=false
TIMEOUT=600
BUG_SEEDS=""
BUG_DEFINE_PREFIX="SEED_BUG_"
REQUIRE_BUG_FAIL=false
WORKDIR="/tmp/verify-1.4-$$"
EXTRACT_DIR="${WORKDIR}/extracted"
DUTS=(rampart_i2c sentinel_hmac)

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
verify-1.4-readiness.sh

Usage:
  bash scripts/verify-1.4-readiness.sh [options]

Options:
  --sim {icarus|verilator|both}   Simulator selection (default: both)
  --quick                         Skip runtime smoke checks
  --timeout SECONDS               Per simulation timeout (default: 600)
  --bug-seeds LIST                Optional comma-separated bug seeds (example: 1,2,3)
  --bug-define-prefix PREFIX      Macro prefix for bug define (default: SEED_BUG_)
  --require-bug-fail              Fail if any bug-seed run does not trigger a failing run
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
    --bug-seeds)
      BUG_SEEDS="$2"
      shift 2
      ;;
    --bug-define-prefix)
      BUG_DEFINE_PREFIX="$2"
      shift 2
      ;;
    --require-bug-fail)
      REQUIRE_BUG_FAIL=true
      shift
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

BUG_SEED_LIST=()
if [[ -n "$BUG_SEEDS" ]]; then
  IFS=',' read -r -a raw_seeds <<< "$BUG_SEEDS"
  for raw in "${raw_seeds[@]}"; do
    seed="${raw//[[:space:]]/}"
    [[ -n "$seed" ]] || continue
    [[ "$seed" =~ ^[0-9]+$ ]] || die "Invalid seed '${seed}' in --bug-seeds"
    BUG_SEED_LIST+=("$seed")
  done
  [[ ${#BUG_SEED_LIST[@]} -gt 0 ]] || die "--bug-seeds provided but no valid seeds parsed"
fi

bug_total=0
bug_killed=0
bug_survived=0

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
    "bind_file.sv"
    "assertion_manifest.yaml"
    "assertions/protocol_assertions.sv"
    "assertions/functional_assertions.sv"
    "assertions/structural_assertions.sv"
    "assertions/liveness_assertions.sv"
    "tests/test_with_assertions.py"
    "tests/__init__.py"
    "testbench/__init__.py"
    "testbench/tl_ul_agent.py"
  )

  for rel in "${required_files[@]}"; do
    [[ -f "${submission_dir}/${rel}" ]] || die "${dut}: missing required file ${rel}"
  done

  [[ -d "${submission_dir}/prompts" ]] || die "${dut}: missing prompts/ directory"

  prompts_md_count="$(find "${submission_dir}/prompts" -maxdepth 1 -type f -name '*.md' | wc -l)"
  [[ "$prompts_md_count" -ge 6 ]] || die "${dut}: need >=6 markdown files in prompts/, found ${prompts_md_count}"

  [[ -f "${submission_dir}/prompts/README.md" ]] || die "${dut}: missing prompts/README.md"

  grep -q 'submissions/task-1.4/prompts.md' "${submission_dir}/prompts/README.md" || \
    die "${dut}: prompts/README.md must reference submissions/task-1.4/prompts.md"

  prompt_chunk_count="$(find "${submission_dir}/prompts" -maxdepth 1 -type f -name '[0-9][0-9]_*.md' | wc -l)"
  [[ "$prompt_chunk_count" -ge 5 ]] || die "${dut}: need >=5 chunked prompt files, found ${prompt_chunk_count}"

  assertion_count="$(grep -Ec '^[[:space:]]*- name:' "${submission_dir}/assertion_manifest.yaml" || true)"
  [[ "$assertion_count" -ge 20 ]] || die "${dut}: assertion_manifest has ${assertion_count}, need >=20"

  for cat in protocol functional structural liveness; do
    cat_count="$(grep -Ec "type:[[:space:]]*\"${cat}\"" "${submission_dir}/assertion_manifest.yaml" || true)"
    [[ "$cat_count" -gt 0 ]] || die "${dut}: assertion_manifest missing type '${cat}'"
  done

  grep -Eq 'task_id:[[:space:]]*"1\.4"' "${submission_dir}/metadata.yaml" || die "${dut}: metadata task_id must be 1.4"
  grep -Eq "dut_id:[[:space:]]*\"${dut}\"" "${submission_dir}/metadata.yaml" || die "${dut}: metadata dut_id mismatch"

  grep -q 'bind_file.sv' "${submission_dir}/Makefile" || die "${dut}: Makefile missing bind_file.sv source"

  ok "${dut}: structure checks passed (assertions=${assertion_count}, prompt chunks=${prompt_chunk_count})"
}

run_smoke() {
  local submission_dir="$1"
  local dut="$2"
  local sim="$3"
  local log_file="${WORKDIR}/task14_${dut}_${sim}.log"

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

run_bug_seed() {
  local submission_dir="$1"
  local dut="$2"
  local sim="$3"
  local seed="$4"
  local define="${BUG_DEFINE_PREFIX}${seed}"
  local log_file="${WORKDIR}/task14_${dut}_${sim}_bug_${seed}.log"

  bug_total=$((bug_total + 1))

  pushd "$submission_dir" >/dev/null
  rm -rf sim_build obj_dir

  if timeout "$TIMEOUT" make clean >"$log_file" 2>&1 && \
     timeout "$TIMEOUT" make SIM="$sim" compile DUT_PATH="${PROJECT_ROOT}/duts" USER_COMPILE_ARGS="-D${define}" >>"$log_file" 2>&1; then
    bug_survived=$((bug_survived + 1))
    warn "${dut}@${sim} seed=${seed} (${define}) SURVIVED: run remained clean"
    if [[ "$REQUIRE_BUG_FAIL" == "true" ]]; then
      tail -n 120 "$log_file" | sed 's/^/    /'
      die "${dut}@${sim} seed=${seed} expected a failing run but survived"
    fi
  else
    if grep -Eq 'Assertion failed|\*\* TESTS=.*FAIL=[1-9]|\$error' "$log_file"; then
      bug_killed=$((bug_killed + 1))
      ok "${dut}@${sim} seed=${seed} (${define}) KILLED: failing run observed"
    else
      tail -n 120 "$log_file" | sed 's/^/    /'
      die "${dut}@${sim} seed=${seed} failed without clear assertion/test-fail evidence"
    fi
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

section "Task 1.4 - Package ZIPs"
bash "${SCRIPT_DIR}/manage-1.4-submissions.sh" package-all
ok "Task 1.4 ZIP packages created"

section "Task 1.4 - Extract ZIPs"
for dut in "${DUTS[@]}"; do
  zip_file="${PROJECT_ROOT}/submissions/zips-1.4/submission-1.4-${dut}.zip"
  [[ -f "$zip_file" ]] || die "Missing ZIP: ${zip_file}"
  unzip -q "$zip_file" -d "$EXTRACT_DIR"
  [[ -d "${EXTRACT_DIR}/submission-1.4-${dut}" ]] || die "Missing extracted folder for ${dut}"
  ok "Extracted submission-1.4-${dut}"
done

section "Task 1.4 - Structure Validation"
for dut in "${DUTS[@]}"; do
  validate_structure "${EXTRACT_DIR}/submission-1.4-${dut}" "$dut"
done

section "Task 1.4 - Runtime Smoke"
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
      run_smoke "${EXTRACT_DIR}/submission-1.4-${dut}" "$dut" "$sim"
    done
  done
fi

section "Task 1.4 - Optional Bug-Seed Campaign"
if [[ ${#BUG_SEED_LIST[@]} -eq 0 ]]; then
  warn "No --bug-seeds provided: skipping bug-seed campaign"
else
  if [[ "$SIM" == "both" ]]; then
    SIMULATORS=(icarus verilator)
  else
    SIMULATORS=("$SIM")
  fi

  for dut in "${DUTS[@]}"; do
    for sim in "${SIMULATORS[@]}"; do
      for seed in "${BUG_SEED_LIST[@]}"; do
        info "Running bug-seed ${seed} for ${dut} on ${sim}"
        run_bug_seed "${EXTRACT_DIR}/submission-1.4-${dut}" "$dut" "$sim" "$seed"
      done
    done
  done

  info "Bug-seed summary: total=${bug_total}, killed=${bug_killed}, survived=${bug_survived}"
fi

section "Task 1.4 - ZIP Status"
bash "${SCRIPT_DIR}/manage-1.4-submissions.sh" status

section "Done"
ok "Task 1.4 readiness verification completed"
