#!/usr/bin/env bash
#
# test-1.2-submissions.sh — Full validation of Task 1.2 submissions
#
# Performs all 4 automated evaluation checks:
# 1. Parse vplan_mapping.yaml — valid YAML + correct structure
# 2. All test functions exist — referenced tests callable
# 3. Run tests on clean RTL — no failures/timeouts
# 4. Coverage bins hit — claimed coverage paths execute
#
# Usage:
#   ./test-1.2-submissions.sh [OPTIONS] [dut1 dut2 ...]
#
# Options:
#   -s, --sim SIMULATOR     Test with (icarus, verilator, both) — default: both
#   -d, --duts LIST         Comma-separated DUTs — default: aegis_aes,sentinel_hmac,rampart_i2c
#   -w, --workdir PATH      Working directory — default: /tmp/task-1.2-test-$$
#   -t, --timeout SECONDS   Per-test timeout — default: 300
#   -v, --verbose           Show full output
#   -k, --keep-workdir      Keep working dir after tests
#   -h, --help              This message
#
# Exit codes:
#   0 = All checks PASS
#   1 = One or more checks FAIL
#   2 = Invalid arguments
#
# Examples:
#   ./test-1.2-submissions.sh                    # Test all with both simulators
#   ./test-1.2-submissions.sh -s icarus          # Test all with Icarus only
#   ./test-1.2-submissions.sh -s both --verbose  # Full output, both simulators
#   ./test-1.2-submissions.sh -d aegis_aes       # Test AES only

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Defaults
SIMULATORS="icarus verilator"
DUTS="aegis_aes sentinel_hmac rampart_i2c"
WORKDIR="/tmp/task-1.2-test-$$"
TIMEOUT=300
VERBOSE=false
KEEP_WORKDIR=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Counters
STATIC_CHECKS_PASSED=0
STATIC_CHECKS_FAILED=0
TESTS_PASSED=0
TESTS_FAILED=0
CHECK4_PASSED=0
CHECK4_FAILED=0

# Helper functions
log_info()   { echo -e "${BLUE}[INFO]${NC} $*"; }
log_pass()   { echo -e "${GREEN}[✓]${NC} $*"; }
log_fail()   { echo -e "${RED}[✗]${NC} $*"; }
log_warn()   { echo -e "${YELLOW}[!]${NC} $*"; }
log_test()   { echo -e "${CYAN}[TEST]${NC} $*"; }
log_debug()  { [[ "$VERBOSE" == "true" ]] && echo -e "${CYAN}[DEBUG]${NC} $*"; }
static_pass() { log_pass "$*"; STATIC_CHECKS_PASSED=$((STATIC_CHECKS_PASSED+1)); }
static_fail() { log_fail "$*"; STATIC_CHECKS_FAILED=$((STATIC_CHECKS_FAILED+1)); }

usage() {
  grep "^#" "$0" | grep -v "^#!/" | sed 's/^# \?//'
  exit "${1:-0}"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -s|--sim)
      if [[ "$2" == "both" ]]; then
        SIMULATORS="icarus verilator"
      else
        SIMULATORS="$2"
      fi
      shift 2
      ;;
    -d|--duts)
      DUTS="${2//,/ }"
      shift 2
      ;;
    -w|--workdir)
      WORKDIR="$2"
      shift 2
      ;;
    -t|--timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    -v|--verbose)
      VERBOSE=true
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
      log_fail "Unknown option: $1"
      usage 2
      ;;
  esac
done

# Setup
log_info "Setting up test environment..."
mkdir -p "$WORKDIR"
cd "$PROJECT_ROOT"

