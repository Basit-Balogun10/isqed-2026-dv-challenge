#!/usr/bin/env bash
#
# verify-1.2-readiness.sh
#
# ZIP-first readiness verification for Task 1.2 submissions.
#
# Flow:
# 1) Package Task 1.2 submission ZIPs
# 2) Extract ZIPs into a temporary workspace
# 3) Validate extracted structure + vplan mapping consistency
# 4) Run reverse simulations from extracted ZIPs on selected simulator(s)
#
# Usage:
#   bash scripts/verify-1.2-readiness.sh
#   bash scripts/verify-1.2-readiness.sh --sim both
#   bash scripts/verify-1.2-readiness.sh --quick

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SIM="both"
QUICK=false
RUN_TASK_1_2_STATUS=true
KEEP_WORKDIR=false
TIMEOUT=300
WORKDIR="/tmp/verify-1.2-$$"
EXTRACT_DIR="${WORKDIR}/extracted"

DUTS=(aegis_aes sentinel_hmac rampart_i2c)

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

ok() {
  echo -e "${GREEN}[OK]${NC} $*"
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $*"
}

info() {
  echo -e "${CYAN}[INFO]${NC} $*"
}

die() {
  echo -e "${RED}[FAIL]${NC} $*"
  exit 1
}

usage() {
  sed -n '1,45p' "$0" | sed 's/^# \{0,1\}//'
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
    --skip-task-1.2-status)
      RUN_TASK_1_2_STATUS=false
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

if [[ "$SIM" != "icarus" && "$SIM" != "verilator" && "$SIM" != "both" ]]; then
  die "Invalid --sim value '$SIM' (expected: icarus|verilator|both)"
fi

if ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]]; then
  die "Invalid --timeout value '$TIMEOUT' (must be integer seconds)"
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

section "Task 1.2 — Package ZIPs"
bash "${SCRIPT_DIR}/manage-1.2-submissions.sh" package-all
ok "Task 1.2 ZIP packages created"

section "Task 1.2 — Verify Extracted ZIP Contents"
export VERIFY_1_2_EXTRACT_DIR="$EXTRACT_DIR"
python3 <<'PY'
from pathlib import Path
import os
import re
import sys
import zipfile
import yaml

zip_root = Path("submissions/zips-1.2")
extract_root = Path(os.environ["VERIFY_1_2_EXTRACT_DIR"])
duts = ["aegis_aes", "sentinel_hmac", "rampart_i2c"]

required_files = [
    "vplan_mapping.yaml",
    "metadata.yaml",
    "methodology.md",
    "Makefile",
]

errors = []
warnings = []

