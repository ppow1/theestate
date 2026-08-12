"""Fail-closed runtime checks for the canonical ChatGPT mailbox worker."""

from __future__ import annotations

import importlib
import os
from pathlib import Path
import socket
import sys
from typing import Any

from estate.core.consultation_store import ConsultationStore


CANONICAL_APP_ROOT = Path(r"A:\AI\OpenWebUI")
CANONICAL_DATA_DIR = CANONICAL_APP_ROOT / "EstateCanonicalData"
CANONICAL_PYTHON = CANONICAL_APP_ROOT / ".venv" / "Scripts" / "python.exe"
CANONICAL_SECRET_FILE = CANONICAL_APP_ROOT / ".webui_secret_key"


def _same_path(left: str | Path, right: str | Path) -> bool:
    return Path(left).resolve(strict=False) == Path(right).resolve(strict=False)


def validate_worker_runtime(*, app_root: str | Path = CANONICAL_APP_ROOT,
                            data_dir: str | Path = CANONICAL_DATA_DIR,
                            python_executable: str | Path = CANONICAL_PYTHON,
                            require_cdp: bool = False,
                            cdp_host: str = "127.0.0.1",
                            cdp_port: int = 9224) -> dict[str, Any]:
    app = Path(app_root)
    data = Path(data_dir)
    expected_python = Path(python_executable)
    checks: dict[str, Any] = {}
    errors: list[str] = []

    checks["python"] = {"expected": str(expected_python), "actual": sys.executable, "ok": _same_path(sys.executable, expected_python)}
    if not checks["python"]["ok"]:
        errors.append("wrong_python_interpreter")
    checks["working_directory"] = {"expected": str(app), "actual": str(Path.cwd()), "ok": _same_path(Path.cwd(), app)}
    if not checks["working_directory"]["ok"]:
        errors.append("wrong_worker_working_directory")
    checks["data_dir"] = {"expected": str(data), "actual": os.getenv("DATA_DIR"), "database_present": (data / "webui.db").is_file(), "ok": _same_path(os.getenv("DATA_DIR", ""), data) and (data / "webui.db").is_file()}
    if not checks["data_dir"]["ok"]:
        errors.append("canonical_data_dir_unavailable")

    secret_file = app / ".webui_secret_key"
    secret_present = secret_file.is_file() and secret_file.stat().st_size > 0
    env_secret_present = bool(os.getenv("WEBUI_SECRET_KEY"))
    secret_source = "environment" if env_secret_present else "canonical_key_file" if secret_present else None
    if not env_secret_present and secret_present:
        # Load the existing governed key into this child process only.  The
        # key file remains the sole persistent source; the value is never
        # returned, logged, or placed on a command line.
        try:
            os.environ["WEBUI_SECRET_KEY"] = secret_file.read_text(encoding="utf-8").strip()
            env_secret_present = bool(os.getenv("WEBUI_SECRET_KEY"))
        except OSError:
            env_secret_present = False
    checks["secret"] = {"variable": "WEBUI_SECRET_KEY", "present": env_secret_present, "source": secret_source, "ok": env_secret_present or secret_present}
    if not checks["secret"]["ok"]:
        errors.append("governed_secret_source_unavailable")

    module_results: dict[str, bool] = {}
    for module_name in ("pydantic_core", "open_webui", "estate.core.consultation_store"):
        try:
            importlib.import_module(module_name)
            module_results[module_name] = True
        except Exception:
            module_results[module_name] = False
            errors.append("required_module_unavailable:" + module_name)
    checks["modules"] = module_results

    try:
        ConsultationStore()
        checks["consultation_store"] = {"ok": True}
    except Exception:
        checks["consultation_store"] = {"ok": False}
        errors.append("consultation_store_unavailable")

    cdp_ok = False
    if require_cdp:
        try:
            with socket.create_connection((cdp_host, cdp_port), timeout=2):
                cdp_ok = True
        except OSError:
            cdp_ok = False
        if not cdp_ok:
            errors.append("chatgpt_cdp_unavailable")
    checks["cdp"] = {"required": require_cdp, "host": cdp_host, "port": cdp_port, "reachable": cdp_ok if require_cdp else None}
    return {"ok": not errors, "errors": errors, "checks": checks}
