"""Canonical, semantic, fail-closed WebUI/Gateway/Grace runtime controller.

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
    grace_port: int
    gateway_port: int
    webui_port: int


SLOTS = {
    "blue": Slot("blue", 8766, 11435, 8080),
    "green": Slot("green", 8767, 11436, 8081),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _open_browser_url(url: str) -> None:
    """Open a URL through the normal Windows shell without cmd empty-argv parsing."""
    if hasattr(os, "startfile"):
        os.startfile(url)  # type: ignore[attr-defined]
        return
    subprocess.Popen(["python", "-m", "webbrowser", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


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
    grace = config.get("grace_runtime")
    if not isinstance(grace, dict) or grace.get("active_port") != 8766 or grace.get("candidate_port") != 8767:
        raise RuntimeControlError("canonical Grace runtime ports are missing or incorrect")
    if Path(grace.get("root", "")).resolve() != source_root:
        raise RuntimeControlError("canonical Grace runtime root mismatch")
    expected_environment = {
        "DATA_DIR": str(Path(config["open_webui"]["data_dir"]).resolve()),
        "DATABASE_URL": "sqlite:///" + str(Path(config["open_webui"]["database"]).as_posix()),
        "PYTHONPATH": str(source_root / "src"),
    }
    for key, expected in expected_environment.items():
        inherited = os.environ.get(key)
        if inherited is not None and inherited != expected:
            raise RuntimeControlError(f"inherited override does not match canonical {key}")
    if os.environ.get("ESTATE_ROOT") not in (None, str(source_root)):
        raise RuntimeControlError("inherited override does not match canonical ESTATE_ROOT")
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


def _append_event(config: dict[str, Any], event: str, **fields: Any) -> None:
    """Record operator-boundary events without recording secrets."""
    root, _, _ = _state_paths(config)
    path = root / "logs" / "operator-actions.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": event, "at": utc_now(), **fields}, sort_keys=True) + "\n")


def _http_json(url: str, timeout: float = 3.0) -> tuple[int, dict[str, Any] | None]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = response.read()
            return response.status, json.loads(data.decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return 0, None


def _grace_http_json(config: dict[str, Any], port: int, path: str, timeout: float = 3.0) -> tuple[int, dict[str, Any] | None]:
    grace = config["grace_runtime"]
    claims = {"iss": grace["authentication_issuer"], "sub": "canonical-runtime-controller", "office": "Runtime", "authority_source": "canonical-runtime-controller", "active": True}
    request = urllib.request.Request(f"http://{grace['host']}:{port}{path}", headers={"Accept": "application/json", "X-Estate-Claims": json.dumps(claims)})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, OSError):
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


def grace_runtime_readiness(config: dict[str, Any], slot: Slot) -> dict[str, Any]:
    grace = config["grace_runtime"]
    health_status, health = _grace_http_json(config, slot.grace_port, grace["health_path"])
    readiness_status, readiness = _grace_http_json(config, slot.grace_port, grace["readiness_path"])
    ready = bool(
        health_status == 200 and readiness_status == 200
        and health and health.get("service") == "grace-momentum" and health.get("healthy") is True
        and readiness and readiness.get("service") == "grace-momentum" and readiness.get("ready") is True
        and readiness.get("mode") == grace["mode"]
        and readiness.get("persistence_healthy") is True
        and readiness.get("replay_healthy") is True
        and readiness.get("idempotency_healthy") is True
    )
    return {"ready": ready, "health_http_status": health_status, "readiness_http_status": readiness_status, "health": health, "readiness": readiness}


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
        configs = rows("config", 'select key,value from "config"')
        return {"quick_check": quick, "users": users, "models": models, "tools": tools, "functions": functions, "configs": configs}
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
    config_values = {row[0]: row[1] for row in state.get("configs", [])}
    try:
        api_base_urls = json.loads(config_values.get("openai.api_base_urls", "[]"))
    except (TypeError, ValueError, json.JSONDecodeError):
        api_base_urls = []
    expected_gateway_url = f"http://{config['gateway']['host']}:{slot.gateway_port}/v1"
    local_gateway_urls = [str(url).rstrip("/") for url in api_base_urls if "127.0.0.1" in str(url) or "localhost" in str(url)]
    bridge_endpoint = local_gateway_urls[0] if len(local_gateway_urls) == 1 else None
    bridge_slot_consistent = bridge_endpoint == expected_gateway_url
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
        and bridge_slot_consistent
    )
    return {
        "ready": ready,
        "state": state,
        "bridge_ready": bridge_ready,
        "model": model,
        "bridge_endpoint": bridge_endpoint,
        "expected_gateway_url": expected_gateway_url,
        "bridge_slot_consistent": bridge_slot_consistent,
    }


def _bind_candidate_webui_gateway(config: dict[str, Any], slot: Slot) -> None:
    """Bind the shared WebUI config to a managed candidate slot.

    Open WebUI persists its OpenAI-compatible endpoints in the shared database;
    process environment is only used to seed missing defaults. The controller
    therefore owns this short-lived candidate binding and records only the
    prior endpoint list (never API keys) for restoration on stop.
    """
    if slot.slot_id == "blue":
        return
    active_port = config["gateway"]["active_port"]
    if _port_open(active_port):
        raise RuntimeControlError("cannot bind candidate WebUI while active Gateway is listening")
    database = Path(config["open_webui"]["database"])
    state_root, _, _ = _state_paths(config)
    binding_path = state_root / "slot-route-bindings" / f"{slot.slot_id}.json"
    if binding_path.exists():
        raise RuntimeControlError(f"candidate WebUI route binding already exists for {slot.slot_id}")
    state = _sqlite_identity(database)
    values = {row[0]: row[1] for row in state.get("configs", [])}
    raw_urls = values.get("openai.api_base_urls")
    try:
        urls = json.loads(raw_urls) if raw_urls is not None else []
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeControlError("Open WebUI api_base_urls config is invalid") from exc
    if not isinstance(urls, list):
        raise RuntimeControlError("Open WebUI api_base_urls config is not a list")
    local_indexes = [index for index, url in enumerate(urls) if "127.0.0.1" in str(url) or "localhost" in str(url)]
    if len(local_indexes) != 1:
        raise RuntimeControlError("Open WebUI must have exactly one local Estate Gateway endpoint")
    target = f"http://{config['gateway']['host']}:{slot.gateway_port}/v1"
    prior_urls = [str(url) for url in urls]
    urls[local_indexes[0]] = target
    import sqlite3
    connection = sqlite3.connect(database)
    try:
        connection.execute("update config set value=? where key=?", (json.dumps(urls), "openai.api_base_urls"))
        if connection.total_changes != 1:
            raise RuntimeControlError("Open WebUI api_base_urls config row is missing")
        connection.commit()
    finally:
        connection.close()
    _write_json(binding_path, {"schema_version": "estate.webui-slot-route-binding.v1", "slot_id": slot.slot_id, "prior_api_base_urls": prior_urls, "bound_api_base_url": target, "bound_at": utc_now()})


def _restore_candidate_webui_gateway(config: dict[str, Any], slot_id: str) -> None:
    if slot_id == "blue":
        return
    state_root, _, _ = _state_paths(config)
    binding_path = state_root / "slot-route-bindings" / f"{slot_id}.json"
    if not binding_path.exists():
        return
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    prior_urls = binding.get("prior_api_base_urls")
    if not isinstance(prior_urls, list):
        raise RuntimeControlError("candidate WebUI route binding cannot be restored")
    import sqlite3
    database = Path(config["open_webui"]["database"])
    connection = sqlite3.connect(database)
    try:
        connection.execute("update config set value=? where key=?", (json.dumps(prior_urls), "openai.api_base_urls"))
        if connection.total_changes != 1:
            raise RuntimeControlError("Open WebUI api_base_urls config row is missing during restore")
        connection.commit()
    finally:
        connection.close()
    binding_path.unlink()


def _manifest(config: dict[str, Any], slot: Slot, status: str, validation: dict[str, Any]) -> dict[str, Any]:
    root = Path(config["source_root"])
    state = canonical_state_identity(config)
    return {
        "schema_version": "estate.runtime-slot-manifest.v1",
        "slot_id": slot.slot_id,
        "source_root": str(root),
        "source_commit": source_commit(root),
        "grace_port": slot.grace_port,
        "gateway_port": slot.gateway_port,
        "webui_port": slot.webui_port,
        "grace_executable": config["grace_runtime"]["python"],
        "grace_runtime_root": config["grace_runtime"]["root"],
        "gateway_executable": config["gateway"]["python"],
        "webui_executable": config["open_webui"]["executable"],
        "webui_version": config["open_webui"]["version"],
        "state_identity": state,
        "bridge_deployment_version": config["bridge_deployment_version"],
        "validation_status": status,
        "validation": validation,
        "updated_at": utc_now(),
    }


def _process_command(config: dict[str, Any], slot: Slot) -> tuple[list[str], list[str], list[str], dict[str, str]]:
    root = Path(config["source_root"])
    env = {key: value for key, value in os.environ.items() if key not in {"DATA_DIR", "DATABASE_URL", "PYTHONPATH", "ESTATE_ROOT"}}
    env["PYTHONPATH"] = str(root / "src")
    env["ESTATE_ROOT"] = str(root)
    env["DATA_DIR"] = str(Path(config["open_webui"]["data_dir"]))
    env["DATABASE_URL"] = "sqlite:///" + str(Path(config["open_webui"]["database"]).as_posix())
    secret_path = Path(config["open_webui"]["secret_key_file"])
    if not secret_path.is_file():
        raise RuntimeControlError("canonical Open WebUI secret key is missing")
    env["WEBUI_SECRET_KEY"] = secret_path.read_text(encoding="utf-8").strip()
    grace_config = config["grace_runtime"]
    grace = [grace_config["python"], grace_config["script"], "--root", grace_config["root"], "--host", grace_config["host"], "--port", str(slot.grace_port), "--mode", grace_config["mode"]]
    gateway = [config["gateway"]["python"], "-m", config["gateway"]["module"], "resident-gateway", "start", "--host", config["gateway"]["host"], "--port", str(slot.gateway_port), "--root", str(root)]
    webui = [config["open_webui"]["executable"], "serve", "--host", config["open_webui"]["host"], "--port", str(slot.webui_port)]
    return grace, gateway, webui, env


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


def _identity_matches(snapshot: dict[str, Any] | None, slot: Slot, service: str, source_root: Path | None = None) -> bool:
    if not snapshot:
        return False
    command = str(snapshot.get("CommandLine") or "").lower()
    executable = str(snapshot.get("ExecutablePath") or "").lower()
    port = str({"grace_runtime": slot.grace_port, "gateway": slot.gateway_port, "webui": slot.webui_port}[service])
    if service == "grace_runtime":
        return "run_grace_momentum_runtime.py" in command and port in command and "python" in executable and (source_root is None or f"--root {str(source_root).lower()}" in command)
    if port not in command:
        return False
    if service == "gateway":
        return "resident-gateway" in command and "python" in executable and (source_root is None or f"--root {str(source_root).lower()}" in command)
    return "open-webui.exe" in command and "a:\\ai\\openwebui" in executable + command


def _environment_matches(pid: int, config: dict[str, Any], service: str) -> bool:
    """Verify the actual live environment, failing closed if it cannot be read."""
    try:
        import psutil
    except ImportError:
        return False
    try:
        environment = psutil.Process(pid).environ()
    except (OSError, psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False
    root = Path(config["source_root"]).resolve()
    expected = {
        "ESTATE_ROOT": str(root),
        "PYTHONPATH": str(root / "src"),
    }
    if service in {"grace_runtime", "webui"}:
        expected.update({
            "DATA_DIR": str(Path(config["open_webui"]["data_dir"]).resolve()),
            "DATABASE_URL": "sqlite:///" + str(Path(config["open_webui"]["database"]).resolve().as_posix()),
        })
    return all(environment.get(key) == value for key, value in expected.items())


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
        "ports": {"grace_runtime": slot.grace_port, "gateway": slot.gateway_port, "webui": slot.webui_port},
        **extra,
    }
    _write_json(_state_paths(config)[0] / "runtime-status.json", payload)
    return payload


def _validate_process_identity(config: dict[str, Any], processes: dict[str, subprocess.Popen[str]], slot: Slot, services: tuple[str, ...]) -> None:
    for service in services:
        if not _identity_matches(_process_snapshot(processes[service].pid), slot, service, Path(config["source_root"]).resolve()) or not _environment_matches(processes[service].pid, config, service):
            raise RuntimeControlError(f"{service} process identity does not match the canonical command")


def _required_services_ready(validation: dict[str, Any], services: tuple[str, ...]) -> bool:
    return bool(services) and all(validation.get(service, {}).get("ready") is True for service in services)


def _slot_ports(config: dict[str, Any], slot_id: str) -> Slot:
    slot = _slot_ports(config, slot_id)
    _, active_path, _ = _state_paths(config)
    if active_path.exists():
        try:
            active = json.loads(active_path.read_text(encoding="utf-8"))
            if active.get("active_slot") == slot_id:
                return Slot(slot_id, config["grace_runtime"]["active_port"], config["gateway"]["active_port"], config["open_webui"]["active_port"])
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            pass
    return slot


def start_slot(config: dict[str, Any], slot_id: str, *, services: tuple[str, ...] = ("grace_runtime", "gateway", "webui"), active_ports: bool = False, wait_seconds: float = 120.0, sleeper: Callable[[float], None] = time.sleep, open_browser: bool = False) -> dict[str, Any]:
    if slot_id not in SLOTS:
        raise RuntimeControlError(f"unknown slot: {slot_id}")
    configured = SLOTS[slot_id]
    slot = Slot(slot_id, config["grace_runtime"]["active_port"], config["gateway"]["active_port"], config["open_webui"]["active_port"]) if active_ports else configured
    if any(_port_open(port) for port in (slot.grace_port, slot.gateway_port, slot.webui_port)):
        raise RuntimeControlError(f"candidate ports already owned for {slot_id}")
    root, _, manifests = _state_paths(config)
    if set(services) - {"grace_runtime", "gateway", "webui"} or not services:
        raise RuntimeControlError("services must contain grace_runtime, gateway, and/or webui")
    grace_command, gateway_command, webui_command, env = _process_command(config, slot)
    commands = {"grace_runtime": (grace_command, Path(config["grace_runtime"]["working_directory"])), "gateway": (gateway_command, Path(config["source_root"])), "webui": (webui_command, Path(config["open_webui"]["working_directory"]))}
    processes: dict[str, subprocess.Popen[str]] = {}
    route_bound = False
    try:
        if "webui" in services:
            _bind_candidate_webui_gateway(config, slot)
            route_bound = slot.slot_id != "blue"
        for service in ("grace_runtime", "gateway", "webui"):
            if service in services:
                command, cwd = commands[service]
                processes[service] = _launch(command, cwd, env, root / "logs" / f"{slot_id}-{service}.log")
        deadline = time.monotonic() + wait_seconds
        validation: dict[str, Any] = {}
        while time.monotonic() < deadline:
            validation = {"grace_runtime": grace_runtime_readiness(config, slot), "gateway": gateway_readiness(config, slot), "webui": webui_readiness(config, slot)}
            required_ready = _required_services_ready(validation, services)
            if required_ready:
                _validate_process_identity(config, processes, slot, services)
                manifest = _manifest(config, slot, "validated" if set(services) == {"grace_runtime", "gateway", "webui"} else f"{services[0]}-ready", validation)
                _write_json(manifests / f"{slot_id}.json", manifest)
                _write_json(root / f"{slot_id}-processes.json", {"slot_id": slot_id, "services": {name: process.pid for name, process in processes.items()}, "pids": [p.pid for p in processes.values()], "started_at": utc_now()})
                _runtime_status(config, slot, "running" if active_ports else "candidate-running", pids=[p.pid for p in processes.values()], services=list(services), validation=validation)
                _append_event(config, "start.semantic_ready", slot=slot_id, active_ports=active_ports, services=list(services), pids=[p.pid for p in processes.values()], data_dir=manifest["state_identity"]["data_dir"], database=manifest["state_identity"]["database"])
                if open_browser:
                    # Browser launch is deliberately after semantic readiness.
                    _open_browser_url(f"http://{config['open_webui']['host']}:{slot.webui_port}/")
                    _append_event(config, "browser.open_requested", slot=slot_id, url=f"http://{config['open_webui']['host']}:{slot.webui_port}/")
                return manifest
            if any(p.poll() is not None for p in processes.values()):
                break
            sleeper(0.5)
        validation = {"grace_runtime": grace_runtime_readiness(config, slot), "gateway": gateway_readiness(config, slot), "webui": webui_readiness(config, slot)}
        raise RuntimeControlError(json.dumps({"slot": slot_id, "validation": validation}, sort_keys=True))
    except Exception:
        for process in processes.values():
            if process.poll() is None:
                process.terminate()
        if route_bound:
            _restore_candidate_webui_gateway(config, slot.slot_id)
        raise


def open_browser(config: dict[str, Any]) -> dict[str, Any]:
    """Open the canonical WebUI without re-starting an already healthy slot."""
    current = status(config)
    runtime = current.get("runtime", {})
    active_slot = current.get("active", {}).get("active_slot", "blue")
    if runtime.get("healthy") is not True or runtime.get("slot_id") != active_slot:
        return start_slot(config, active_slot, active_ports=True, open_browser=True)

    webui = runtime.get("webui", {})
    if webui.get("ready") is not True:
        raise RuntimeControlError("canonical WebUI is not semantically ready")
    url = f"http://{config['open_webui']['host']}:{config['open_webui']['active_port']}/"
    _open_browser_url(url)
    _append_event(config, "browser.open_requested", slot=active_slot, url=url, reused_healthy_runtime=True)
    return {"state": "browser-opened", "active_slot": active_slot, "url": url, "runtime": current}


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
    pids = sorted(set(pids) | set(_port_owner_pids(slot.grace_port)) | set(_port_owner_pids(slot.gateway_port)) | set(_port_owner_pids(slot.webui_port)))
    terminated = []
    for raw_pid in pids:
        snapshot = _process_snapshot(int(raw_pid))
        command = str((snapshot or {}).get("CommandLine") or "").lower()
        if not ("run_grace_momentum_runtime.py" in command or "resident-gateway" in command or "open-webui.exe" in command):
            continue
        try:
            process = subprocess.Popen(["taskkill", "/PID", str(int(raw_pid)), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            process.wait(timeout=10)
            terminated.append(int(raw_pid))
        except (ValueError, OSError, subprocess.TimeoutExpired):
            continue
    process_path.unlink(missing_ok=True)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and any(_port_open(port) for port in (slot.grace_port, slot.gateway_port, slot.webui_port)):
        time.sleep(0.25)
    closed = not any(_port_open(port) for port in (slot.grace_port, slot.gateway_port, slot.webui_port))
    result = {"slot_id": slot_id, "terminated_pids": terminated, "ports_closed": closed}
    _runtime_status(config, slot, "stopped" if closed else "degraded", **result)
    _append_event(config, "stop.completed", **result)
    if not closed:
        raise RuntimeControlError(json.dumps(result, sort_keys=True))
    _restore_candidate_webui_gateway(config, slot_id)
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
    validation = {"grace_runtime": grace_runtime_readiness(config, slot), "gateway": gateway_readiness(config, slot), "webui": webui_readiness(config, slot)}
    if not _required_services_ready(validation, ("grace_runtime", "gateway", "webui")):
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
    if not _required_services_ready(validation, ("grace_runtime", "gateway", "webui")):
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
    if not _required_services_ready(promoted_manifest["validation"], ("grace_runtime", "gateway", "webui")):
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
            "processes_match": len(snapshots) == 3
            and _identity_matches(snapshots[0], slot, "grace_runtime", Path(config["source_root"]).resolve())
            and _identity_matches(snapshots[1], slot, "gateway", Path(config["source_root"]).resolve())
            and _identity_matches(snapshots[2], slot, "webui", Path(config["source_root"]).resolve())
            and all(_environment_matches(pid, config, service) for pid, service in zip(pids, ("grace_runtime", "gateway", "webui"))),
            "grace_runtime": grace_runtime_readiness(config, slot),
            "gateway": gateway_readiness(config, slot),
            "webui": webui_readiness(config, slot),
        }
        live["healthy"] = bool(live["processes_match"] and _required_services_ready(live, ("grace_runtime", "gateway", "webui")))
        live["state"] = "running" if live["healthy"] else "degraded"
    runtime_status_path = root / "runtime-status.json"
    recorded_status = json.loads(runtime_status_path.read_text(encoding="utf-8")) if runtime_status_path.exists() else None
    return {"active": active, "runtime": live, "recorded_status": recorded_status, "manifests": manifest_map, "source_commit": source_commit(Path(config["source_root"])), "state_identity": canonical_state_identity(config)}


def restart(config: dict[str, Any]) -> dict[str, Any]:
    active = status(config).get("active") or {"active_slot": "blue"}
    slot_id = active.get("active_slot", "blue")
    stop_slot(config, slot_id)
    manifest = start_slot(config, slot_id, active_ports=True)
    if not _required_services_ready(manifest["validation"], ("grace_runtime", "gateway", "webui")):
        raise RuntimeControlError("restart semantic validation failed")
    _, active_path, manifests = _state_paths(config)
    refreshed = dict(active)
    refreshed["manifest_sha256"] = sha256_file(manifests / f"{slot_id}.json")
    refreshed["state_identity"] = manifest["state_identity"]
    refreshed["source_commit"] = manifest["source_commit"]
    refreshed["refreshed_at"] = utc_now()
    _write_json(active_path, refreshed)
    return {"restarted_slot": slot_id, "manifest": manifest, "active": refreshed}
