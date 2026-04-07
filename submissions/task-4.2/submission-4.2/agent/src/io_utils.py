from __future__ import annotations

import json
import os
import re
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


def read_text(path: Path, max_chars: int = 200_000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text[:max_chars]


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict | list) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_rtl_files(rtl_base: Path) -> list[Path]:
    files = [
        p.resolve()
        for p in rtl_base.rglob("*")
        if p.is_file() and p.suffix.lower() in RTL_EXTENSIONS
    ]
    return sorted(files)


def tokenize(value: str) -> list[str]:
    return [t for t in re.split(r"[^a-zA-Z0-9_]+", value.lower()) if t]


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
