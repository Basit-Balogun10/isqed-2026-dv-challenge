#!/usr/bin/env bash
#
# verify-readiness.sh
#
# Generic task-driven readiness runner.
#
# Dispatches to per-task scripts following this naming convention:
#   scripts/verify-<task_id>-readiness.sh
# Example:
#   task_id=1.2 -> scripts/verify-1.2-readiness.sh
#
# Usage:
#   bash scripts/verify-readiness.sh
#   bash scripts/verify-readiness.sh --tasks 1.1,1.2,1.3 --sim both
#   bash scripts/verify-readiness.sh 1.1 1.2 1.3 --quick
#
# Options:
#   --tasks LIST                  Comma-separated tasks (e.g. 1.1,1.2)
#   --sim {icarus|verilator|both} Simulator selection (default: both)
#   --quick                       Skip long simulation checks where supported
#   --skip-task-1.2-status        Skip optional task_1_2_status.py report for Task 1.2
#   --timeout SECONDS             Forward timeout to Task 1.2 verifier
#   -k, --keep-workdir            Keep temporary verification workdirs
#   -h, --help                    Show usage

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SIM="both"
QUICK=false
RUN_TASK_1_2_STATUS=true
KEEP_WORKDIR=false
TIMEOUT=""
TASKS=()

usage() {
  sed -n '1,45p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tasks)
      IFS=',' read -r -a parsed_tasks <<< "$2"
      for t in "${parsed_tasks[@]}"; do
        [[ -n "$t" ]] && TASKS+=("$t")
      done
      shift 2
      ;;
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
    --*)
      usage 2
      ;;
    *)
      TASKS+=("$1")
      shift
      ;;
  esac
done

if [[ ${#TASKS[@]} -eq 0 ]]; then
  TASKS=("1.1" "1.2" "1.3")
fi

if [[ "$SIM" != "icarus" && "$SIM" != "verilator" && "$SIM" != "both" ]]; then
  echo "[FAIL] Invalid --sim value '$SIM' (expected: icarus|verilator|both)" >&2
  exit 1
fi

if [[ -n "$TIMEOUT" ]] && ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]]; then
  echo "[FAIL] Invalid --timeout value '$TIMEOUT' (must be integer seconds)" >&2
  exit 1
fi

for task in "${TASKS[@]}"; do
  task_script="${SCRIPT_DIR}/verify-${task}-readiness.sh"
  if [[ ! -f "$task_script" ]]; then
    echo "[FAIL] No verifier script for task '$task': $task_script" >&2
    echo "       Add scripts/verify-${task}-readiness.sh or remove this task from --tasks." >&2
    exit 1
  fi

  task_args=(--sim "$SIM")

  if [[ "$QUICK" == "true" ]]; then
    task_args+=(--quick)
  fi

  if [[ "$KEEP_WORKDIR" == "true" ]]; then
    task_args+=(--keep-workdir)
  fi

  if [[ "$task" == "1.2" ]]; then
    if [[ "$RUN_TASK_1_2_STATUS" != "true" ]]; then
      task_args+=(--skip-task-1.2-status)
    fi
    if [[ -n "$TIMEOUT" ]]; then
      task_args+=(--timeout "$TIMEOUT")
    fi
  fi

  bash "$task_script" "${task_args[@]}"
done
