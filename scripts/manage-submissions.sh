#!/usr/bin/env bash
#
# manage-submissions.sh — Submission packaging, extraction, and verification utility
#
# Purpose: Automated zip creation, extraction, and structure validation for
#          ISQED 2026 DV Challenge submissions (Task 1.1-4.3).
#
# Usage:
#   ./manage-submissions.sh [COMMAND] [OPTIONS]
#
# Commands:
#   package [DUT]         Create submission zips from task-1.1/submission-1.1-{DUT}/
#   extract [DUT]         Extract all submission zips to /tmp/extracted-submissions/
#   verify [DUT]          Check required files in submission structure
#   rebuild-all            Repackage all 3 DUTs (aegis_aes, rampart_i2c, sentinel_hmac)
#   clean                 Remove all temporary extraction/test directories
#   status                Show current submission status (size, timestamp, file count)
#
# Options (optional):
#   -d, --duts LIST       Comma-separated DUT names (default: aegis_aes,rampart_i2c,sentinel_hmac)
#   -o, --output PATH     Output directory for operations (default: project root)
#   -v, --verbose         Show detailed output
#   -h, --help            Show this message
#
# Examples:
#   ./manage-submissions.sh package aegis_aes
#   ./manage-submissions.sh extract -d aegis_aes,rampart_i2c
#   ./manage-submissions.sh rebuild-all
#   ./manage-submissions.sh verify --verbose
#   ./manage-submissions.sh status
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TASK_DIR="${PROJECT_ROOT}/submissions/task-1.1"
ZIP_DIR="${PROJECT_ROOT}/submissions/zips"
EXTRACT_DIR="/tmp/extracted-submissions-$$"

# Defaults
DUTS="aegis_aes rampart_i2c sentinel_hmac"
VERBOSE=false
OUTPUT_DIR="$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Helper functions
log_info()   { echo -e "${BLUE}[INFO]${NC} $*"; }
log_pass()   { echo -e "${GREEN}[✓]${NC} $*"; }
log_fail()   { echo -e "${RED}[✗]${NC} $*"; }
log_warn()   { echo -e "${YELLOW}[!]${NC} $*"; }
log_debug()  { [[ "$VERBOSE" == "true" ]] && echo -e "${CYAN}[DEBUG]${NC} $*"; }

usage() {
  grep "^#" "$0" | grep -v "^#!/" | sed 's/^# \?//'
  exit "${1:-0}"
}

# Parse arguments
COMMAND="${1:-status}"
shift || true

while [[ $# -gt 0 ]]; do
  case "$1" in
    -d|--duts)
      DUTS="${2//,/ }"
      shift 2
      ;;
    -o|--output)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    -v|--verbose)
      VERBOSE=true
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

# Ensure directories exist
mkdir -p "$ZIP_DIR"

# REQUIRED FILES in submission structure
REQUIRED_FILES=(
  "Makefile"
  "metadata.yaml"
  "methodology.md"
  "testbench/__init__.py"
  "testbench/tl_ul_agent.py"
  "testbench/scoreboard.py"
  "testbench/coverage.py"
  "testbench/env.py"
  "tests/__init__.py"
  "tests/test_basic.py"
)

# ============================================================================
# COMMAND IMPLEMENTATIONS
# ============================================================================

cmd_package() {
  local dut="${1:-all}"
  
  if [[ "$dut" == "all" ]]; then
    for d in $DUTS; do
      cmd_package "$d"
    done
    return 0
  fi
  
  # Validate DUT exists
  local submission_dir="${TASK_DIR}/submission-1.1-${dut}"
  if [[ ! -d "$submission_dir" ]]; then
    log_fail "Submission directory not found: $submission_dir"
    return 1
  fi
  
  # Create zip (exclude build artifacts)
  local zip_file="${ZIP_DIR}/submission-1.1-${dut}.zip"
  log_info "Packaging: $dut → $zip_file"
  
  # Remove existing zip to force clean rebuild
  [[ -f "$zip_file" ]] && rm -f "$zip_file"
  
  cd "$TASK_DIR"
  if zip -r -q "$zip_file" "submission-1.1-${dut}" \
      -x "submission-1.1-${dut}/sim_build/*" \
      -x "submission-1.1-${dut}/obj_dir/*" \
      -x "submission-1.1-${dut}/__pycache__/*" \
      -x "submission-1.1-${dut}/**/__pycache__/*" \
      -x "submission-1.1-${dut}/**/*.pyc" \
      2>/dev/null; then
    local size=$(du -h "$zip_file" | cut -f1)
    log_pass "Created: $zip_file ($size)"
  else
    log_fail "Failed to create zip: $zip_file"
    return 1
  fi
}

