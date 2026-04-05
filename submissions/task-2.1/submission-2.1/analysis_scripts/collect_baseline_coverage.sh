#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUBMISSION_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUNNER_DIR="${SUBMISSION_DIR}/baseline_runner"
OUT_DIR="${SUBMISSION_DIR}/baseline_artifacts"

DUTS=(nexus_uart bastion_gpio warden_timer citadel_spi aegis_aes sentinel_hmac rampart_i2c)
EXTRA_ARGS="--coverage --coverage-line --coverage-toggle"

if [[ -f "${SUBMISSION_DIR}/../../../.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${SUBMISSION_DIR}/../../../.venv/bin/activate"
fi

VERILATOR_COVERAGE_BIN="$(command -v verilator_coverage || true)"
if [[ -z "${VERILATOR_COVERAGE_BIN}" && -x "/home/abdulbasit/open-source/verilator/bin/verilator_coverage" ]]; then
  VERILATOR_COVERAGE_BIN="/home/abdulbasit/open-source/verilator/bin/verilator_coverage"
fi

if [[ -z "${VERILATOR_COVERAGE_BIN}" ]]; then
  echo "[FAIL] verilator_coverage not found in PATH"
  exit 1
fi

mkdir -p "${OUT_DIR}"

for dut in "${DUTS[@]}"; do
  dut_out="${OUT_DIR}/${dut}"
  mkdir -p "${dut_out}/annotated"

  echo "[INFO] Running baseline coverage for ${dut}"
  pushd "${RUNNER_DIR}" >/dev/null

  rm -rf sim_build obj_dir results.xml coverage.dat

  if make clean >/dev/null 2>&1 && \
     make run SIM=verilator DUT="${dut}" EXTRA_ARGS="${EXTRA_ARGS}" >"${dut_out}/run.log" 2>&1; then
    echo "[OK] ${dut} baseline run passed"
  else
    echo "[WARN] ${dut} baseline run failed (see ${dut_out}/run.log)"
    popd >/dev/null
    continue
  fi

  cov_file=""
  if [[ -f "coverage.dat" ]]; then
    cov_file="coverage.dat"
  elif [[ -f "sim_build/coverage.dat" ]]; then
    cov_file="sim_build/coverage.dat"
  else
    cov_file="$(find . -maxdepth 3 -type f -name 'coverage.dat' | head -n1 || true)"
  fi

  if [[ -z "${cov_file}" || ! -f "${cov_file}" ]]; then
    echo "[WARN] ${dut} coverage.dat not found"
    popd >/dev/null
    continue
  fi

  cp "${cov_file}" "${dut_out}/coverage.dat"
  cp results.xml "${dut_out}/results.xml" 2>/dev/null || true

  "${VERILATOR_COVERAGE_BIN}" --write-info "${dut_out}/coverage.info" "${dut_out}/coverage.dat" >/dev/null 2>&1 || true
  "${VERILATOR_COVERAGE_BIN}" --annotate "${dut_out}/annotated" "${dut_out}/coverage.dat" >/dev/null 2>&1 || true

  popd >/dev/null
done

echo "[INFO] Baseline collection complete: ${OUT_DIR}"
