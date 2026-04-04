#!/usr/bin/env bash
#
# manage-1.2-submissions.sh — Task 1.2 submission packaging & verification
#
# Automates:
# - Creating submission zips from source directories
# - Extracting and testing zips locally
# - Verifying submission structure integrity
# - Preparing final deliverables for platform upload
#
# Usage:
#   ./manage-1.2-submissions.sh [COMMAND] [OPTIONS]
#
# Commands:
#   package [DUT]          Create zip from submissions/task-1.2/submission-1.2-{DUT}/
#   extract [DUT]          Extract zip(s) to /tmp for testing
#   verify [DUT]           Check required files in submission
#   package-all            Zip all 3 DUTs (aegis_aes, sentinel_hmac, rampart_i2c)
#   extract-all            Extract all zips
#   test-all               Full end-to-end: package → extract → verify
#   status                 Show current submission status
#   clean                  Remove temporary directories
#
# Options (optional):
#   -d, --duts LIST        Comma-separated DUT names
#   -o, --output PATH      Output directory for zips (default: submissions/zips-1.2)
#   -v, --verbose          Detailed output
#   -h, --help             This message
#
# Examples:
#   ./manage-1.2-submissions.sh package-all
#   ./manage-1.2-submissions.sh extract-all --verbose
#   ./manage-1.2-submissions.sh verify aegis_aes
#   ./manage-1.2-submissions.sh test-all
#   ./manage-1.2-submissions.sh status

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TASK_DIR="${PROJECT_ROOT}/submissions/task-1.2"
ZIP_DIR="${PROJECT_ROOT}/submissions/zips-1.2"
EXTRACT_DIR="/tmp/task-1.2-extracted-$$"

# Defaults
DUTS="aegis_aes sentinel_hmac rampart_i2c"
VERBOSE=false

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
      ZIP_DIR="$2"
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

