#!/usr/bin/env bash
#
# test-submission.sh — Automated submission reverse-testing & packaging script
# 
# Purpose: Extract, test, and repackage submission zips for dual-simulator compliance
#          (Icarus Verilog + Verilator) before platform upload.
#
# Usage:
#   ./test-submission.sh [OPTIONS] [dut1 dut2 ...]
#
# Options:
#   -s, --sim SIMULATOR     Test with specific simulator (icarus, verilator, both)
#   -d, --duts LIST         Comma-separated DUT names (default: all)
#   -w, --workdir PATH      Temporary working directory (default: /tmp/submission-test-$$)
#   -t, --timeout SECONDS   Timeout per test (default: 180)
#   -v, --verbose           Show full make output (default: tail last 50 lines)
#   -k, --keep-workdir      Preserve working directory after tests
#   -h, --help              Show this message
#
# Examples:
#   ./test-submission.sh -s icarus
#   ./test-submission.sh -s both -d aegis_aes,rampart_i2c
#   ./test-submission.sh --verbose --keep-workdir
#
# Exit Codes:
#   0 = All tests passed
#   1 = One or more tests failed/timed out
#   2 = Invalid arguments
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SUBMISSIONS_DIR="${PROJECT_ROOT}/submissions/zips"
DUTS_DIR="${PROJECT_ROOT}/duts"

# Defaults
SIMULATORS="icarus"
DUTS="aegis_aes rampart_i2c sentinel_hmac"
WORKDIR="/tmp/submission-test-$$"
TIMEOUT=180
VERBOSE=false
KEEP_WORKDIR=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info()   { echo -e "${BLUE}[INFO]${NC} $*"; }
log_pass()   { echo -e "${GREEN}[PASS]${NC} $*"; }
log_fail()   { echo -e "${RED}[FAIL]${NC} $*"; }
log_warn()   { echo -e "${YELLOW}[WARN]${NC} $*"; }

usage() {
  grep "^#" "$0" | grep -v "^#!/" | sed 's/^# \?//'
  exit "${1:-0}"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -s|--sim)
      SIMULATORS="$2"
      [[ "$SIMULATORS" == "both" ]] && SIMULATORS="icarus verilator"
      shift 2
      ;;
    -d|--duts)
      DUTS="${2//,/ }"  # Replace commas with spaces
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
[[ -d "$DUTS_DIR" ]] || { log_fail "DUTs directory not found: $DUTS_DIR"; exit 1; }
[[ -d "$SUBMISSIONS_DIR" ]] || { log_fail "Submissions directory not found: $SUBMISSIONS_DIR"; exit 1; }