trap "
  if [[ \"\$KEEP_WORKDIR\" != \"true\" ]]; then
    rm -rf \"\$WORKDIR\"
    log_info \"Cleaned temporary directory\"
  else
    log_info \"Preserved working directory: $WORKDIR\"
  fi
" EXIT

# Activate venv
if [[ -f "${PROJECT_ROOT}/.venv/bin/activate" ]]; then
  source "${PROJECT_ROOT}/.venv/bin/activate"
  log_info "Python virtual environment activated"
fi

echo "====================================================================="
echo "TASK 1.2 AUTOMATED EVALUATION CHECKS"
echo "====================================================================="
echo

# ===========================================================================
# CHECK 1: Parse vplan_mapping.yaml
# ===========================================================================
echo -e "${BLUE}═══ CHECK 1: vplan_mapping.yaml Validation ═══${NC}"
echo

for dut in $DUTS; do
  vplan_file="${PROJECT_ROOT}/submissions/task-1.2/submission-1.2-${dut}/vplan_mapping.yaml"
  
  if [[ ! -f "$vplan_file" ]]; then
    static_fail "$dut — vplan_mapping.yaml NOT FOUND"
    continue
  fi
  
  # Validate YAML syntax
  if python3 -c "import yaml; yaml.safe_load(open('$vplan_file'))" 2>/dev/null; then
    static_pass "$dut — vplan_mapping.yaml is valid YAML"
  else
    static_fail "$dut — vplan_mapping.yaml has YAML syntax errors"
    continue
  fi
  
  # Validate structure
  YAML_CHECK=$(python3 << EOF
import yaml
with open('$vplan_file') as f:
    data = yaml.safe_load(f)
if not isinstance(data, dict):
    print("FAIL: Not a dict")
elif 'dut' not in data:
    print("FAIL: Missing 'dut' key")
elif 'mappings' not in data:
    print("FAIL: Missing 'mappings' key")
elif not isinstance(data['mappings'], list):
    print("FAIL: 'mappings' is not a list")
else:
    print("PASS")
EOF
)
  
  if [[ "$YAML_CHECK" == "PASS" ]]; then
    TOTAL_MAPPINGS=$(python3 -c "import yaml; data=yaml.safe_load(open('$vplan_file')); print(len(data['mappings']))")
    static_pass "$dut — vplan_mapping.yaml structure valid ($TOTAL_MAPPINGS mappings)"
  else
    static_fail "$dut — vplan_mapping.yaml structure error: $YAML_CHECK"
  fi
done

echo

# ===========================================================================
# CHECK 2: All test functions exist
# ===========================================================================
echo -e "${BLUE}═══ CHECK 2: Test Functions Exist ═══${NC}"
echo

for dut in $DUTS; do
  vplan_file="${PROJECT_ROOT}/submissions/task-1.2/submission-1.2-${dut}/vplan_mapping.yaml"
  tests_dir="${PROJECT_ROOT}/submissions/task-1.2/submission-1.2-${dut}/tests"
  
  if [[ ! -f "$vplan_file" ]]; then
    continue
  fi
  
  # Check each mapping
  EXIST_CHECK=$(python3 << EOF
import yaml
from pathlib import Path
vplan_file = '$vplan_file'
tests_dir = '$tests_dir'

with open(vplan_file) as f:
    data = yaml.safe_load(f)

missing = []
for mapping in data.get('mappings', []):
    vp_id = mapping.get('vp_id')
    test_name = mapping.get('test_name')
    
    if '::' not in test_name:
        missing.append(f"{vp_id}: Invalid test_name format (missing ::)")
        continue
    
    module_path, func_name = test_name.split('::')
    module_parts = module_path.split('.')
    test_file = Path(tests_dir) / f"{module_parts[-1]}.py"
    
    if not test_file.exists():
        missing.append(f"{vp_id}: File {test_file.name} not found")
        continue
    
    # Check if function exists
    with open(test_file) as f:
        content = f.read()
    if f'async def {func_name}' not in content:
        missing.append(f"{vp_id}: Function {func_name} not found")
    elif '@cocotb.test()' not in content:
        missing.append(f"{vp_id}: @cocotb.test() decorator missing")

if missing:
    print("\n".join(missing))
else:
    print("ALL_PASS")
EOF
)
  
  if [[ "$EXIST_CHECK" == "ALL_PASS" ]]; then
    TOTAL=$(python3 -c "import yaml; data=yaml.safe_load(open('$vplan_file')); print(len(data['mappings']))")
    static_pass "$dut — All $TOTAL test functions exist and decorated"
  else
    static_fail "$dut — Some test functions missing:"
    echo "$EXIST_CHECK" | sed 's/^/    /'
  fi
done

echo

# ===========================================================================
# CHECK 3 & 4: Run tests on clean RTL + runtime coverage validation
# ===========================================================================
echo -e "${BLUE}═══ CHECK 3 & 4: Test Execution + Runtime Coverage ═══${NC}"
echo

for sim in $SIMULATORS; do
  echo
  log_info "Simulator: $sim"
  echo "---"
  
  for dut in $DUTS; do
    submission_dir="${PROJECT_ROOT}/submissions/task-1.2/submission-1.2-${dut}"
    
    if [[ ! -d "$submission_dir" ]]; then
      log_fail "$dut@$sim — Submission directory not found"
      TESTS_FAILED=$((TESTS_FAILED + 1))
      continue
    fi
    
    # Check Makefile
    if [[ ! -f "${submission_dir}/Makefile" ]]; then
      log_fail "$dut@$sim — Makefile not found"
      TESTS_FAILED=$((TESTS_FAILED + 1))
      continue
    fi
    
    cd "$submission_dir"
    log_test "$dut@$sim — Compiling..."
    
    # Clean build directory
    rm -rf sim_build obj_dir
    
    # Run make (with timeout)
    TEST_LOG="${WORKDIR}/${dut}_${sim}.log"
    COVERAGE_JSON="${WORKDIR}/${dut}_${sim}_runtime_coverage.json"
    rm -f "$COVERAGE_JSON"
    mkdir -p "$(dirname "$TEST_LOG")"
    
    if TASK12_RUNTIME_COVERAGE_FILE="$COVERAGE_JSON" timeout $TIMEOUT make SIM=$sim > "$TEST_LOG" 2>&1; then
      # Parse the cocotb summary line instead of grepping generic PASS/FAIL tokens.
      SUMMARY_LINE=$(grep -E "\*\* TESTS=" "$TEST_LOG" | tail -1)
      if [[ -n "$SUMMARY_LINE" ]]; then
        DUT_TESTS=$(echo "$SUMMARY_LINE" | sed -n 's/.*TESTS=\([0-9]\+\).*/\1/p')
        DUT_PASS=$(echo "$SUMMARY_LINE" | sed -n 's/.*PASS=\([0-9]\+\).*/\1/p')
        DUT_FAIL=$(echo "$SUMMARY_LINE" | sed -n 's/.*FAIL=\([0-9]\+\).*/\1/p')
      else
        DUT_TESTS=""
        DUT_PASS=""
        DUT_FAIL=""
      fi

      if [[ -n "$DUT_TESTS" ]] && [[ -n "$DUT_FAIL" ]] && [[ "$DUT_FAIL" -eq 0 ]] && [[ "$DUT_TESTS" -gt 0 ]]; then
        log_pass "$dut@$sim — TESTS=$DUT_TESTS PASS=$DUT_PASS FAIL=$DUT_FAIL (CHECK 3 ✓)"
        TESTS_PASSED=$((TESTS_PASSED + DUT_PASS))

        if python3 "${SCRIPT_DIR}/task_1_2_runtime_check4.py" \
            --mapping "${submission_dir}/vplan_mapping.yaml" \
            --runtime-coverage "$COVERAGE_JSON" \
            --dut "$dut" \
            --sim "$sim"; then
          CHECK4_PASSED=$((CHECK4_PASSED + 1))
        else
          CHECK4_FAILED=$((CHECK4_FAILED + 1))
          TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
      else
        if [[ -n "$DUT_TESTS" ]] && [[ -n "$DUT_FAIL" ]]; then
          log_fail "$dut@$sim — TESTS=$DUT_TESTS PASS=$DUT_PASS FAIL=$DUT_FAIL"
          TESTS_FAILED=$((TESTS_FAILED + DUT_FAIL))
        else
          log_fail "$dut@$sim — Missing cocotb TESTS summary line"
          TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
        if [[ "$VERBOSE" == "true" ]]; then
          tail -30 "$TEST_LOG" | sed 's/^/    /'
        fi
      fi
    else
      log_fail "$dut@$sim — Timeout (${TIMEOUT}s) or compilation error"
      TESTS_FAILED=$((TESTS_FAILED + 1))
      if [[ "$VERBOSE" == "true" ]]; then
        tail -30 "$TEST_LOG" | sed 's/^/    /'
      fi
    fi
  done
done

cd "$PROJECT_ROOT"
echo

# ===========================================================================
# SUMMARY
# ===========================================================================
echo "====================================================================="
echo -e "${BLUE}EVALUATION SUMMARY${NC}"
echo "====================================================================="
echo
echo -e "CHECK 1+2 (Static Checks):  ${GREEN}$STATIC_CHECKS_PASSED${NC} passed, ${RED}$STATIC_CHECKS_FAILED${NC} failed"
echo -e "CHECK 3 (Tests Pass):       ${GREEN}$TESTS_PASSED${NC} tests passed, ${RED}$TESTS_FAILED${NC} tests failed"
echo -e "CHECK 4 (Runtime Coverage): ${GREEN}$CHECK4_PASSED${NC} job(s) passed, ${RED}$CHECK4_FAILED${NC} job(s) failed"
echo
if [[ $STATIC_CHECKS_FAILED -eq 0 ]] && [[ $TESTS_FAILED -eq 0 ]]; then
  echo -e "${GREEN}✓ ALL CHECKS PASSED — Ready for submission${NC}"
  echo "====================================================================="
  exit 0
else
  echo -e "${RED}✗ SOME CHECKS FAILED — Review errors above${NC}"
  echo "====================================================================="
  exit 1
fi