# REQUIRED FILES in Task 1.2 submission
REQUIRED_FILES=(
  "vplan_mapping.yaml"
  "metadata.yaml"
  "methodology.md"
  "Makefile"
  "testbench/__init__.py"
  "testbench/tl_ul_agent.py"
  "tests/__init__.py"
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
  local submission_dir="${TASK_DIR}/submission-1.2-${dut}"
  if [[ ! -d "$submission_dir" ]]; then
    log_fail "Submission directory not found: $submission_dir"
    return 1
  fi
  
  # Create zip (exclude build artifacts)
  local zip_file="${ZIP_DIR}/submission-1.2-${dut}.zip"
  log_info "Packaging: $dut → $zip_file"
  
  # Remove existing zip
  [[ -f "$zip_file" ]] && rm -f "$zip_file"
  
  cd "$TASK_DIR"
  if zip -r -q "$zip_file" "submission-1.2-${dut}" \
      -x "submission-1.2-${dut}/sim_build/*" \
      -x "submission-1.2-${dut}/obj_dir/*" \
      -x "submission-1.2-${dut}/__pycache__/*" \
      -x "submission-1.2-${dut}/**/__pycache__/*" \
      -x "submission-1.2-${dut}/**/*.pyc" \
      -x "submission-1.2-${dut}/results.xml" \
      -x "submission-1.2-${dut}/.venv/*" \
      2>/dev/null; then
    local size=$(du -h "$zip_file" | cut -f1)
    local file_count=$(unzip -l "$zip_file" 2>/dev/null | tail -1 | awk '{print $2}')
    log_pass "Created: $zip_file ($size, $file_count files)"
    return 0
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
    echo ""
    echo "Extracted submissions to: $EXTRACT_DIR"
    return 0
  fi
  
  local zip_file="${ZIP_DIR}/submission-1.2-${dut}.zip"
  if [[ ! -f "$zip_file" ]]; then
    log_fail "ZIP not found: $zip_file"
    return 1
  fi
  
  mkdir -p "$EXTRACT_DIR"
  log_info "Extracting: $dut → $EXTRACT_DIR"
  
  if unzip -q "$zip_file" -d "$EXTRACT_DIR"; then
    log_pass "Extracted: $dut"
    return 0
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
  local submission_dir="${TASK_DIR}/submission-1.2-${dut}"
  
  if [[ ! -d "$submission_dir" ]]; then
    log_fail "Submission directory not found: $submission_dir"
    return 1
  fi
  
  # Check required files
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
  
  # Count test files
  local test_count=$(find "${submission_dir}/tests" -name "test_vp_*.py" 2>/dev/null | wc -l)
  if [[ $test_count -eq 0 ]]; then
    missing+=("No test files found")
  else
    log_debug "  ✓ Found: $test_count test files"
  fi

  # Check prompt evidence directory
  local prompts_dir="${submission_dir}/prompts"
  if [[ ! -d "$prompts_dir" ]]; then
    missing+=("prompts/ directory missing")
  else
    local prompts_md_count
    prompts_md_count=$(find "$prompts_dir" -maxdepth 1 -type f -name "*.md" | wc -l)
    if [[ "$prompts_md_count" -lt 3 ]]; then
      missing+=("prompts/ needs at least 3 markdown files")
    fi
  fi
  
  if [[ ${#missing[@]} -eq 0 ]]; then
    log_pass "All required files present + $test_count test files"
    return 0
  else
    log_fail "${#missing[@]} issue(s) found:"
    for item in "${missing[@]}"; do
      echo "    - $item"
    done
    return 1
  fi
}

cmd_status() {
  log_info "SUBMISSION STATUS (Task 1.2)"
  echo "=================================================================="
  printf "%-20s | %-10s | %-10s | %s\n" "DUT" "ZIP Size" "Files" "Status"
  echo "=================================================================="
  
  for dut in $DUTS; do
    local submission_dir="${TASK_DIR}/submission-1.2-${dut}"
    local zip_file="${ZIP_DIR}/submission-1.2-${dut}.zip"
    
    if [[ ! -d "$submission_dir" ]]; then
      printf "%-20s | %-10s | %-10s | ${RED}NOT FOUND${NC}\n" "$dut" "N/A" "N/A"
      continue
    fi
    
    if [[ -f "$zip_file" ]]; then
      local size=$(du -h "$zip_file" | cut -f1)
      local file_count=$(unzip -l "$zip_file" 2>/dev/null | tail -1 | awk '{print $2}')
      printf "%-20s | %-10s | %-10s | ${GREEN}Ready${NC}\n" "$dut" "$size" "$file_count"
    else
      printf "%-20s | %-10s | %-10s | ${YELLOW}Not packaged${NC}\n" "$dut" "N/A" "N/A"
    fi
  done
  echo "=================================================================="
  
  # Show submission zips directory
  if [[ -d "$ZIP_DIR" ]]; then
    echo ""
    echo "📦 Submission zips location: $ZIP_DIR"
    echo "   Ready for upload to competition platform"
  fi
}

cmd_test_all() {
  log_info "Running full end-to-end: package → extract → verify"
  echo "=================================================================="
  echo ""
  
  # Step 1: Package
  log_info "Step 1: Packaging submissions..."
  cmd_package all || {
    log_fail "Packaging failed"
    return 1
  }
  echo ""
  
  # Step 2: Extract
  log_info "Step 2: Extracting submissions..."
  cmd_extract all || {
    log_fail "Extraction failed"
    return 1
  }
  echo ""
  
  # Step 3: Verify
  log_info "Step 3: Verifying submissions..."
  cmd_verify all || {
    log_fail "Verification failed"
    return 1
  }
  echo ""
  
  log_pass "End-to-end test PASSED ✓"
  return 0
}

cmd_clean() {
  log_warn "Removing temporary directories..."
  rm -rf /tmp/task-1.2-extracted-*
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
    ;;
  verify)
    cmd_verify "${1:-all}"
    ;;
  package-all)
    cmd_package all
    ;;
  extract-all)
    cmd_extract all
    ;;
  test-all)
    cmd_test_all
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
