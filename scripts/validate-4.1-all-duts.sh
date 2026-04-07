#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUB_DIR="${ROOT_DIR}/submissions/task-4.1/submission-4.1"
SAMPLES_ROOT="${ROOT_DIR}/submissions/task-4.1/local_samples"

PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python3"
fi

SIMULATOR="both"
RETENTION_MODE="full" # full | compact
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="${SAMPLES_ROOT}/${TIMESTAMP}"

DUTS=(
  "nexus_uart"
  "bastion_gpio"
  "citadel_spi"
  "rampart_i2c"
  "sentinel_hmac"
  "aegis_aes"
  "warden_timer"
)

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --simulator <auto|both|icarus|verilator>   Simulator mode passed to run_agent.py (default: both)
  --retention <full|compact>                 Artifact retention mode (default: full)
  --duts <comma-separated list>              DUT subset to run (default: all 7)
  --tag <string>                             Optional run tag appended to timestamp folder
  -h, --help                                 Show this help message

Examples:
  $(basename "$0")
  $(basename "$0") --simulator both --retention full
  $(basename "$0") --duts nexus_uart,bastion_gpio --retention compact
EOF
}

parse_args() {
  local run_tag=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --simulator)
        SIMULATOR="$2"
        shift 2
        ;;
      --retention)
        RETENTION_MODE="$2"
        shift 2
        ;;
      --duts)
        IFS=',' read -r -a DUTS <<< "$2"
        shift 2
        ;;
      --tag)
        run_tag="$2"
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "[FAIL] Unknown argument: $1" >&2
        usage
        exit 1
        ;;
    esac
  done

  case "${SIMULATOR}" in
    auto|both|icarus|verilator) ;;
    *)
      echo "[FAIL] Invalid simulator mode: ${SIMULATOR}" >&2
      exit 1
      ;;
  esac

  case "${RETENTION_MODE}" in
    full|compact) ;;
    *)
      echo "[FAIL] Invalid retention mode: ${RETENTION_MODE}" >&2
      exit 1
      ;;
  esac

  if [[ -n "${run_tag}" ]]; then
    RUN_DIR="${SAMPLES_ROOT}/${TIMESTAMP}_${run_tag}"
  fi
}

prune_output_dir() {
  local out="$1"
  local mode="$2"

  # Remove heavyweight compile artifacts in all modes.
  rm -rf "${out}/sim_build" || true
  find "${out}" -type d -name "__pycache__" -prune -exec rm -rf {} + || true

  if [[ "${mode}" == "compact" ]]; then
    # Keep only lightweight reviewer-friendly outputs.
    local keep_tmp
    keep_tmp="$(mktemp -d)"

    for rel in \
      "report.md" \
      "agent_log.json" \
      "test_results.json" \
      "iteration_log.json" \
      "analysis.json" \
      "build_manifest.json" \
      "verification_plan.json" \
      "verification_plan.md" \
      "coverage/coverage_summary.json" \
      "coverage/code_coverage/summary.txt" \
      "coverage/func_coverage/summary.txt" \
      "coverage/func_coverage/bin_counts.json"
    do
      if [[ -e "${out}/${rel}" ]]; then
        mkdir -p "${keep_tmp}/$(dirname "${rel}")"
        cp -a "${out}/${rel}" "${keep_tmp}/${rel}"
      fi
    done

    if [[ -d "${out}/bug_reports" ]]; then
      mkdir -p "${keep_tmp}"
      cp -a "${out}/bug_reports" "${keep_tmp}/bug_reports"
    fi

    rm -rf "${out}"
    mkdir -p "${out}"
    cp -a "${keep_tmp}/." "${out}/"
    rm -rf "${keep_tmp}"
  fi
}

