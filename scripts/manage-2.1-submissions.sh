#!/usr/bin/env bash
#
# manage-2.1-submissions.sh - Task 2.1 packaging and integrity checks

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TASK_DIR="${PROJECT_ROOT}/submissions/task-2.1"
SUBMISSION_DIR="${TASK_DIR}/submission-2.1"
ZIP_DIR="${PROJECT_ROOT}/submissions/zips-2.1"
EXTRACT_DIR="/tmp/task-2.1-extracted-$$"

VERBOSE=false

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_pass()  { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_fail()  { echo -e "${RED}[FAIL]${NC} $*"; }
log_debug() { [[ "${VERBOSE}" == "true" ]] && echo -e "${CYAN}[DEBUG]${NC} $*"; }

usage() {
  cat <<'EOF'
manage-2.1-submissions.sh - Task 2.1 packaging and integrity checks

Usage:
  ./scripts/manage-2.1-submissions.sh [command] [options]

Commands:
  package        Create submission ZIP (submission-2.1.zip)
  extract        Extract ZIP to a temporary directory
  verify         Verify required file structure and content checks
  test-all       Run package -> extract -> verify
  status         Show current status
  clean          Remove temporary extraction directories

Options:
  -o, --output PATH   Output ZIP directory (default: submissions/zips-2.1)
  -v, --verbose       Verbose output
  -h, --help          Show this help
EOF
  exit "${1:-0}"
}

COMMAND="${1:-status}"
shift || true

while [[ $# -gt 0 ]]; do
  case "$1" in
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

mkdir -p "$ZIP_DIR"

REQUIRED_FILES=(
  "Makefile"
  "metadata.yaml"
  "methodology.md"
  "gap_analysis.yaml"
  "gap_summary.md"
  "closure_plan.md"
  "summary.md"
  "priority_table.yaml"
  "analysis_scripts/collect_baseline_coverage.sh"
  "analysis_scripts/summarize_coverage.py"
  "analysis_scripts/generate_gap_deliverables.py"
)

verify_submission_tree() {
  local root="$1"
  local missing=()

  for rel in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "${root}/${rel}" ]]; then
      missing+=("$rel")
    else
      log_debug "Found: ${rel}"
    fi
  done

  [[ -d "${root}/gap_analysis" ]] || missing+=("gap_analysis/ directory")
  [[ -d "${root}/prompts" ]] || missing+=("prompts/ directory")

  local dut_gap_count
  dut_gap_count="$(find "${root}/gap_analysis" -maxdepth 1 -type f -name '*_gaps.md' 2>/dev/null | wc -l)"
  if [[ "$dut_gap_count" -lt 7 ]]; then
    missing+=("gap_analysis/*_gaps.md (need >=7, found ${dut_gap_count})")
  fi

  local prompt_md_count
  prompt_md_count="$(find "${root}/prompts" -maxdepth 1 -type f -name '*.md' 2>/dev/null | wc -l)"
  if [[ "$prompt_md_count" -lt 5 ]]; then
    missing+=("prompts/*.md (need >=5, found ${prompt_md_count})")
  fi

  if ! grep -Eq 'task_id:[[:space:]]*"2\.1"' "${root}/metadata.yaml"; then
    missing+=("metadata.yaml task_id must be \"2.1\"")
  fi

  for target in compile simulate coverage clean; do
    if ! grep -Eq "^${target}:" "${root}/Makefile"; then
      missing+=("Makefile missing target: ${target}")
    fi
  done

  if [[ ${#missing[@]} -gt 0 ]]; then
    log_fail "Verification failed"
    for item in "${missing[@]}"; do
      echo "  - ${item}"
    done
    return 1
  fi

  log_pass "Structure check passed (dut gap files=${dut_gap_count}, prompts=${prompt_md_count})"
}

cmd_package() {
  local zip_file="${ZIP_DIR}/submission-2.1.zip"

  [[ -d "$SUBMISSION_DIR" ]] || {
    log_fail "Submission directory not found: $SUBMISSION_DIR"
    return 1
  }

  [[ -f "$zip_file" ]] && rm -f "$zip_file"

  log_info "Packaging Task 2.1 submission"
  (
    cd "$TASK_DIR"
    zip -r -q "$zip_file" "submission-2.1" \
      -x "submission-2.1/sim_build/*" \
      -x "submission-2.1/obj_dir/*" \
      -x "submission-2.1/baseline_artifacts/*/annotated/*" \
      -x "submission-2.1/results.xml" \
      -x "submission-2.1/__pycache__/*" \
      -x "submission-2.1/**/__pycache__/*" \
      -x "submission-2.1/**/*.pyc" \
      -x "submission-2.1/.venv/*"
  )

  local size file_count
  size="$(du -h "$zip_file" | cut -f1)"
  file_count="$(unzip -l "$zip_file" | tail -1 | awk '{print $2}')"
  log_pass "Created $zip_file ($size, $file_count files)"
}

cmd_extract() {
  local zip_file="${ZIP_DIR}/submission-2.1.zip"
  [[ -f "$zip_file" ]] || {
    log_fail "ZIP not found: $zip_file"
    return 1
  }

  mkdir -p "$EXTRACT_DIR"
  unzip -q "$zip_file" -d "$EXTRACT_DIR"
  log_pass "Extracted to $EXTRACT_DIR"
}

cmd_verify() {
  [[ -d "$SUBMISSION_DIR" ]] || {
    log_fail "Submission directory not found: $SUBMISSION_DIR"
    return 1
  }

  verify_submission_tree "$SUBMISSION_DIR"
}

cmd_status() {
  local zip_file="${ZIP_DIR}/submission-2.1.zip"

  echo "Task 2.1 Submission Status"
  echo "=========================="
  echo "Submission dir: $SUBMISSION_DIR"
  if [[ -d "$SUBMISSION_DIR" ]]; then
    log_pass "Submission directory exists"
  else
    log_fail "Submission directory missing"
  fi

  if [[ -f "$zip_file" ]]; then
    local size
    size="$(du -h "$zip_file" | cut -f1)"
    log_pass "ZIP ready: $zip_file ($size)"
  else
    log_warn "ZIP not created yet: $zip_file"
  fi
}

cmd_test_all() {
  cmd_package
  cmd_extract
  verify_submission_tree "${EXTRACT_DIR}/submission-2.1"
  log_pass "Task 2.1 package/extract/verify flow passed"
}

cmd_clean() {
  rm -rf /tmp/task-2.1-extracted-*
  log_pass "Removed temporary extraction directories"
}

case "$COMMAND" in
  package)
    cmd_package
    ;;
  extract)
    cmd_extract
    ;;
  verify)
    cmd_verify
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