cmd_extract() {
  local dut="${1:-all}"
  
  if [[ "$dut" == "all" ]]; then
    for d in $DUTS; do
      cmd_extract "$d"
    done
    return 0
  fi
  
  local zip_file="${ZIP_DIR}/submission-1.1-${dut}.zip"
  if [[ ! -f "$zip_file" ]]; then
    log_fail "ZIP not found: $zip_file"
    return 1
  fi
  
  local extract_path="${EXTRACT_DIR}/submission-1.1-${dut}"
  mkdir -p "$EXTRACT_DIR"
  
  log_info "Extracting: $dut → $extract_path"
  if unzip -q "$zip_file" -d "$EXTRACT_DIR"; then
    log_pass "Extracted: $extract_path"
  else
    log_fail "Failed to extract: $zip_file"
    return 1
  fi
}

cmd_verify() {
  local dut="${1:-all}"
  local all_pass=true
  
  if [[ "$dut" == "all" ]]; then
    for d in $DUTS; do
      cmd_verify "$d" || all_pass=false
    done
    return $([[ "$all_pass" == "true" ]] && echo 0 || echo 1)
  fi
  
  log_info "Verifying: $dut"
  local submission_dir="${TASK_DIR}/submission-1.1-${dut}"
  
  if [[ ! -d "$submission_dir" ]]; then
    log_fail "Submission directory not found: $submission_dir"
    return 1
  fi
  
  local missing=()
  for file in "${REQUIRED_FILES[@]}"; do
    local full_path="${submission_dir}/${file}"
    if [[ ! -f "$full_path" ]]; then
      missing+=("$file")
      log_debug "  ✗ Missing: $file"
    else
      log_debug "  ✓ Found: $file"
    fi
  done
  
  if [[ ${#missing[@]} -eq 0 ]]; then
    log_pass "All required files present (${#REQUIRED_FILES[@]}/$(( ${#REQUIRED_FILES[@]} )))"
    return 0
  else
    log_fail "${#missing[@]} file(s) missing:"
    for file in "${missing[@]}"; do
      echo "    - $file"
    done
    return 1
  fi
}

cmd_rebuild_all() {
  log_info "Rebuilding all submission zips..."
  for dut in $DUTS; do
    cmd_verify "$dut" || { log_fail "Verification failed for $dut; skipping package"; continue; }
    cmd_package "$dut" || { log_fail "Packaging failed for $dut"; }
  done
  log_pass "Rebuild complete"
}

cmd_status() {
  log_info "SUBMISSION STATUS"
  echo "===================================================================="
  for dut in $DUTS; do
    local zip_file="${ZIP_DIR}/submission-1.1-${dut}.zip"
    local submission_dir="${TASK_DIR}/submission-1.1-${dut}"
    
    if [[ -f "$zip_file" ]]; then
      local size=$(du -h "$zip_file" | cut -f1)
      local timestamp=$(stat -c %y "$zip_file" | cut -d' ' -f1-2)
      local file_count=$(unzip -l "$zip_file" 2>/dev/null | tail -1 | awk '{print $2}')
      printf "%-15s | Size: %5s | Files: %2d | Updated: %s\n" \
        "$dut" "$size" "$file_count" "$timestamp"
    else
      printf "%-15s | ${RED}NOT FOUND${NC}\n" "$dut"
    fi
  done
  echo "===================================================================="
}

cmd_clean() {
  log_warn "Cleaning up temporary directories..."
  rm -rf /tmp/extracted-submissions-* /tmp/submission-test-*
  log_pass "Cleanup complete"
}

# ============================================================================
# MAIN
# ============================================================================

case "$COMMAND" in
  package)
    cmd_package "${1:-all}"
    ;;
  extract)
    cmd_extract "${1:-all}"
    echo "Extracted to: $EXTRACT_DIR"
    ;;
  verify)
    cmd_verify "${1:-all}"
    ;;
  rebuild-all)
    cmd_rebuild_all
    ;;
  status)
    cmd_status
    ;;
  clean)
    cmd_clean
    ;;
  *)
    log_fail "Unknown command: $COMMAND"
    usage 2
    ;;
esac