summarize_run() {
  local dut="$1"
  local sample_dir="$2"
  local exit_code="$3"
  local duration="$4"

  "${PYTHON_BIN}" - <<PY
import json
from pathlib import Path

sample_dir = Path(r"${sample_dir}")
out = sample_dir / "output"
summary = {
    "dut": "${dut}",
    "exit_code": int(${exit_code}),
    "duration_seconds": int(${duration}),
    "status": "pass" if int(${exit_code}) == 0 else "fail",
    "simulator_mode": "${SIMULATOR}",
    "retention_mode": "${RETENTION_MODE}",
}

tr = out / "test_results.json"
if tr.exists():
    try:
        data = json.loads(tr.read_text())
        summary["simulation_passed"] = bool(data.get("simulation_passed", False))
        summary["simulators_tested"] = data.get("simulators_tested", [])
        summary["simulators_requested"] = data.get("simulators_requested", [])
        summary["dual_simulator_compliant"] = bool(data.get("dual_simulator_compliant", False))
        summary["directed_test_count"] = int(data.get("directed_test_count", 0))
        summary["random_test_count"] = int(data.get("random_test_count", 0))
    except Exception as exc:
        summary["test_results_parse_error"] = str(exc)

cov = out / "coverage" / "coverage_summary.json"
if cov.exists():
    try:
        c = json.loads(cov.read_text())
        cc = c.get("code_coverage", {})
        fc = c.get("functional_coverage", {})
        summary["line_percent"] = float(cc.get("line_percent", 0.0))
        summary["branch_percent"] = float(cc.get("branch_percent", 0.0))
        summary["toggle_percent"] = float(cc.get("toggle_percent", 0.0))
        summary["fsm_percent"] = float(cc.get("fsm_percent", 0.0))
        summary["functional_percent"] = float(fc.get("percent", 0.0))
        summary["toggle_source"] = str(cc.get("toggle_source", ""))
        summary["fsm_source"] = str(cc.get("fsm_source", ""))
    except Exception as exc:
        summary["coverage_parse_error"] = str(exc)

sample_dir.mkdir(parents=True, exist_ok=True)
(sample_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
PY
}

generate_matrix_report() {
  local report_md="${RUN_DIR}/matrix_report.md"
  local report_csv="${RUN_DIR}/matrix_report.csv"

  "${PYTHON_BIN}" - <<PY
import csv
import json
from pathlib import Path

run_dir = Path(r"${RUN_DIR}")
rows = []
for dut_dir in sorted([p for p in run_dir.iterdir() if p.is_dir()]):
    summary_file = dut_dir / "run_summary.json"
    if not summary_file.exists():
        continue
    data = json.loads(summary_file.read_text())
    rows.append(data)

csv_fields = [
    "dut",
    "status",
    "exit_code",
    "duration_seconds",
    "simulator_mode",
    "simulation_passed",
    "dual_simulator_compliant",
    "line_percent",
    "branch_percent",
    "toggle_percent",
    "fsm_percent",
    "functional_percent",
    "simulators_tested",
    "toggle_source",
    "fsm_source",
]

with (run_dir / "matrix_report.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=csv_fields)
    writer.writeheader()
    for row in rows:
        out = {k: row.get(k, "") for k in csv_fields}
        if isinstance(out.get("simulators_tested"), list):
            out["simulators_tested"] = ";".join(out["simulators_tested"])
        writer.writerow(out)

lines = [
    "# Task 4.1 All-DUT Validation Matrix",
    "",
    f"Run directory: {run_dir}",
    "",
    "| DUT | Status | Exit | Time(s) | Sim-Pass | Dual-Sim | Line | Branch | Toggle | FSM | Functional | Sims Tested |",
    "|---|---|---:|---:|---|---|---:|---:|---:|---:|---:|---|",
]

for row in rows:
    sims = row.get("simulators_tested", [])
    if isinstance(sims, list):
        sims_txt = ",".join(sims)
    else:
        sims_txt = str(sims)
    lines.append(
        "| {dut} | {status} | {exit_code} | {duration_seconds} | {simulation_passed} | {dual} | {line:.2f} | {branch:.2f} | {toggle:.2f} | {fsm:.2f} | {func:.2f} | {sims} |".format(
            dut=row.get("dut", ""),
            status=row.get("status", ""),
            exit_code=int(row.get("exit_code", 0)),
            duration_seconds=int(row.get("duration_seconds", 0)),
            simulation_passed=bool(row.get("simulation_passed", False)),
            dual=bool(row.get("dual_simulator_compliant", False)),
            line=float(row.get("line_percent", 0.0)),
            branch=float(row.get("branch_percent", 0.0)),
            toggle=float(row.get("toggle_percent", 0.0)),
            fsm=float(row.get("fsm_percent", 0.0)),
            func=float(row.get("functional_percent", 0.0)),
            sims=sims_txt,
        )
    )

(run_dir / "matrix_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

  echo "[PASS] Wrote ${report_md}"
  echo "[PASS] Wrote ${report_csv}"
}

run_one_dut() {
  local dut="$1"
  local sample_dir="${RUN_DIR}/${dut}"
  local output_dir="${SUB_DIR}/output_${dut}"
  local log_file="${sample_dir}/run.log"

  mkdir -p "${sample_dir}"

  local rtl_path="${ROOT_DIR}/duts/${dut}"
  local spec_path="${ROOT_DIR}/specs/${dut}_spec.md"
  local csr_path="${ROOT_DIR}/csr_maps/${dut}_csr.hjson"

  if [[ ! -e "${rtl_path}" || ! -e "${spec_path}" || ! -e "${csr_path}" ]]; then
    echo "[FAIL] Missing DUT inputs for ${dut}" | tee "${sample_dir}/run.log"
    summarize_run "${dut}" "${sample_dir}" 1 0
    return 0
  fi

  echo "[INFO] Running ${dut} (simulator=${SIMULATOR}, retention=${RETENTION_MODE})"

  local start_epoch
  start_epoch="$(date +%s)"
  local exit_code=0

  (
    cd "${SUB_DIR}"
    rm -rf "${output_dir}"
    "${PYTHON_BIN}" agent/run_agent.py \
      --rtl "${rtl_path}" \
      --spec "${spec_path}" \
      --csr_map "${csr_path}" \
      --output_dir "${output_dir}" \
      --simulator "${SIMULATOR}"
  ) >"${log_file}" 2>&1 || exit_code=$?

  local end_epoch
  end_epoch="$(date +%s)"
  local duration=$((end_epoch - start_epoch))

  if [[ -d "${output_dir}" ]]; then
    rm -rf "${sample_dir}/output"
    cp -a "${output_dir}" "${sample_dir}/output"
    prune_output_dir "${sample_dir}/output" "${RETENTION_MODE}"
  fi

  summarize_run "${dut}" "${sample_dir}" "${exit_code}" "${duration}"

  # Keep working dir clean while preserving copied samples.
  rm -rf "${output_dir}" || true

  if [[ "${exit_code}" -eq 0 ]]; then
    echo "[PASS] ${dut} completed in ${duration}s"
  else
    echo "[WARN] ${dut} exited with code ${exit_code} in ${duration}s"
  fi
}

main() {
  parse_args "$@"

  mkdir -p "${RUN_DIR}"

  cat > "${RUN_DIR}/run_config.json" <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "simulator": "${SIMULATOR}",
  "retention_mode": "${RETENTION_MODE}",
  "duts": ["$(IFS='","'; echo "${DUTS[*]}")"]
}
EOF

  for dut in "${DUTS[@]}"; do
    run_one_dut "${dut}"
  done

  generate_matrix_report
  echo "[PASS] All requested DUT runs completed. Samples at: ${RUN_DIR}"
}

main "$@"