trap "
  if [[ \"\$KEEP_WORKDIR\" != \"true\" ]]; then
    rm -rf \"\$WORKDIR\"
    log_info \"Cleaned up $WORKDIR\"
  else
    log_info \"Keeping working directory: $WORKDIR\"
  fi
" EXIT

# Activate virtual environment if available
if [[ -f "${SCRIPT_DIR}/.venv/bin/activate" ]]; then
  source "${SCRIPT_DIR}/.venv/bin/activate"
  log_info "Virtual environment activated"
fi

# Main test loop
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

declare -A results

log_info "Starting reverse-tests: SIM=[${SIMULATORS}] DUTs=[${DUTS}]"
echo "======================================================================"

for sim in $SIMULATORS; do
  echo
  log_info "SIMULATOR: $sim"
  echo "======================================================================"
  
  for dut in $DUTS; do
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    TEST_NAME="${dut}@${sim}"
    ZIP_FILE="${SUBMISSIONS_DIR}/submission-1.1-${dut}.zip"
    
    # Verify zip exists
    if [[ ! -f "$ZIP_FILE" ]]; then
      log_fail "$TEST_NAME — ZIP not found: $ZIP_FILE"
      results[$TEST_NAME]="SKIP"
      FAILED_TESTS=$((FAILED_TESTS + 1))
      continue
    fi
    
    # Extract and test
    EXTRACT_SUBDIR="${WORKDIR}/extract-${dut}-${sim}"
    rm -rf "$EXTRACT_SUBDIR"
    mkdir -p "$EXTRACT_SUBDIR"
    unzip -q "$ZIP_FILE" -d "$EXTRACT_SUBDIR" 2>/dev/null || {
      log_fail "$TEST_NAME — Failed to extract ZIP"
      results[$TEST_NAME]="FAIL"
      FAILED_TESTS=$((FAILED_TESTS + 1))
      continue
    }
    
    # Find the extracted submission directory (unzip extracts top-level dir)
    TESTDIR=$(find "$EXTRACT_SUBDIR" -maxdepth 1 -type d -name "submission-1.1-*" | head -1)
    if [[ -z "$TESTDIR" ]]; then
      log_fail "$TEST_NAME — Could not find extracted submission directory"
      results[$TEST_NAME]="FAIL"
      FAILED_TESTS=$((FAILED_TESTS + 1))
      continue
    fi
    
    cd "$TESTDIR" || { log_fail "$TEST_NAME — Failed to cd into test dir: $TESTDIR"; results[$TEST_NAME]="FAIL"; FAILED_TESTS=$((FAILED_TESTS + 1)); continue; }
    
    # Run make
    if [[ "$VERBOSE" == "true" ]]; then
      log_info "$TEST_NAME — Running make..."
      if timeout $TIMEOUT make SIM=$sim 2>&1 | tee make.log; then
        PASS_COUNT=$(grep -c "PASS=3" make.log || echo 0)
        if [[ $PASS_COUNT -gt 0 ]]; then
          log_pass "$TEST_NAME — 3/3 tests passed"
          results[$TEST_NAME]="PASS"
          PASSED_TESTS=$((PASSED_TESTS + 1))
        else
          log_fail "$TEST_NAME — Tests did not pass as expected"
          results[$TEST_NAME]="FAIL"
          FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
      else
        log_fail "$TEST_NAME — Timeout or compilation error"
        results[$TEST_NAME]="FAIL"
        FAILED_TESTS=$((FAILED_TESTS + 1))
      fi
    else
      # Non-verbose: capture output and grep for result
      if timeout $TIMEOUT make SIM=$sim > make.log 2>&1; then
        if grep -q "PASS=3" make.log; then
          log_pass "$TEST_NAME — 3/3 tests passed"
          results[$TEST_NAME]="PASS"
          PASSED_TESTS=$((PASSED_TESTS + 1))
        else
          log_fail "$TEST_NAME — Tests did not pass"
          tail -20 make.log | sed 's/^/  /'
          results[$TEST_NAME]="FAIL"
          FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
      else
        log_fail "$TEST_NAME — Timeout (${TIMEOUT}s) or compilation error"
        tail -20 make.log | sed 's/^/  /'
        results[$TEST_NAME]="FAIL"
        FAILED_TESTS=$((FAILED_TESTS + 1))
      fi
    fi
  done
done

# Summary report
echo
echo "======================================================================"
log_info "TEST SUMMARY"
echo "======================================================================"
printf "%-30s | %-10s\n" "TEST" "RESULT"
echo "--------------------------------------------------------------------"
for test_name in "${!results[@]}"; do
  result="${results[$test_name]}"
  if [[ "$result" == "PASS" ]]; then
    printf "%-30s | ${GREEN}%-10s${NC}\n" "$test_name" "$result"
  else
    printf "%-30s | ${RED}%-10s${NC}\n" "$test_name" "$result"
  fi
done | sort
echo "--------------------------------------------------------------------"
printf "${GREEN}PASSED${NC}: %d | ${RED}FAILED${NC}: %d | TOTAL: %d\n" \
  "$PASSED_TESTS" "$FAILED_TESTS" "$TOTAL_TESTS"
echo "======================================================================"

# Exit with appropriate code
if [[ $FAILED_TESTS -eq 0 ]]; then
  log_pass "All tests passed!"
  exit 0
else
  log_fail "$FAILED_TESTS test(s) failed"
  exit 1
fi
