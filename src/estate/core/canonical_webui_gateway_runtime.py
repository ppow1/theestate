"""Canonical, semantic, fail-closed WebUI/Gateway runtime controller.

The controller owns the two application processes, while Open WebUI state stays
in one explicit shared database. Blue/green slots are code/process slots; they
never silently clone or replace user state.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


class RuntimeControlError(RuntimeError):
    """A fail-closed runtime-control error."""


@dataclass(frozen=True)
class Slot:
    slot_id: str
    gateway_port: int
    webui_port: int


SLOTS = {
    "blue": Slot("blue", 11435, 8080),
    "green": Slot("green", 11436, 8081),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != "estate.canonical-webui-gateway.v1":
        raise RuntimeControlError("unsupported canonical runtime configuration")
    source_root = Path(config["source_root"]).resolve()
    if source_root != Path(__file__).resolve().parents[3]:
        raise RuntimeControlError(f"canonical source root mismatch: {source_root}")
    if not source_root.joinpath("src", "estate").is_dir():
        raise RuntimeControlError("canonical source root is not an Estate checkout")
    for key in ("DATA_DIR", "DATABASE_URL", "PYTHONPATH", "ESTATE_ROOT"):
        if key in os.environ:
            raise RuntimeControlError(f"unexpected inherited override: {key}")
    return config


def source_commit(source_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def canonical_state_identity(config: dict[str, Any]) -> dict[str, Any]:
    database = Path(config["open_webui"]["database"]).resolve()
    data_dir = Path(config["open_webui"]["data_dir"]).resolve()
    if database.parent != data_dir or database.name != "webui.db":
        raise RuntimeControlError("database must be the canonical data directory webui.db")
    return {
        "data_dir": str(data_dir),
        "database": str(database),
        "database_sha256": sha256_file(database) if database.exists() else None,
    }


def _state_paths(config: dict[str, Any]) -> tuple[Path, Path, Path]:
    root = Path(config["state_root"]).resolve()
    return root, root / "active-slot.json", root / "slot-manifests"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with temporary.open("r+b") as handle:
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def _http_json(url: str, timeout: float = 3.0) -> tuple[int, dict[str, Any] | None]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = response.read()
            return response.status, json.loads(data.decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return 0, None


def _http_status(url: str, timeout: float = 3.0) -> int:
    try:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read(1024)
            return response.status
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0


def _port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.2)
        return probe.connect_ex((host, port)) == 0


def _grace_entry(payload: dict[str, Any]) -> dict[str, Any] | None:
    for entry in payload.get("data", []):
        if entry.get("id") == "estate/grace":
            return entry
    return None


def gateway_readiness(config: dict[str, Any], slot: Slot) -> dict[str, Any]:
    gateway = config["gateway"]
    status, payload = _http_json(f"http://{gateway['host']}:{slot.gateway_port}{gateway['health_path']}")
    entry = _grace_entry(payload or {})
    ready = bool(
        status == 200
        and entry
        and entry.get("estate", {}).get("resident_id") == "grace"
        and entry.get("estate", {}).get("resident_gateway_capable") is True
        and entry.get("estate", {}).get("privileged_actions_enabled") is False
    )
    return {"ready": ready, "http_status": status, "grace_present": entry is not None, "model": entry}


def _sqlite_identity(database: Path) -> dict[str, Any]:
    import sqlite3

    if not database.exists():
        return {"quick_check": "missing", "users": [], "models": [], "tools": [], "functions": []}
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        quick = connection.execute("PRAGMA quick_check").fetchone()[0]
        tables = {row[0] for row in connection.execute("select name from sqlite_master where type='table'")}
        def rows(table: str, query: str) -> list[tuple[Any, ...]]:
            return connection.execute(query).fetchall() if table in tables else []
        users = rows("user", 'select id,name,email,role from "user"')
        models = rows("model", 'select id,name,base_model_id,meta from "model"')
        tools = rows("tool", 'select id,name from "tool"')
        functions = rows("function", 'select id,name,is_active,is_global from "function"')
        return {"quick_check": quick, "users": users, "models": models, "tools": tools, "functions": functions}
    finally:
        connection.close()


def webui_readiness(config: dict[str, Any], slot: Slot) -> dict[str, Any]:
    webui = config["open_webui"]
    state = _sqlite_identity(Path(webui["database"]))
    models = []
    for row in state["models"]:
        try:
            meta = json.loads(row[3]) if isinstance(row[3], str) else row[3]
        except (TypeError, ValueError):
            meta = {}
        models.append({"id": row[0], "base_model_id": row[2], "meta": meta})
    expected_model = webui["expected_model"]
    model = next((item for item in models if item["id"] == expected_model), None)
    tool_ids = {row[0] for row in state["tools"]}
    function_ids = {row[0] for row in state["functions"]}
    bridge_ready = bool(
        model
        and model["base_model_id"] == webui["expected_base_model"]
        and "grace_runtime_bridge" in tool_ids
        and "grace_runtime_grounding" in function_ids
        and "grace_runtime_grounding" in set((model["meta"] or {}).get("filterIds", []))
        and "grace_runtime_bridge" in set((model["meta"] or {}).get("toolIds", []))
    )
    ready = bool(
        _http_status(f"http://{webui['host']}:{slot.webui_port}{webui['health_path']}") in range(200, 500)
        and state["quick_check"] == "ok"
        and any(row[3] == "admin" for row in state["users"])
        and bridge_ready
    )
    return {"ready": ready, "state": state, "bridge_ready": bridge_ready, "model": model}


def _manifest(config: dict[str, Any], slot: Slot, status: str, validation: dict[str, Any]) -> dict[str, Any]:
    root = Path(config["source_root"])
    state = canonical_state_identity(config)
    return {
        "schema_version": "estate.runtime-slot-manifest.v1",
        "slot_id": slot.slot_id,
        "source_root": str(root),
        "source_commit": source_commit(root),
        "gateway_port": slot.gateway_port,
        "webui_port": slot.webui_port,
        "gateway_executable": config["gateway"]["python"],
        "webui_executable": config["open_webui"]["executable"],
        "webui_version": config["open_webui"]["version"],
        "state_identity": state,
        "bridge_deployment_version": config["bridge_deployment_version"],
        "validation_status": status,
        "validation": validation,
        "updated_at": utc_now(),
    }


def _process_command(config: dict[str, Any], slot: Slot) -> tuple[list[str], list[str], dict[str, str]]:
    root = Path(config["source_root"])
    env = {key: value for key, value in os.environ.items() if key not in {"DATA_DIR", "DATABASE_URL", "PYTHONPATH", "ESTATE_ROOT"}}
    env["PYTHONPATH"] = str(root / "src")
    env["DATA_DIR"] = str(Path(config["open_webui"]["data_dir"]))
    env["DATABASE_URL"] = "sqlite:///" + str(Path(config["open_webui"]["database"]).as_posix())
    secret_path = Path(config["open_webui"]["secret_key_file"])
    if not secret_path.is_file():
        raise RuntimeControlError("canonical Open WebUI secret key is missing")
    env["WEBUI_SECRET_KEY"] = secret_path.read_text(encoding="utf-8").strip()
    gateway = [config["gateway"]["python"], "-m", config["gateway"]["module"], "resident-gateway", "start", "--host", config["gateway"]["host"], "--port", str(slot.gateway_port)]
    webui = [config["open_webui"]["executable"], "serve", "--host", config["open_webui"]["host"], "--port", str(slot.webui_port)]
    return gateway, webui, env


def _launch(command: list[str], cwd: Path, env: dict[str, str], log_path: Path) -> subprocess.Popen[str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stream = log_path.open("a", encoding="utf-8")
    return subprocess.Popen(command, cwd=str(cwd), env=env, stdout=stream, stderr=subprocess.STDOUT, text=True)


def _process_command_line(pid: int) -> str:
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", f"(Get-CimInstance Win32_Process -Filter 'ProcessId = {int(pid)}').CommandLine"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout.strip()


def _process_snapshot(pid: int) -> dict[str, Any] | None:
    """Return the live Windows identity for a PID, or None when it is gone."""
    script = (
        f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId = {int(pid)}' "
        "-ErrorAction SilentlyContinue; "
        "if ($null -ne $p) { $p | Select-Object ProcessId,ParentProcessId,CommandLine,ExecutablePath,CreationDate | "
        "ConvertTo-Json -Compress }"
    )
    result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", script], capture_output=True, text=True, timeout=10)
    if not result.stdout.strip():
        return None
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _identity_matches(snapshot: dict[str, Any] | None, slot: Slot, service: str) -> bool:
    if not snapshot:
        return False
    command = str(snapshot.get("CommandLine") or "").lower()
    executable = str(snapshot.get("ExecutablePath") or "").lower()
    port = str(slot.gateway_port if service == "gateway" else slot.webui_port)
    if port not in command:
        return False
    if service == "gateway":
        return "resident-gateway" in command and "python" in executable
    return "open-webui.exe" in command and "a:\\ai\\openwebui" in executable + command


def _port_owner_pids(port: int) -> list[int]:
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", f"Get-NetTCPConnection -LocalPort {int(port)} -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"],
        capture_output=True, text=True, timeout=10,
    )
    owners: list[int] = []
    for line in result.stdout.splitlines():
        try:
            owners.append(int(line.strip()))
        except ValueError:
            continue
    return owners


def _runtime_status(config: dict[str, Any], slot: Slot, state: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "schema_version": "estate.canonical-runtime-status.v1",
        "state": state,
        "active_slot": slot.slot_id,
        "checked_at": utc_now(),
        "data_dir": str(Path(config["open_webui"]["data_dir"]).resolve()),
        "database": str(Path(config["open_webui"]["database"]).resolve()),
        **extra,
    }
    _write_json(_state_paths(config)[0] / "runtime-status.json", payload)
    return payload


def _validate_process_identity(processes: list[subprocess.Popen[str]], slot: Slot, services: tuple[str, ...]) -> None:
    lines = [_process_command_line(process.pid).lower() for process in processes]
    combined = "\n".join(lines)
    if "gateway" in services and ("resident-gateway" not in combined or str(slot.gateway_port) not in combined):
        raise RuntimeControlError("Gateway process identity does not match the canonical command")
    if "webui" in services and ("open-webui.exe" not in combined or str(slot.webui_port) not in combined):
        raise RuntimeControlError("Open WebUI process identity does not match the canonical command")


def start_slot(config: dict[str, Any], slot_id: str, *, services: tuple[str, ...] = ("gateway", "webui"), active_ports: bool = False, wait_seconds: float = 45.0, sleeper: Callable[[float], None] = time.sleep, open_browser: bool = False) -> dict[str, Any]:
    if slot_id not in SLOTS:
        raise RuntimeControlError(f"unknown slot: {slot_id}")
    configured = SLOTS[slot_id]
    slot = Slot(slot_id, config["gateway"]["active_port"], config["open_webui"]["active_port"]) if active_ports else configured
    if _port_open(slot.gateway_port) or _port_open(slot.webui_port):
        raise RuntimeControlError(f"candidate ports already owned for {slot_id}")
    root, _, manifests = _state_paths(config)
    if set(services) - {"gateway", "webui"} or not services:
        raise RuntimeControlError("services must contain gateway and/or webui")
    gateway_command, webui_command, env = _process_command(config, slot)
    processes = []
    try:
        if "gateway" in services:
            processes.append(_launch(gateway_command, Path(config["source_root"]), env, root / "logs" / f"{slot_id}-gateway.log"))
        if "webui" in services:
            processes.append(_launch(webui_command, Path(config["open_webui"]["working_directory"]), env, root / "logs" / f"{slot_id}-webui.log"))
        deadline = time.monotonic() + wait_seconds
        validation: dict[str, Any] = {}
        while time.monotonic() < deadline:
            validation = {"gateway": gateway_readiness(config, slot), "webui": webui_readiness(config, slot)}
            required_ready = all(validation[service]["ready"] for service in services)
            if required_ready:
                _validate_process_identity(processes, slot, services)
                manifest = _manifest(config, slot, "validated" if set(services) == {"gateway", "webui"} else f"{services[0]}-ready", validation)
                _write_json(manifests / f"{slot_id}.json", manifest)
                _write_json(root / f"{slot_id}-processes.json", {"slot_id": slot_id, "pids": [p.pid for p in processes], "started_at": utc_now()})
                _runtime_status(config, slot, "running" if active_ports else "candidate-running", pids=[p.pid for p in processes], validation=validation)
                if open_browser:
                    # Browser launch is deliberately after semantic readiness.
                    subprocess.Popen(["cmd.exe", "/d", "/s", "/c", "start", "", f"http://{config['open_webui']['host']}:{slot.webui_port}/"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return manifest
            if any(p.poll() is not None for p in processes):
                break
            sleeper(0.5)
        validation = {"gateway": gateway_readiness(config, slot), "webui": webui_readiness(config, slot)}
        raise RuntimeControlError(json.dumps({"slot": slot_id, "validation": validation}, sort_keys=True))
    except Exception:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        raise


def stop_slot(config: dict[str, Any], slot_id: str) -> dict[str, Any]:
    if slot_id not in SLOTS:
        raise RuntimeControlError(f"unknown slot: {slot_id}")
    slot = SLOTS[slot_id]
    root, _, _ = _state_paths(config)
    process_path = root / f"{slot_id}-processes.json"
    pids = []
    if process_path.exists():
        pids = json.loads(process_path.read_text(encoding="utf-8")).get("pids", [])
    # Include the live owners of the canonical ports. This closes the gap
    # where a stale PID record made stop appear successful while an older
    # Estate process continued serving the port.
    pids = sorted(set(pids) | set(_port_owner_pids(slot.gateway_port)) | set(_port_owner_pids(slot.webui_port)))
    terminated = []
    for raw_pid in pids:
        snapshot = _process_snapshot(int(raw_pid))
        command = str((snapshot or {}).get("CommandLine") or "").lower()
        if not ("resident-gateway" in command or "open-webui.exe" in command):
            continue
        try:
            process = subprocess.Popen(["taskkill", "/PID", str(int(raw_pid)), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            process.wait(timeout=10)
            terminated.append(int(raw_pid))
        except (ValueError, OSError, subprocess.TimeoutExpired):
            continue
    process_path.unlink(missing_ok=True)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and (_port_open(slot.gateway_port) or _port_open(slot.webui_port)):
        time.sleep(0.25)
    closed = not _port_open(slot.gateway_port) and not _port_open(slot.webui_port)
    result = {"slot_id": slot_id, "terminated_pids": terminated, "ports_closed": closed}
    _runtime_status(config, slot, "stopped" if closed else "degraded", **result)
    if not closed:
        raise RuntimeControlError(json.dumps(result, sort_keys=True))
    return result


def promote(config: dict[str, Any], slot_id: str) -> dict[str, Any]:
    root, active_path, _ = _state_paths(config)
    manifest_path = _state_paths(config)[2] / f"{slot_id}.json"
    if not manifest_path.exists():
        raise RuntimeControlError("slot has no validated manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("validation_status") != "validated":
        raise RuntimeControlError("only a validated slot may be promoted")
    slot = SLOTS[slot_id]
    validation = {"gateway": gateway_readiness(config, slot), "webui": webui_readiness(config, slot)}
    if not validation["gateway"]["ready"] or not validation["webui"]["ready"]:
        raise RuntimeControlError("post-candidate semantic validation failed")
    previous = None
    if active_path.exists():
        previous = json.loads(active_path.read_text(encoding="utf-8")).get("active_slot")
    # The candidate has been validated on its isolated ports. Stop it, stop
    # the managed active slot, then start the same code/state on canonical
    # public ports and revalidate before publishing promotion metadata.
    stop_slot(config, slot_id)
    if previous and previous != slot_id:
        stop_slot(config, previous)
    promoted_manifest = start_slot(config, slot_id, active_ports=True)
    validation = promoted_manifest["validation"]
    if not validation["gateway"]["ready"] or not validation["webui"]["ready"]:
        raise RuntimeControlError("post-promotion semantic validation failed")
    manifest_path = _state_paths(config)[2] / f"{slot_id}.json"
    manifest = promoted_manifest
    record = {"schema_version": "estate.runtime-promotion.v1", "active_slot": slot_id, "previous_slot": previous, "manifest_sha256": sha256_file(manifest_path), "source_commit": manifest["source_commit"], "state_identity": manifest["state_identity"], "promoted_at": utc_now(), "institutional_acceptance_state": "not_granted"}
    _write_json(active_path, record)
    _write_json(root / "last-promotion.json", record)
    return record


def rollback(config: dict[str, Any]) -> dict[str, Any]:
    root, active_path, manifests = _state_paths(config)
    if not active_path.exists():
        raise RuntimeControlError("no active slot promotion record")
    current = json.loads(active_path.read_text(encoding="utf-8"))
    previous = current.get("previous_slot")
    if previous not in SLOTS:
        raise RuntimeControlError("no known-good rollback slot")
    manifest_path = manifests / f"{previous}.json"
    if not manifest_path.exists():
        raise RuntimeControlError("rollback manifest is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("validation_status") != "validated":
        raise RuntimeControlError("rollback slot is not validated")
    stop_slot(config, current.get("active_slot"))
    promoted_manifest = start_slot(config, previous, active_ports=True)
    if not promoted_manifest["validation"]["gateway"]["ready"] or not promoted_manifest["validation"]["webui"]["ready"]:
        raise RuntimeControlError("rollback semantic validation failed")
    record = {"schema_version": "estate.runtime-promotion.v1", "active_slot": previous, "previous_slot": current.get("active_slot"), "manifest_sha256": sha256_file(manifest_path), "source_commit": manifest["source_commit"], "state_identity": manifest["state_identity"], "rollback_of": current.get("promoted_at"), "promoted_at": utc_now(), "institutional_acceptance_state": "not_granted"}
    _write_json(active_path, record)
    _write_json(root / "last-rollback.json", record)
    return record


def status(config: dict[str, Any]) -> dict[str, Any]:
    root, active_path, manifests = _state_paths(config)
    active = json.loads(active_path.read_text(encoding="utf-8")) if active_path.exists() else None
    manifest_map = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in manifests.glob("*.json")}
    live = None
    if active and active.get("active_slot") in SLOTS:
        slot = SLOTS[active["active_slot"]]
        process_record = root / f"{slot.slot_id}-processes.json"
        pids = []
        if process_record.exists():
            try:
                pids = [int(pid) for pid in json.loads(process_record.read_text(encoding="utf-8")).get("pids", [])]
            except (ValueError, TypeError, json.JSONDecodeError):
                pids = []
        snapshots = [_process_snapshot(pid) for pid in pids]
        live = {
            "slot_id": slot.slot_id,
            "pids": pids,
            "processes_match": len(snapshots) == 2 and _identity_matches(snapshots[0], slot, "gateway") and _identity_matches(snapshots[1], slot, "webui"),
            "gateway": gateway_readiness(config, slot),
            "webui": webui_readiness(config, slot),
        }
        live["healthy"] = bool(live["processes_match"] and live["gateway"]["ready"] and live["webui"]["ready"])
        live["state"] = "running" if live["healthy"] else "degraded"
    runtime_status_path = root / "runtime-status.json"
    recorded_status = json.loads(runtime_status_path.read_text(encoding="utf-8")) if runtime_status_path.exists() else None
    return {"active": active, "runtime": live, "recorded_status": recorded_status, "manifests": manifest_map, "source_commit": source_commit(Path(config["source_root"])), "state_identity": canonical_state_identity(config)}


def restart(config: dict[str, Any]) -> dict[str, Any]:
    active = status(config).get("active") or {"active_slot": "blue"}
    slot_id = active.get("active_slot", "blue")
    stop_slot(config, slot_id)
    manifest = start_slot(config, slot_id, active_ports=True)
    if not manifest["validation"]["gateway"]["ready"] or not manifest["validation"]["webui"]["ready"]:
        raise RuntimeControlError("restart semantic validation failed")
    _, active_path, manifests = _state_paths(config)
    refreshed = dict(active)
    refreshed["manifest_sha256"] = sha256_file(manifests / f"{slot_id}.json")
    refreshed["state_identity"] = manifest["state_identity"]
    refreshed["source_commit"] = manifest["source_commit"]
    refreshed["refreshed_at"] = utc_now()
    _write_json(active_path, refreshed)
    return {"restarted_slot": slot_id, "manifest": manifest, "active": refreshed}
