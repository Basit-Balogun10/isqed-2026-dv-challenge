#!/usr/bin/env bash
#
# manage-2.2-submissions.sh - Task 2.2 packaging and integrity checks

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TASK_DIR="${PROJECT_ROOT}/submissions/task-2.2"
ZIP_DIR="${PROJECT_ROOT}/submissions/zips-2.2"
EXTRACT_DIR="/tmp/task-2.2-extracted-$$"

DUTS="aegis_aes sentinel_hmac rampart_i2c warden_timer"
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
manage-2.2-submissions.sh - Task 2.2 packaging and integrity checks

Usage:
  ./scripts/manage-2.2-submissions.sh [command] [options]

Commands:
  package [DUT]    Create zip for one DUT (or all)
  extract [DUT]    Extract zip for one DUT (or all)
  verify [DUT]     Verify required files and content checks (or all)
  package-all      Create zips for all Task 2.2 DUT submissions
  extract-all      Extract all Task 2.2 zips
  test-all         Run package-all -> extract-all -> verify-all
  status           Show current Task 2.2 packaging status
  clean            Remove temporary extraction directories

Options:
  -d, --duts LIST    Comma-separated DUT names
  -o, --output PATH  Output ZIP directory (default: submissions/zips-2.2)
  -v, --verbose      Verbose output
  -h, --help         Show this help
EOF
  exit "${1:-0}"
}

normalize_dut() {
  local dut="$1"
  dut="${dut#submission-2.2-}"
  echo "$dut"
}

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

mkdir -p "$ZIP_DIR"

REQUIRED_FILES=(
  "Makefile"
  "metadata.yaml"
  "methodology.md"
  "testbench/__init__.py"
  "testbench/tl_ul_agent.py"
  "tests/__init__.py"
  "tests/test_reference.py"
  "results/coverage_before.txt"
  "results/coverage_after.txt"
)

