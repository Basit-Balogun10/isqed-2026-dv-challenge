#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
run-4.2-monitored.sh

Runs Task 4.2 agent in file listen mode and prints live progress so runs never look stuck.

Usage:
  bash scripts/run-4.2-monitored.sh [options]

Options:
  --commit-stream PATH   Commit stream JSON (default: submissions/task-4.2/sample_commit_stream.json)
  --rtl-base PATH        Baseline RTL dir (default: duts/nexus_uart)
  --test-suite PATH      Baseline test suite dir (default: skeleton_envs/nexus_uart)
  --output-dir PATH      Output directory (default: submissions/task-4.2/submission-4.2/output_monitored_eval)
  --config PATH          Agent config path (default: submissions/task-4.2/submission-4.2/agent/agent_config.yaml)
  --poll-seconds N       Poll interval in seconds (default: 5)
  --keep-output          Do not clean output dir before run
  --no-run               Monitor-only mode for an already running output dir
  -h, --help             Show this help
EOF
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
[[ -x "${PYTHON_BIN}" ]] || PYTHON_BIN="python3"

COMMIT_STREAM="${ROOT_DIR}/submissions/task-4.2/sample_commit_stream.json"
RTL_BASE="${ROOT_DIR}/duts/nexus_uart"
TEST_SUITE="${ROOT_DIR}/skeleton_envs/nexus_uart"
OUTPUT_DIR="${ROOT_DIR}/submissions/task-4.2/submission-4.2/output_monitored_eval"
CONFIG_PATH="${ROOT_DIR}/submissions/task-4.2/submission-4.2/agent/agent_config.yaml"
POLL_SECONDS=5
KEEP_OUTPUT=false
NO_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --commit-stream)
      COMMIT_STREAM="$2"
      shift 2
      ;;
    --rtl-base)
      RTL_BASE="$2"
      shift 2
      ;;
    --test-suite)
      TEST_SUITE="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --config)
      CONFIG_PATH="$2"
      shift 2
      ;;
    --poll-seconds)
      POLL_SECONDS="$2"
      shift 2
      ;;
    --keep-output)
      KEEP_OUTPUT=true
      shift
      ;;
    --no-run)
      NO_RUN=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! [[ "${POLL_SECONDS}" =~ ^[0-9]+$ ]] || [[ "${POLL_SECONDS}" -le 0 ]]; then
  echo "--poll-seconds must be a positive integer" >&2
  exit 2
fi

if [[ "${NO_RUN}" == false ]]; then
  [[ -f "${COMMIT_STREAM}" ]] || { echo "Missing commit stream: ${COMMIT_STREAM}" >&2; exit 1; }
  [[ -d "${RTL_BASE}" ]] || { echo "Missing rtl base: ${RTL_BASE}" >&2; exit 1; }
  [[ -d "${TEST_SUITE}" ]] || { echo "Missing test suite: ${TEST_SUITE}" >&2; exit 1; }
  [[ -f "${CONFIG_PATH}" ]] || { echo "Missing config: ${CONFIG_PATH}" >&2; exit 1; }
fi

RUN_LOG="${OUTPUT_DIR}/run.log"
mkdir -p "${OUTPUT_DIR}"

if [[ "${NO_RUN}" == false && "${KEEP_OUTPUT}" == false ]]; then
  rm -rf "${OUTPUT_DIR}"
  mkdir -p "${OUTPUT_DIR}"
fi

AGENT_PID=""
if [[ "${NO_RUN}" == false ]]; then
  (
    cd "${ROOT_DIR}"
    "${PYTHON_BIN}" submissions/task-4.2/submission-4.2/agent/run_agent.py \
      --listen file \
      --commit_stream "${COMMIT_STREAM}" \
      --rtl_base "${RTL_BASE}" \
      --test_suite "${TEST_SUITE}" \
      --output_dir "${OUTPUT_DIR}" \
      --config "${CONFIG_PATH}"
  ) >"${RUN_LOG}" 2>&1 &
  AGENT_PID="$!"
  echo "[START] pid=${AGENT_PID} output_dir=${OUTPUT_DIR}"
else
  echo "[INFO] Monitor-only mode: not launching a new run"
fi

