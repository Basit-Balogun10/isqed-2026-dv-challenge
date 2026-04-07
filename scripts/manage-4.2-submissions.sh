#!/usr/bin/env bash
# manage-4.2-submissions.sh - Task 4.2 packaging and integrity checks

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TASK_DIR="${PROJECT_ROOT}/submissions/task-4.2"
SUBMISSION_DIR="${TASK_DIR}/submission-4.2"
ZIP_DIR="${PROJECT_ROOT}/submissions/zips-4.2"
EXTRACT_DIR="/tmp/task-4.2-extracted-$$"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_pass()  { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_fail()  { echo -e "${RED}[FAIL]${NC} $*"; }

usage() {
  cat <<'EOF'
manage-4.2-submissions.sh - Task 4.2 packaging and integrity checks

Usage:
  ./scripts/manage-4.2-submissions.sh [command]

Commands:
  package        Create submission ZIP (submission-4.2.zip)
  extract        Extract ZIP to a temporary directory
  verify         Verify required file structure and content checks
  test-all       Run package -> extract -> verify
  status         Show current status
  clean          Remove temporary extraction directories
EOF
  exit "${1:-0}"
}

COMMAND="${1:-status}"
mkdir -p "${ZIP_DIR}"

required_files=(
  "agent/run_agent.py"
  "agent/agent_config.yaml"
  "agent/src"
  "methodology.md"
  "metadata.yaml"
  "Makefile"
  "README.md"
)

required_prompt_files=(
  "prompts/README.md"
  "prompts/01_task42_requirements_audit_prompt.md"
  "prompts/02_task42_schema_first_contract_prompt.md"
  "prompts/03_task42_reuse_mapping_prompt.md"
  "prompts/04_task42_regression_engine_prompt.md"
  "prompts/05_task42_readiness_and_packaging_prompt.md"
)

cmd_package() {
  local zip_file="${ZIP_DIR}/submission-4.2.zip"

  [[ -d "${SUBMISSION_DIR}" ]] || {
    log_fail "Submission directory not found: ${SUBMISSION_DIR}"
    return 1
  }

  [[ -f "${zip_file}" ]] && rm -f "${zip_file}"

  log_info "Packaging Task 4.2 submission"
  (
    cd "${TASK_DIR}"
    zip -r -q "${zip_file}" "submission-4.2" \
      -x "submission-4.2/**/__pycache__/*" \
      -x "submission-4.2/**/*.pyc" \
      -x "submission-4.2/.venv/*"
  )

  local size
  size="$(du -h "${zip_file}" | cut -f1)"
  log_pass "Created ${zip_file} (${size})"
}

cmd_extract() {
  local zip_file="${ZIP_DIR}/submission-4.2.zip"
  [[ -f "${zip_file}" ]] || {
    log_fail "ZIP not found: ${zip_file}"
    return 1
  }

  mkdir -p "${EXTRACT_DIR}"
  unzip -q "${zip_file}" -d "${EXTRACT_DIR}"
  log_pass "Extracted to ${EXTRACT_DIR}"
}

cmd_verify() {
  [[ -d "${SUBMISSION_DIR}" ]] || {
    log_fail "Submission directory not found: ${SUBMISSION_DIR}"
    return 1
  }

  local missing=()

  for rel in "${required_files[@]}"; do
    if [[ ! -e "${SUBMISSION_DIR}/${rel}" ]]; then
      missing+=("${rel}")
    fi
  done

  for rel in "${required_prompt_files[@]}"; do
    if [[ ! -f "${SUBMISSION_DIR}/${rel}" ]]; then
      missing+=("${rel}")
    fi
  done

  if ! grep -Eq 'task_id:[[:space:]]*"4\.2"' "${SUBMISSION_DIR}/metadata.yaml"; then
    missing+=("metadata.yaml task_id must be \"4.2\"")
  fi

  for target in compile simulate coverage run_agent clean; do
    if ! grep -Eq "^${target}:" "${SUBMISSION_DIR}/Makefile"; then
      missing+=("Makefile missing target ${target}")
    fi
  done

  if [[ ${#missing[@]} -gt 0 ]]; then
    log_fail "Submission verification failed"
    for item in "${missing[@]}"; do
      echo "  - ${item}"
    done
    return 1
  fi

  log_pass "Structure check passed"
}

cmd_status() {
  local zip_file="${ZIP_DIR}/submission-4.2.zip"

  echo "Task 4.2 Submission Status"
  echo "=========================="
  echo "Submission dir: ${SUBMISSION_DIR}"
  if [[ -d "${SUBMISSION_DIR}" ]]; then
    log_pass "Submission directory exists"
  else
    log_fail "Submission directory missing"
  fi

  if [[ -f "${zip_file}" ]]; then
    local size
    size="$(du -h "${zip_file}" | cut -f1)"
    log_pass "ZIP ready: ${zip_file} (${size})"
  else
    log_warn "ZIP not created yet: ${zip_file}"
  fi
}

cmd_test_all() {
  cmd_package
  cmd_extract
  cmd_verify
  log_pass "Task 4.2 package/extract/verify flow passed"
}

cmd_clean() {
  rm -rf /tmp/task-4.2-extracted-*
  log_pass "Removed temporary extraction directories"
}

case "${COMMAND}" in
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
  -h|--help)
    usage 0
    ;;
  *)
    log_fail "Unknown command: ${COMMAND}"
    usage 2
    ;;
esac
