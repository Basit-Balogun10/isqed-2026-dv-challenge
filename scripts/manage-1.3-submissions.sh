#!/usr/bin/env bash
#
# manage-1.3-submissions.sh - Task 1.3 packaging and integrity checks

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TASK_DIR="${PROJECT_ROOT}/submissions/task-1.3"
SUBMISSION_DIR="${TASK_DIR}/submission-1.3"
ZIP_DIR="${PROJECT_ROOT}/submissions/zips-1.3"
EXTRACT_DIR="/tmp/task-1.3-extracted-$$"

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
manage-1.3-submissions.sh - Task 1.3 packaging and integrity checks

Usage:
  ./scripts/manage-1.3-submissions.sh [command] [options]

Commands:
  package        Create submission ZIP (submission-1.3.zip)
  extract        Extract ZIP to a temporary directory
  verify         Verify required file structure and generated outputs
  test-all       Run package -> extract -> verify
  status         Show current status
  clean          Remove temporary extraction directories

Options:
  -o, --output PATH   Output ZIP directory (default: submissions/zips-1.3)
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
  "generator/csr_test_generator.py"
  "generated_tests/__init__.py"
)

cmd_package() {
  local zip_file="${ZIP_DIR}/submission-1.3.zip"

  [[ -d "$SUBMISSION_DIR" ]] || {
    log_fail "Submission directory not found: $SUBMISSION_DIR"
    return 1
  }

  [[ -f "$zip_file" ]] && rm -f "$zip_file"

  log_info "Packaging Task 1.3 submission"
  (
    cd "$TASK_DIR"
    zip -r -q "$zip_file" "submission-1.3" \
      -x "submission-1.3/sim_build/*" \
      -x "submission-1.3/obj_dir/*" \
      -x "submission-1.3/results.xml" \
      -x "submission-1.3/__pycache__/*" \
      -x "submission-1.3/**/__pycache__/*" \
      -x "submission-1.3/**/*.pyc" \
      -x "submission-1.3/.venv/*"
  )

  local size file_count
  size="$(du -h "$zip_file" | cut -f1)"
  file_count="$(unzip -l "$zip_file" | tail -1 | awk '{print $2}')"
  log_pass "Created $zip_file ($size, $file_count files)"
}

cmd_extract() {
  local zip_file="${ZIP_DIR}/submission-1.3.zip"
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

  local generated_count
  generated_count="$(find "${SUBMISSION_DIR}/generated_tests" -maxdepth 1 -type f -name 'test_csr_*.py' | wc -l)"
  if [[ "$generated_count" -lt 3 ]]; then
    missing+=("generated_tests/test_csr_*.py (need >=3, found ${generated_count})")
  fi

  local csr_map_count
  csr_map_count="$(find "${SUBMISSION_DIR}/csr_maps" -maxdepth 1 -type f -name '*_csr.hjson' 2>/dev/null | wc -l)"
  if [[ "$csr_map_count" -lt 3 ]]; then
    missing+=("csr_maps/*_csr.hjson (need >=3, found ${csr_map_count})")
  fi

  if [[ ! -d "${SUBMISSION_DIR}/prompts" ]]; then
    missing+=("prompts/ directory")
  else
    local prompt_count
    prompt_count="$(find "${SUBMISSION_DIR}/prompts" -maxdepth 1 -type f -name '*.md' | wc -l)"
    if [[ "$prompt_count" -lt 6 ]]; then
      missing+=("prompts/*.md (need >=6, found ${prompt_count})")
    fi

    if [[ ! -f "${SUBMISSION_DIR}/prompts/README.md" ]]; then
      missing+=("prompts/README.md")
    fi

    local prompt_chunk_count
    prompt_chunk_count="$(find "${SUBMISSION_DIR}/prompts" -maxdepth 1 -type f -name '[0-9][0-9]_*.md' | wc -l)"
    if [[ "$prompt_chunk_count" -lt 5 ]]; then
      missing+=("prompts/[0-9][0-9]_*.md (need >=5, found ${prompt_chunk_count})")
    fi
  fi

  if [[ ${#missing[@]} -gt 0 ]]; then
    log_fail "Submission verification failed"
    for item in "${missing[@]}"; do
      echo "  - $item"
    done
    return 1
  fi

  log_pass "Structure check passed (generated tests: ${generated_count}, csr maps: ${csr_map_count})"
}

cmd_status() {
  local zip_file="${ZIP_DIR}/submission-1.3.zip"

  echo "Task 1.3 Submission Status"
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
  log_pass "Task 1.3 package/extract/verify flow passed"
}

cmd_clean() {
  rm -rf /tmp/task-1.3-extracted-*
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
