#!/usr/bin/env bash
#
# verify-2.1-readiness.sh
#
# ZIP-first readiness verification for Task 2.1 submission.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

QUICK=false
KEEP_WORKDIR=false
TIMEOUT=600
SIM="both"
WORKDIR="/tmp/verify-2.1-$$"
EXTRACT_DIR="${WORKDIR}/extracted"

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
verify-2.1-readiness.sh

Usage:
  bash scripts/verify-2.1-readiness.sh [options]

Options:
  --sim {icarus|verilator|both}   Accepted for interface compatibility (not used)
  --quick                         Skip report regeneration smoke
  --timeout SECONDS               Command timeout (default: 600)
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

if ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]]; then
  die "Invalid --timeout value '${TIMEOUT}' (must be integer seconds)"
fi

if [[ "$SIM" != "icarus" && "$SIM" != "verilator" && "$SIM" != "both" ]]; then
  die "Invalid --sim value '${SIM}' (expected: icarus|verilator|both)"
fi

cleanup() {
  if [[ "$KEEP_WORKDIR" == "true" ]]; then
    warn "Keeping workdir: $WORKDIR"
  else
    rm -rf "$WORKDIR"
  fi
}
trap cleanup EXIT

mkdir -p "$EXTRACT_DIR"
cd "$PROJECT_ROOT"

section "Environment"
if [[ -f "${PROJECT_ROOT}/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${PROJECT_ROOT}/.venv/bin/activate"
  ok "Python virtual environment activated"
else
  die "Missing expected venv at ${PROJECT_ROOT}/.venv"
fi

section "Task 2.1 - Package ZIP"
bash "${SCRIPT_DIR}/manage-2.1-submissions.sh" package
ok "Task 2.1 ZIP package created"

section "Task 2.1 - Extract ZIP"
ZIP_FILE="${PROJECT_ROOT}/submissions/zips-2.1/submission-2.1.zip"
[[ -f "$ZIP_FILE" ]] || die "Missing ZIP: $ZIP_FILE"
unzip -q "$ZIP_FILE" -d "$EXTRACT_DIR"
SUBMISSION_EXTRACTED="${EXTRACT_DIR}/submission-2.1"
[[ -d "$SUBMISSION_EXTRACTED" ]] || die "Extracted submission root missing"
ok "ZIP extracted to $SUBMISSION_EXTRACTED"

section "Task 2.1 - Structure Validation"
required_files=(
  "Makefile"
  "metadata.yaml"
  "methodology.md"
  "gap_analysis.yaml"
  "gap_summary.md"
  "closure_plan.md"
  "summary.md"
  "priority_table.yaml"
  "analysis_scripts/summarize_coverage.py"
  "analysis_scripts/generate_gap_deliverables.py"
)

for rel in "${required_files[@]}"; do
  [[ -f "${SUBMISSION_EXTRACTED}/${rel}" ]] || die "Missing required file: ${rel}"
done

[[ -d "${SUBMISSION_EXTRACTED}/gap_analysis" ]] || die "Missing gap_analysis/ directory"
[[ -d "${SUBMISSION_EXTRACTED}/prompts" ]] || die "Missing prompts/ directory"

rtl_file_count="$(find "${SUBMISSION_EXTRACTED}" -type f \( -name '*.sv' -o -name '*.v' -o -name '*.svh' -o -name '*.vh' \) | wc -l)"
[[ "$rtl_file_count" -eq 0 ]] || die "Unexpected HDL sources in submission package (found ${rtl_file_count})"

gap_md_count="$(find "${SUBMISSION_EXTRACTED}/gap_analysis" -maxdepth 1 -type f -name '*_gaps.md' | wc -l)"
[[ "$gap_md_count" -ge 7 ]] || die "Need >=7 per-DUT gap markdown files, found ${gap_md_count}"

prompt_count="$(find "${SUBMISSION_EXTRACTED}/prompts" -maxdepth 1 -type f -name '*.md' | wc -l)"
[[ "$prompt_count" -ge 5 ]] || die "Need >=5 prompt evidence markdown files, found ${prompt_count}"

grep -Eq 'task_id:[[:space:]]*"2\.1"' "${SUBMISSION_EXTRACTED}/metadata.yaml" || die "metadata.yaml task_id must be 2.1"

for target in compile simulate coverage clean; do
  grep -Eq "^${target}:" "${SUBMISSION_EXTRACTED}/Makefile" || die "Makefile missing target ${target}"
done

ok "Structure checks passed (dut gap files=${gap_md_count}, prompts=${prompt_count})"

section "Task 2.1 - YAML Integrity"
python - <<PY
from pathlib import Path
import yaml

root = Path("${SUBMISSION_EXTRACTED}")

gap = yaml.safe_load((root / "gap_analysis.yaml").read_text(encoding="utf-8"))
pri = yaml.safe_load((root / "priority_table.yaml").read_text(encoding="utf-8"))

assert isinstance(gap, dict) and "gaps" in gap, "gap_analysis.yaml missing top-level gaps"
assert isinstance(pri, dict) and "priorities" in pri, "priority_table.yaml missing top-level priorities"

gaps = gap["gaps"]
priorities = pri["priorities"]
assert len(gaps) >= 20, f"need >=20 major gaps, found {len(gaps)}"
assert len(priorities) >= 10, f"need >=10 priority rows, found {len(priorities)}"

seen = set()
for g in gaps:
    did = g["dut"]
    seen.add(did)

required = {
    "nexus_uart",
    "bastion_gpio",
    "warden_timer",
    "citadel_spi",
    "aegis_aes",
    "sentinel_hmac",
    "rampart_i2c",
}
missing = required - seen
assert not missing, f"missing DUT coverage in gap list: {sorted(missing)}"

print(f"gap_count={len(gaps)} priority_count={len(priorities)} duts={len(seen)}")
PY
ok "YAML parse and content checks passed"

section "Task 2.1 - Report Regeneration Smoke"
if [[ "$QUICK" == "true" ]]; then
  warn "Quick mode enabled: skipping make reports smoke"
else
  pushd "$SUBMISSION_EXTRACTED" >/dev/null
  LOG_FILE="${WORKDIR}/task21_reports.log"
  if timeout "$TIMEOUT" make reports >"$LOG_FILE" 2>&1; then
    ok "make reports passed in extracted ZIP"
  else
    tail -n 120 "$LOG_FILE" | sed 's/^/    /'
    die "make reports failed or timed out"
  fi
  popd >/dev/null
fi

section "Task 2.1 - ZIP Status"
bash "${SCRIPT_DIR}/manage-2.1-submissions.sh" status

section "Done"
ok "Task 2.1 readiness verification completed"
