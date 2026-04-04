#!/usr/bin/env bash
#
# verify-1.1-readiness.sh
#
# ZIP-first readiness verification for Task 1.1 submissions.
#
# Flow:
# 1) Rebuild Task 1.1 ZIPs from source submissions
# 2) Extract ZIPs into a temporary workspace
# 3) Verify required files and sanity-check extracted testbench wiring
# 4) Reverse-test extracted ZIPs on selected simulator(s)
#
# Usage:
#   bash scripts/verify-1.1-readiness.sh
#   bash scripts/verify-1.1-readiness.sh --sim both
#   bash scripts/verify-1.1-readiness.sh --quick

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SIM="both"
QUICK=false
KEEP_WORKDIR=false
WORKDIR="/tmp/verify-1.1-$$"
EXTRACT_DIR="${WORKDIR}/extracted"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

section() {
  echo
  echo -e "${BLUE}======================================================================${NC}"
  echo -e "${BLUE}$*${NC}"
  echo -e "${BLUE}======================================================================${NC}"
}

ok() {
  echo -e "${GREEN}[OK]${NC} $*"
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $*"
}

die() {
  echo -e "${RED}[FAIL]${NC} $*"
  exit 1
}

usage() {
  sed -n '1,40p' "$0" | sed 's/^# \{0,1\}//'
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

if [[ "$SIM" != "icarus" && "$SIM" != "verilator" && "$SIM" != "both" ]]; then
  die "Invalid --sim value '$SIM' (expected: icarus|verilator|both)"
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
  warn "No .venv found; relying on system Python"
fi

section "Task 1.1 — Rebuild ZIP Packages"
bash "${SCRIPT_DIR}/manage-1.1-submissions.sh" rebuild-all
ok "Task 1.1 ZIP packages rebuilt"

section "Task 1.1 — Verify Extracted ZIP Contents"
export VERIFY_1_1_EXTRACT_DIR="$EXTRACT_DIR"
python3 <<'PY'
from pathlib import Path
import os
import re
import sys
import zipfile

zip_root = Path("submissions/zips-1.1")
extract_root = Path(os.environ["VERIFY_1_1_EXTRACT_DIR"])
duts = ["aegis_aes", "rampart_i2c", "sentinel_hmac"]

required_files = [
    "Makefile",
    "metadata.yaml",
    "methodology.md",
    "testbench/__init__.py",
    "testbench/tl_ul_agent.py",
    "testbench/scoreboard.py",
    "testbench/coverage.py",
    "testbench/env.py",
    "tests/__init__.py",
    "tests/test_basic.py",
]

errors = []
warnings = []

for dut in duts:
    zip_path = zip_root / f"submission-1.1-{dut}.zip"
    if not zip_path.exists():
        errors.append(f"{dut}: missing ZIP {zip_path}")
        continue

    dut_extract = extract_root / dut
    dut_extract.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dut_extract)

    submission = dut_extract / f"submission-1.1-{dut}"
    if not submission.is_dir():
        candidates = [p for p in dut_extract.glob("submission-1.1-*") if p.is_dir()]
        if len(candidates) == 1:
            submission = candidates[0]
        else:
            errors.append(f"{dut}: could not locate extracted submission root")
            continue

    for rel in required_files:
        if not (submission / rel).is_file():
            errors.append(f"{dut}: missing required file in ZIP extraction -> {rel}")

    prompts_dir = submission / "prompts"
    if not prompts_dir.is_dir():
      errors.append(f"{dut}: missing prompts/ directory in ZIP extraction")
    else:
      prompts_md_count = len(list(prompts_dir.glob("*.md")))
      if prompts_md_count < 3:
        errors.append(
          f"{dut}: prompts/ must contain at least 3 markdown files (found {prompts_md_count})"
        )

    scoreboard = submission / "testbench" / "scoreboard.py"
    env = submission / "testbench" / "env.py"
    coverage = submission / "testbench" / "coverage.py"

    if scoreboard.is_file():
        sb_text = scoreboard.read_text(encoding="utf-8", errors="ignore")
        if not re.search(r"^\s*class\s+\w+", sb_text, re.MULTILINE):
            errors.append(f"{dut}: scoreboard.py has no class definition")
        lower_sb = sb_text.lower()
        if not any(tok in lower_sb for tok in ["predict", "expected", "reference model"]):
            warnings.append(
                f"{dut}: scoreboard.py has no obvious predict/expected/reference keyword"
            )

    if env.is_file():
      env_text = env.read_text(encoding="utf-8", errors="ignore").lower()
      if "scoreboard" not in env_text:
        errors.append(f"{dut}: env.py does not appear to reference scoreboard")
      if "coverage" not in env_text:
        errors.append(f"{dut}: env.py does not appear to reference coverage")

    if not coverage.is_file():
      errors.append(f"{dut}: missing testbench/coverage.py")

if warnings:
    print("[WARN] Task 1.1 sanity warnings:")
    for item in warnings:
        print(f"  - {item}")

if errors:
    print("[FAIL] Task 1.1 ZIP verification errors:")
    for item in errors:
        print(f"  - {item}")
    sys.exit(1)

print("[OK] Task 1.1 ZIP extraction checks passed")
PY
ok "Task 1.1 extracted ZIP structure and sanity checks passed"

section "Task 1.1 — ZIP Reverse Testing"
if [[ "$QUICK" == "true" ]]; then
  warn "Quick mode enabled: skipping reverse simulation tests"
else
  bash "${SCRIPT_DIR}/test-1.1-submissions.sh" -s "$SIM"
  ok "Task 1.1 reverse tests passed"
fi

section "Task 1.1 — ZIP Status"
bash "${SCRIPT_DIR}/manage-1.1-submissions.sh" status

section "Done"
ok "Task 1.1 readiness verification completed"