last_print=""
while true; do
  verdict_count=0
  if [[ -d "${OUTPUT_DIR}/verdicts" ]]; then
    verdict_count="$(find "${OUTPUT_DIR}/verdicts" -maxdepth 1 -type f -name 'commit_*.json' | wc -l | tr -d ' ')"
  fi

  status="unknown"
  processed="${verdict_count}"
  expected="?"
  llm_calls="?"
  tokens="?"
  cost="?"
  elapsed="?"

  if [[ -f "${OUTPUT_DIR}/run_progress.json" ]]; then
    parsed="$(${PYTHON_BIN} - <<PY
import json
from pathlib import Path
p = Path(${OUTPUT_DIR@Q}) / "run_progress.json"
obj = json.loads(p.read_text())
print("\t".join([
    str(obj.get("status", "unknown")),
    str(obj.get("commits_processed", "?")),
    str(obj.get("commits_expected", "?")),
    str(obj.get("llm_calls", "?")),
    str(obj.get("total_tokens", "?")),
    str(obj.get("estimated_cost_usd", "?")),
    str(obj.get("elapsed_seconds", "?")),
]))
PY
)"
    IFS=$'\t' read -r status processed expected llm_calls tokens cost elapsed <<<"${parsed}"
  fi

  if [[ "${status}" == "unknown" && -f "${OUTPUT_DIR}/stream_summary.json" ]]; then
    status="completed"
    parsed_summary="$(${PYTHON_BIN} - <<PY
import json
from pathlib import Path
s = json.loads((Path(${OUTPUT_DIR@Q}) / "stream_summary.json").read_text())
m = {}
meta_path = Path(${OUTPUT_DIR@Q}) / "agent_log.json"
if meta_path.exists():
    m = json.loads(meta_path.read_text()).get("metadata", {})
print("\t".join([
    str(s.get("commits_processed", "?")),
    str(m.get("total_commits", s.get("commits_processed", "?"))),
    str(s.get("total_llm_calls", m.get("total_llm_calls", "?"))),
    str(m.get("total_tokens_used", "?")),
    str(m.get("estimated_cost_usd", "?")),
    str(s.get("elapsed_seconds", "?")),
]))
PY
)"
    IFS=$'\t' read -r processed expected llm_calls tokens cost elapsed <<<"${parsed_summary}"
  fi

  stable_line="status=${status} commits=${processed}/${expected} files=${verdict_count} llm_calls=${llm_calls} tokens=${tokens} cost_usd=${cost} elapsed_s=${elapsed}"
  if [[ "${stable_line}" != "${last_print}" ]]; then
    echo "[PROGRESS] $(date '+%H:%M:%S') ${stable_line}"
    last_print="${stable_line}"
  fi

  if [[ "${NO_RUN}" == false ]]; then
    if ! kill -0 "${AGENT_PID}" >/dev/null 2>&1; then
      break
    fi
  else
    if [[ -f "${OUTPUT_DIR}/stream_summary.json" ]]; then
      break
    fi
  fi

  sleep "${POLL_SECONDS}"
done

if [[ "${NO_RUN}" == false ]]; then
  set +e
  wait "${AGENT_PID}"
  EXIT_CODE="$?"
  set -e
  echo "[DONE] agent exit code=${EXIT_CODE}"
  if [[ "${EXIT_CODE}" -ne 0 ]]; then
    echo "[ERROR] Agent failed. Tail of run log:"
    tail -n 60 "${RUN_LOG}" || true
    exit "${EXIT_CODE}"
  fi
fi

if [[ -f "${OUTPUT_DIR}/stream_summary.json" ]]; then
  echo "[SUMMARY]"
  "${PYTHON_BIN}" - <<PY
import json
from pathlib import Path
summary = json.loads((Path(${OUTPUT_DIR@Q}) / "stream_summary.json").read_text())
print(json.dumps(summary, indent=2))
PY
else
  echo "[WARN] stream_summary.json not found in ${OUTPUT_DIR}"
fi

if [[ -f "${OUTPUT_DIR}/agent_log.json" ]]; then
  echo "[COST]"
  "${PYTHON_BIN}" - <<PY
import json
from pathlib import Path
meta = json.loads((Path(${OUTPUT_DIR@Q}) / "agent_log.json").read_text()).get("metadata", {})
print(json.dumps({
  "total_llm_calls": meta.get("total_llm_calls"),
  "total_tokens_used": meta.get("total_tokens_used"),
  "estimated_cost_usd": meta.get("estimated_cost_usd"),
  "verdict_counts": meta.get("verdict_counts"),
}, indent=2))
PY
fi

echo "[INFO] run log: ${RUN_LOG}"
