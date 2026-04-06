from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

RTL_EXTENSIONS = {".sv", ".v", ".svh", ".vh"}


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def discover_rtl_files(rtl_path: Path) -> list[Path]:
    if rtl_path.is_file():
        if rtl_path.suffix.lower() not in RTL_EXTENSIONS:
            raise ValueError(f"Unsupported RTL file extension: {rtl_path}")
        return [rtl_path.resolve()]

    if not rtl_path.is_dir():
        raise ValueError(f"RTL path does not exist: {rtl_path}")

    files = [
        p.resolve() for p in rtl_path.rglob("*") if p.suffix.lower() in RTL_EXTENSIONS
    ]
    if not files:
        raise ValueError(f"No RTL files found under: {rtl_path}")
    return sorted(files)


def read_text(path: Path, max_chars: int = 250_000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    if len(text) > max_chars:
        return text[:max_chars]
    return text


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_dotenv_upwards(start_dir: Path) -> None:
    current = start_dir.resolve()
    for candidate in [current, *current.parents]:
        dotenv = candidate / ".env"
        if dotenv.exists():
            load_dotenv(dotenv)
            return


def total_file_size(paths: list[Path]) -> int:
    total = 0
    for p in paths:
        if p.exists() and p.is_file():
            total += p.stat().st_size
    return total
