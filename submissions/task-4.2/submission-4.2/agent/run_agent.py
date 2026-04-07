#!/usr/bin/env python3
"""Task 4.2 Regression Agent entry point."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml  # type: ignore[import-untyped]

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from io_utils import load_dotenv_upwards
from regression_orchestrator import RegressionAgentOrchestrator  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Task 4.2 Regression Agent")
    parser.add_argument(
        "--commit_stream",
        required=False,
        help="Path to commit stream JSON payload",
    )
    parser.add_argument(
        "--rtl_base",
        "--baseline_rtl",
        dest="rtl_base",
        required=True,
        help="Path to baseline RTL directory",
    )
    parser.add_argument(
        "--test_suite",
        "--baseline_env",
        dest="test_suite",
        required=True,
        help="Path to baseline test suite directory",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Directory to write verdict outputs",
    )
    parser.add_argument(
        "--config",
        default=str(SCRIPT_DIR / "agent_config.yaml"),
        help="Path to agent config YAML",
    )
    parser.add_argument(
        "--listen",
        choices=["file", "stdin", "http"],
        default="file",
        help="Input mode: file (default), stdin, or http",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="HTTP port when --listen http is selected",
    )
    return parser.parse_args()


def load_config(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as file_handle:
        loaded = yaml.safe_load(file_handle) or {}
    if not isinstance(loaded, dict):
        raise RuntimeError("agent config must be a YAML mapping")
    return loaded


def _validate_inputs(args: argparse.Namespace) -> None:
    rtl_base = Path(args.rtl_base)
    test_suite = Path(args.test_suite)

    if args.listen == "file":
        if not args.commit_stream:
            raise RuntimeError("--commit_stream is required when --listen file")
        commit_stream = Path(args.commit_stream)
        if not commit_stream.exists() or not commit_stream.is_file():
            raise FileNotFoundError(f"Commit stream not found: {commit_stream}")

    if not rtl_base.exists() or not rtl_base.is_dir():
        raise FileNotFoundError(f"RTL base directory not found: {rtl_base}")

    if not test_suite.exists() or not test_suite.is_dir():
        raise FileNotFoundError(f"Test suite directory not found: {test_suite}")

    if args.listen == "http" and args.port <= 0:
        raise RuntimeError("--port must be a positive integer in HTTP mode")


def _parse_commit_payload(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        commits = payload.get("commits")
        if isinstance(commits, list):
            return [item for item in commits if isinstance(item, dict)]
        return [payload]

    raise RuntimeError("Input payload must be a JSON object or list")


def _run_file_mode(args: argparse.Namespace, orchestrator: RegressionAgentOrchestrator) -> int:
    orchestrator.run(
        commit_stream_path=Path(args.commit_stream).resolve(),
        rtl_base=Path(args.rtl_base).resolve(),
        test_suite=Path(args.test_suite).resolve(),
        output_dir=Path(args.output_dir).resolve(),
    )
    return 0


def _run_stdin_mode(args: argparse.Namespace, orchestrator: RegressionAgentOrchestrator) -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        raise RuntimeError("stdin mode requires JSON input from stdin")

    payload = json.loads(raw)
    commits = _parse_commit_payload(payload)

    orchestrator.initialize_runtime(
        rtl_base=Path(args.rtl_base).resolve(),
        test_suite=Path(args.test_suite).resolve(),
        output_dir=Path(args.output_dir).resolve(),
    )
    orchestrator.logger.set_commit_count(len(commits))

    verdicts = []
    for commit in commits:
        verdicts.append(orchestrator.process_commit(commit))

    orchestrator.finalize_runtime()

    if len(verdicts) == 1:
        print(json.dumps(verdicts[0], indent=2), flush=True)
    else:
        for verdict in verdicts:
            print(json.dumps(verdict), flush=True)

    return 0


def _run_http_mode(args: argparse.Namespace, orchestrator: RegressionAgentOrchestrator) -> int:
    orchestrator.initialize_runtime(
        rtl_base=Path(args.rtl_base).resolve(),
        test_suite=Path(args.test_suite).resolve(),
        output_dir=Path(args.output_dir).resolve(),
    )

    class CommitHandler(BaseHTTPRequestHandler):
        def _write_json(self, status: int, payload: dict | list) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                self._write_json(
                    200,
                    {
                        "status": "ok",
                        "commits_processed": orchestrator.logger.metadata.get(
                            "total_commits", 0
                        ),
                    },
                )
                return
            self._write_json(404, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
                payload = json.loads(raw)

                if self.path == "/commit":
                    commit_payload = payload.get("commit") if isinstance(payload, dict) else None
                    commit = commit_payload if isinstance(commit_payload, dict) else payload
                    if not isinstance(commit, dict):
                        self._write_json(400, {"error": "commit payload must be JSON object"})
                        return
                    verdict = orchestrator.process_commit(commit)
                    self._write_json(200, verdict)
                    return

                if self.path == "/stream":
                    commits = _parse_commit_payload(payload)
                    orchestrator.logger.set_commit_count(len(commits))
                    verdicts = [orchestrator.process_commit(item) for item in commits]
                    self._write_json(200, {"verdicts": verdicts})
                    return

                self._write_json(404, {"error": "not found"})
            except Exception as exc:
                self._write_json(500, {"error": str(exc)})

    server = ThreadingHTTPServer(("0.0.0.0", args.port), CommitHandler)
    print(f"HTTP listen mode active on port {args.port}", flush=True)
    print("POST /commit for single commit, POST /stream for a list, GET /health for status", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        orchestrator.finalize_runtime()

    return 0


def main() -> int:
    args = parse_args()

    # Support local execution with a root-level .env while keeping secrets out of repo.
    load_dotenv_upwards(start_dir=Path.cwd())

    _validate_inputs(args)
    config = load_config(args.config)

    orchestrator = RegressionAgentOrchestrator(config=config)

    if args.listen == "stdin":
        return _run_stdin_mode(args, orchestrator)

    if args.listen == "http":
        return _run_http_mode(args, orchestrator)

    return _run_file_mode(args, orchestrator)


if __name__ == "__main__":
    raise SystemExit(main())