verify_one_submission() {
  local submission_dir="$1"
  local dut="$2"
  local missing=()

  local required_prompt_files=(
    "README.md"
    "01_task22_audit_and_planning.md"
    "02_stimulus_scaffolding_and_baseline_split.md"
    "03_coverage_execution_and_makefile_alignment.md"
    "04_gap_closure_and_debug_iterations.md"
    "05_packaging_and_readiness_automation.md"
    "06_final_audit_and_submission_signoff.md"
  )

  for rel in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "${submission_dir}/${rel}" ]]; then
      missing+=("$rel")
    else
      log_debug "Found: ${rel}"
    fi
  done

  if [[ ! -d "${submission_dir}/prompts" ]]; then
    missing+=("prompts/ directory")
  else
    local prompts_md_count
    prompts_md_count="$(find "${submission_dir}/prompts" -maxdepth 1 -type f -name '*.md' | wc -l)"
    if [[ "$prompts_md_count" -lt 7 ]]; then
      missing+=("prompts/*.md (need >=7, found ${prompts_md_count})")
    fi

    for rel in "${required_prompt_files[@]}"; do
      if [[ ! -f "${submission_dir}/prompts/${rel}" ]]; then
        missing+=("prompts/${rel}")
      fi
    done

    if [[ -f "${submission_dir}/prompts/README.md" ]]; then
      if ! grep -q 'submissions/task-2.2/prompts.md' "${submission_dir}/prompts/README.md"; then
        missing+=("prompts/README.md must reference submissions/task-2.2/prompts.md")
      fi
      if ! grep -q 'https://github.com/' "${submission_dir}/prompts/README.md"; then
        missing+=("prompts/README.md must include GitHub master transcript URL")
      fi
    fi
  fi

  local coverage_test_count
  coverage_test_count="$(find "${submission_dir}/tests" -maxdepth 1 -type f -name 'test_coverage_*.py' | wc -l)"
  if [[ "$coverage_test_count" -lt 1 ]]; then
    missing+=("tests/test_coverage_*.py (need >=1)")
  fi

  if ! grep -Eq 'task_id:[[:space:]]*"2\.2"' "${submission_dir}/metadata.yaml"; then
    missing+=("metadata.yaml task_id must be \"2.2\"")
  fi

  if ! grep -Eq "dut_id:[[:space:]]*\"${dut}\"" "${submission_dir}/metadata.yaml"; then
    missing+=("metadata.yaml dut_id must be \"${dut}\"")
  fi

  for target in compile simulate coverage clean; do
    if ! grep -Eq "^${target}:" "${submission_dir}/Makefile"; then
      missing+=("Makefile missing target ${target}")
    fi
  done

  if [[ ${#missing[@]} -gt 0 ]]; then
    log_fail "Verification failed for ${dut}"
    for item in "${missing[@]}"; do
      echo "  - ${item}"
    done
    return 1
  fi

  log_pass "${dut}: verification passed (coverage tests=${coverage_test_count})"
}

cmd_package() {
  local dut="${1:-all}"

  if [[ "$dut" == "all" ]]; then
    for d in $DUTS; do
      cmd_package "$d"
    done
    return 0
  fi

  dut="$(normalize_dut "$dut")"
  local submission_name="submission-2.2-${dut}"
  local submission_dir="${TASK_DIR}/${submission_name}"
  local zip_file="${ZIP_DIR}/${submission_name}.zip"

  [[ -d "$submission_dir" ]] || {
    log_fail "Submission directory not found: ${submission_dir}"
    return 1
  }

  [[ -f "$zip_file" ]] && rm -f "$zip_file"

  log_info "Packaging ${submission_name}"
  (
    cd "$TASK_DIR"
    zip -r -q "$zip_file" "$submission_name" \
      -x "${submission_name}/sim_build/*" \
      -x "${submission_name}/obj_dir/*" \
      -x "${submission_name}/results.xml" \
      -x "${submission_name}/__pycache__/*" \
      -x "${submission_name}/**/__pycache__/*" \
      -x "${submission_name}/**/*.pyc" \
      -x "${submission_name}/.venv/*"
  )

  local size file_count
  size="$(du -h "$zip_file" | cut -f1)"
  file_count="$(unzip -l "$zip_file" | tail -1 | awk '{print $2}')"
  log_pass "Created ${zip_file} (${size}, ${file_count} files)"
}

cmd_extract() {
  local dut="${1:-all}"

  if [[ "$dut" == "all" ]]; then
    for d in $DUTS; do
      cmd_extract "$d"
    done
    log_pass "Extracted all Task 2.2 zips to ${EXTRACT_DIR}"
    return 0
  fi

  dut="$(normalize_dut "$dut")"
  local zip_file="${ZIP_DIR}/submission-2.2-${dut}.zip"

  [[ -f "$zip_file" ]] || {
    log_fail "ZIP not found: ${zip_file}"
    return 1
  }

  mkdir -p "$EXTRACT_DIR"
  unzip -q "$zip_file" -d "$EXTRACT_DIR"
  log_pass "Extracted ${zip_file}"
}

cmd_verify() {
  local dut="${1:-all}"
  local all_pass=true

  if [[ "$dut" == "all" ]]; then
    for d in $DUTS; do
      cmd_verify "$d" || all_pass=false
    done
    [[ "$all_pass" == "true" ]]
    return
  fi

  dut="$(normalize_dut "$dut")"
  local submission_dir="${TASK_DIR}/submission-2.2-${dut}"

  [[ -d "$submission_dir" ]] || {
    log_fail "Submission directory not found: ${submission_dir}"
    return 1
  }

  verify_one_submission "$submission_dir" "$dut"
}

cmd_status() {
  echo "Task 2.2 Submission Status"
  echo "=========================="

  for dut in $DUTS; do
    local submission_name="submission-2.2-${dut}"
    local submission_dir="${TASK_DIR}/${submission_name}"
    local zip_file="${ZIP_DIR}/${submission_name}.zip"

    echo "- ${submission_name}"

    if [[ -d "$submission_dir" ]]; then
      log_pass "  source present"
    else
      log_fail "  source missing"
    fi

    if [[ -f "$zip_file" ]]; then
      local size
      size="$(du -h "$zip_file" | cut -f1)"
      log_pass "  zip ready: ${zip_file} (${size})"
    else
      log_warn "  zip missing: ${zip_file}"
    fi
  done
}

cmd_test_all() {
  cmd_package all
  cmd_extract all
  cmd_verify all
  log_pass "Task 2.2 package/extract/verify flow passed"
}

cmd_clean() {
  rm -rf /tmp/task-2.2-extracted-*
  log_pass "Removed temporary extraction directories"
}

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
    log_fail "Unknown command: ${COMMAND}"
    usage 2
    ;;
esac