for dut in duts:
    zip_path = zip_root / f"submission-1.2-{dut}.zip"
    if not zip_path.exists():
        errors.append(f"{dut}: missing ZIP {zip_path}")
        continue

    dut_extract = extract_root / dut
    dut_extract.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dut_extract)

    submission = dut_extract / f"submission-1.2-{dut}"
    if not submission.is_dir():
        candidates = [p for p in dut_extract.glob("submission-1.2-*") if p.is_dir()]
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

    tests_dir = submission / "tests"
    if not tests_dir.is_dir():
        errors.append(f"{dut}: tests directory missing")
        continue

    if not (tests_dir / "__init__.py").is_file():
        warnings.append(f"{dut}: tests/__init__.py missing (recommended)")

    testbench_dir = submission / "testbench"
    if testbench_dir.is_dir() and not (testbench_dir / "tl_ul_agent.py").is_file():
        warnings.append(f"{dut}: testbench present but tl_ul_agent.py missing")

    mapping_file = submission / "vplan_mapping.yaml"
    try:
        data = yaml.safe_load(mapping_file.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{dut}: invalid vplan_mapping.yaml ({exc})")
        continue

    if not isinstance(data, dict):
        errors.append(f"{dut}: vplan_mapping.yaml root must be a mapping")
        continue

    mappings = data.get("mappings")
    if not isinstance(mappings, list):
        errors.append(f"{dut}: vplan_mapping.yaml 'mappings' must be a list")
        continue

    if not mappings:
        errors.append(f"{dut}: vplan_mapping.yaml has no mappings")
        continue

    for idx, mapping in enumerate(mappings, start=1):
        if not isinstance(mapping, dict):
            errors.append(f"{dut}: mapping #{idx} is not a dictionary")
            continue

        vp_id = mapping.get("vp_id", "")
        test_name = mapping.get("test_name", "")

        if not vp_id:
            errors.append(f"{dut}: mapping #{idx} missing vp_id")
            continue

        if "::" not in test_name:
            errors.append(f"{dut}:{vp_id}: invalid test_name format (expected module::function)")
            continue

        module_name, func_name = test_name.split("::", 1)
        module_leaf = module_name.split(".")[-1]
        test_file = tests_dir / f"{module_leaf}.py"

        if not test_file.is_file():
            errors.append(f"{dut}:{vp_id}: missing test file {module_leaf}.py")
            continue

        text = test_file.read_text(encoding="utf-8", errors="ignore")
        if not re.search(r"@cocotb\.test\s*\(", text):
            errors.append(f"{dut}:{vp_id}: missing @cocotb.test() decorator")
        if vp_id not in text:
            errors.append(f"{dut}:{vp_id}: VP-ID not found in test docstring/comments")
        if not re.search(rf"async\s+def\s+{re.escape(func_name)}\s*\(", text):
            errors.append(f"{dut}:{vp_id}: async function '{func_name}' missing")

if warnings:
    print("[WARN] Task 1.2 ZIP checks warnings:")
    for item in warnings:
        print(f"  - {item}")

if errors:
    print("[FAIL] Task 1.2 ZIP verification errors:")
    for item in errors:
        print(f"  - {item}")
    sys.exit(1)

print("[OK] Task 1.2 ZIP extraction checks passed")
PY
ok "Task 1.2 extracted ZIP structure and mapping checks passed"

section "Task 1.2 — Checks 3 & 4 (Simulation + Runtime Coverage)"
if [[ "$QUICK" == "true" ]]; then
  warn "Quick mode enabled: skipping simulation and runtime Check-4 coverage validation"
else
  if [[ "$SIM" == "both" ]]; then
    SIMULATORS=(icarus verilator)
  else
    SIMULATORS=("$SIM")
  fi

  TESTS_FAILED=0
  TESTS_PASSED=0
  CHECK4_PASSED=0
  CHECK4_FAILED=0

  for sim in "${SIMULATORS[@]}"; do
    info "Simulator: $sim"
    for dut in "${DUTS[@]}"; do
      TEST_DIR="${EXTRACT_DIR}/${dut}/submission-1.2-${dut}"
      if [[ ! -d "$TEST_DIR" ]]; then
        echo -e "${RED}[FAIL]${NC} ${dut}@${sim} — extracted submission directory missing"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        continue
      fi

      pushd "$TEST_DIR" >/dev/null
      rm -rf sim_build obj_dir
      TEST_LOG="${WORKDIR}/${dut}_${sim}.log"
      COVERAGE_JSON="${WORKDIR}/${dut}_${sim}_runtime_coverage.json"
      rm -f "$COVERAGE_JSON"

      if TASK12_RUNTIME_COVERAGE_FILE="$COVERAGE_JSON" timeout "$TIMEOUT" make SIM="$sim" DUT_PATH="${PROJECT_ROOT}/duts" > "$TEST_LOG" 2>&1; then
        SUMMARY_LINE=$(grep -E "\*\* TESTS=" "$TEST_LOG" | tail -1 || true)
        DUT_TESTS=$(echo "$SUMMARY_LINE" | sed -n 's/.*TESTS=\([0-9]\+\).*/\1/p')
        DUT_PASS=$(echo "$SUMMARY_LINE" | sed -n 's/.*PASS=\([0-9]\+\).*/\1/p')
        DUT_FAIL=$(echo "$SUMMARY_LINE" | sed -n 's/.*FAIL=\([0-9]\+\).*/\1/p')

        if [[ -n "$DUT_TESTS" ]] && [[ -n "$DUT_FAIL" ]] && [[ "$DUT_FAIL" -eq 0 ]] && [[ "$DUT_TESTS" -gt 0 ]]; then
          echo -e "${GREEN}[OK]${NC} ${dut}@${sim} — TESTS=${DUT_TESTS} PASS=${DUT_PASS} FAIL=${DUT_FAIL}"
          TESTS_PASSED=$((TESTS_PASSED + DUT_PASS))

          if python3 "${SCRIPT_DIR}/task_1_2_runtime_check4.py" \
              --mapping "${TEST_DIR}/vplan_mapping.yaml" \
              --runtime-coverage "$COVERAGE_JSON" \
              --dut "$dut" \
              --sim "$sim"; then
            CHECK4_PASSED=$((CHECK4_PASSED + 1))
          else
            CHECK4_FAILED=$((CHECK4_FAILED + 1))
            TESTS_FAILED=$((TESTS_FAILED + 1))
          fi
        else
          echo -e "${RED}[FAIL]${NC} ${dut}@${sim} — Missing/invalid cocotb summary or non-zero FAIL"
          tail -20 "$TEST_LOG" | sed 's/^/    /'
          TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
      else
        echo -e "${RED}[FAIL]${NC} ${dut}@${sim} — timeout (${TIMEOUT}s) or build/test error"
        tail -20 "$TEST_LOG" | sed 's/^/    /'
        TESTS_FAILED=$((TESTS_FAILED + 1))
      fi
      popd >/dev/null
    done
  done

  if [[ "$TESTS_FAILED" -ne 0 ]]; then
    die "Task 1.2 checks failed (${TESTS_FAILED} failing job(s), Check-4 failures=${CHECK4_FAILED})"
  fi

  ok "Task 1.2 checks passed (${TESTS_PASSED} test(s) passed, Check-4 jobs=${CHECK4_PASSED})"
fi

if [[ "$RUN_TASK_1_2_STATUS" == "true" ]]; then
  section "Task 1.2 — Optional Detailed Diagnostic"
  STATUS_SCRIPT="${SCRIPT_DIR}/task_1_2_status.py"
  if [[ -f "$STATUS_SCRIPT" ]]; then
    python3 "$STATUS_SCRIPT"
    ok "task_1_2_status.py reported no critical issues"
  else
    warn "Optional diagnostic skipped: ${STATUS_SCRIPT} not found"
  fi
fi

section "Task 1.2 — ZIP Status"
bash "${SCRIPT_DIR}/manage-1.2-submissions.sh" status

section "Done"
ok "Task 1.2 readiness verification completed"
