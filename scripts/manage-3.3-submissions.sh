#!/usr/bin/env bash
#
# manage-3.3-submissions.sh - Task 3.3 packaging and integrity checks

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TASK_DIR="${PROJECT_ROOT}/submissions/task-3.3"
SUBMISSION_DIR="${TASK_DIR}/submission-3.3"
ZIP_DIR="${PROJECT_ROOT}/submissions/zips-3.3"
EXTRACT_DIR="/tmp/task-3.3-extracted-$$"

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
log_debug() {
  if [[ "${VERBOSE}" == "true" ]]; then
    echo -e "${CYAN}[DEBUG]${NC} $*"
  fi
}

usage() {
  cat <<'EOF'
manage-3.3-submissions.sh - Task 3.3 packaging and integrity checks

Usage:
  ./scripts/manage-3.3-submissions.sh [command] [options]

Commands:
  package        Create submission ZIP (submission-3.3.zip)
  extract        Extract ZIP to a temporary directory
  verify         Verify required file structure and content checks
  test-all       Run package -> extract -> verify
  status         Show current status
  clean          Remove temporary extraction directories

Options:
  -o, --output PATH   Output ZIP directory (default: submissions/zips-3.3)
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
  "bucketing.yaml"
  "bug_descriptions.yaml"
  "priority_ranking.yaml"
  "patch_validation.yaml"
  "methodology.md"
  "metadata.yaml"
  "Makefile"
  "analysis_scripts/validate_task33.py"
)

COMPATIBILITY_FILES=(
  "root_causes.md"
  "priority.yaml"
)

REQUIRED_PROMPT_FILES=(
  "prompts/README.md"
  "prompts/01_task33_audit_and_requirements.md"
  "prompts/02_input_inventory_and_failure_taxonomy.md"
  "prompts/03_bucketing_and_root_cause_mapping.md"
  "prompts/04_priority_and_patch_validation.md"
  "prompts/05_packaging_and_readiness_automation.md"
  "prompts/06_final_validation_and_signoff.md"
)

cmd_package() {
  local zip_file="${ZIP_DIR}/submission-3.3.zip"

  [[ -d "$SUBMISSION_DIR" ]] || {
    log_fail "Submission directory not found: $SUBMISSION_DIR"
    return 1
  }

  [[ -f "$zip_file" ]] && rm -f "$zip_file"

  log_info "Packaging Task 3.3 submission"
  (
    cd "$TASK_DIR"
    zip -r -q "$zip_file" "submission-3.3" \
      -x "submission-3.3/**/__pycache__/*" \
      -x "submission-3.3/**/*.pyc" \
      -x "submission-3.3/.venv/*"
  )

  local size file_count
  size="$(du -h "$zip_file" | cut -f1)"
  file_count="$(unzip -l "$zip_file" | tail -1 | awk '{print $2}')"
  log_pass "Created $zip_file ($size, $file_count files)"
}

cmd_extract() {
  local zip_file="${ZIP_DIR}/submission-3.3.zip"
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

  local missing=()

  for rel in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "${SUBMISSION_DIR}/${rel}" ]]; then
      missing+=("$rel")
    else
      log_debug "Found: $rel"
    fi
  done

  for rel in "${COMPATIBILITY_FILES[@]}"; do
    if [[ ! -f "${SUBMISSION_DIR}/${rel}" ]]; then
      missing+=("$rel")
    else
      log_debug "Found compatibility file: $rel"
    fi
  done

  for rel in "${REQUIRED_PROMPT_FILES[@]}"; do
    if [[ ! -f "${SUBMISSION_DIR}/${rel}" ]]; then
      missing+=("$rel")
    else
      log_debug "Found: $rel"
    fi
  done

  local prompts_md_count
  if [[ ! -d "${SUBMISSION_DIR}/prompts" ]]; then
    missing+=("prompts/ directory")
  else
    prompts_md_count="$(find "${SUBMISSION_DIR}/prompts" -maxdepth 1 -type f -name '*.md' | wc -l)"
    if [[ "$prompts_md_count" -ne 7 ]]; then
      missing+=("prompts/*.md (need exactly 7 files, found ${prompts_md_count})")
    fi

    if [[ -f "${SUBMISSION_DIR}/prompts/README.md" ]]; then
      if ! grep -q 'submissions/task-3.3/prompts.md' "${SUBMISSION_DIR}/prompts/README.md"; then
        missing+=("prompts/README.md must reference submissions/task-3.3/prompts.md")
      fi
      if ! grep -q 'https://github.com/' "${SUBMISSION_DIR}/prompts/README.md"; then
        missing+=("prompts/README.md must include GitHub master transcript URL")
      fi
    fi
  fi

  if ! grep -Eq 'task_id:[[:space:]]*"3\.3"' "${SUBMISSION_DIR}/metadata.yaml"; then
    missing+=("metadata.yaml task_id must be \"3.3\"")
  fi

  for target in compile simulate coverage clean; do
    if ! grep -Eq "^${target}:" "${SUBMISSION_DIR}/Makefile"; then
      missing+=("Makefile missing target ${target}")
    fi
  done

  if ! python3 "${SUBMISSION_DIR}/analysis_scripts/validate_task33.py" \
    --submission-dir "${SUBMISSION_DIR}" \
    --failure-details "${PROJECT_ROOT}/phase3_materials/task_3_3_regression/failure_details.yaml" \
    --patches-dir "${PROJECT_ROOT}/phase3_materials/task_3_3_regression/patches" >/dev/null 2>&1; then
    missing+=("analysis validation failed (run analysis_scripts/validate_task33.py)")
  fi

  if [[ ${#missing[@]} -gt 0 ]]; then
    log_fail "Submission verification failed"
    for item in "${missing[@]}"; do
      echo "  - $item"
    done
    return 1
  fi

  log_pass "Structure check passed (prompts=${prompts_md_count:-0}, required YAMLs present)"
}

cmd_status() {
  local zip_file="${ZIP_DIR}/submission-3.3.zip"

  echo "Task 3.3 Submission Status"
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
  cmd_verify
  log_pass "Task 3.3 package/extract/verify flow passed"
}

cmd_clean() {
  rm -rf /tmp/task-3.3-extracted-*
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
