"""Governed physical-GPU runtime lanes.

Lanes are configuration and evidence for an isolated provider process.  A
lane's NVIDIA UUID is canonical; CUDA ordinals are deliberately absent from
the contract.  This module never resets devices and never selects a fallback.
"""
from __future__ import annotations

import json
import os
import socket
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

LANE_CONFIG = Path("config/runtime/gpu_runtime_lanes.json")
LANE_EVIDENCE = Path("runtime/compute_resources/runtime_lanes.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _loopback(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"} and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment


def _ollama_host_matches(endpoint: str, host: str) -> bool:
    parsed = urlparse(endpoint)
    return host in {f"{parsed.hostname}:{parsed.port}", f"http://{parsed.hostname}:{parsed.port}"}


@dataclass(frozen=True)
class RuntimeLane:
    runtime_lane_id: str
    provider_id: str
    endpoint_type: str
    endpoint_address: str
    host_id: str
    compute_resource_id: str
    gpu_uuid: str
    model_identity: str
    environment_binding: dict[str, str]
    state: str = "registered"
    health_reference: str | None = None
    capacity_reference: str | None = None
    process_id: int | None = None
    process_identity: str | None = None
    started_at: str | None = None
    observed_at: str | None = None
    freshness_seconds: int = 120

    def validate(self) -> None:
        for key in ("runtime_lane_id", "provider_id", "endpoint_type", "endpoint_address", "host_id", "compute_resource_id", "gpu_uuid", "model_identity"):
            if not str(getattr(self, key) or "").strip():
                raise ValueError(f"runtime lane requires {key}")
        if self.endpoint_type != "ollama-http" or not _loopback(self.endpoint_address):
            raise ValueError("runtime lane endpoint must be loopback ollama-http")
        if not self.gpu_uuid.startswith("GPU-"):
            raise ValueError("runtime lane requires a full NVIDIA UUID")
        if self.environment_binding.get("CUDA_VISIBLE_DEVICES") != self.gpu_uuid:
            raise ValueError("runtime lane CUDA binding must equal its full GPU UUID")
        allowed = {"CUDA_VISIBLE_DEVICES", "OLLAMA_HOST"}
        if set(self.environment_binding) - allowed:
            raise ValueError("runtime lane environment contains an unapproved field")
        if self.environment_binding.get("OLLAMA_HOST") and not _ollama_host_matches(self.endpoint_address, self.environment_binding["OLLAMA_HOST"]):
            raise ValueError("runtime lane OLLAMA_HOST must equal its endpoint")
        if self.freshness_seconds < 1:
            raise ValueError("runtime lane freshness_seconds must be positive")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def load_registered_lanes(root: str | Path) -> list[RuntimeLane]:
    path = Path(root) / LANE_CONFIG
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows = payload.get("lanes") if isinstance(payload, dict) else None
    lanes: list[RuntimeLane] = []
    for row in rows or []:
        try:
            lane = RuntimeLane(**row)
            lane.validate()
            lanes.append(lane)
        except (TypeError, ValueError):
            continue
    return lanes


def select_runtime_lane(lanes: Iterable[RuntimeLane], *, provider_id: str, model_identity: str, required_gpu_uuid: str | None = None, required_resource_id: str | None = None, preferred_gpu_uuid: str | None = None) -> dict[str, Any]:
    candidates = list(lanes)
    excluded: dict[str, str] = {}
    eligible: list[RuntimeLane] = []
    for lane in candidates:
        try:
            lane.validate()
        except ValueError as exc:
            excluded[lane.runtime_lane_id] = str(exc)
            continue
        if lane.provider_id != provider_id:
            excluded[lane.runtime_lane_id] = "provider mismatch"; continue
        if lane.model_identity != model_identity:
            excluded[lane.runtime_lane_id] = "model mismatch"; continue
        if lane.state != "registered":
            excluded[lane.runtime_lane_id] = f"lane state is {lane.state}"; continue
        if required_gpu_uuid and lane.gpu_uuid != required_gpu_uuid:
            excluded[lane.runtime_lane_id] = "required GPU UUID mismatch"; continue
        if required_resource_id and lane.compute_resource_id != required_resource_id:
            excluded[lane.runtime_lane_id] = "required resource mismatch"; continue
        eligible.append(lane)
    selected = next((lane for lane in eligible if preferred_gpu_uuid and lane.gpu_uuid == preferred_gpu_uuid), None) or (eligible[0] if eligible else None)
    return {"selected": selected.runtime_lane_id if selected else None, "eligible": selected is not None, "reason": "registered runtime lane selected" if selected else "no registered runtime lane satisfies the required physical identity", "excluded": excluded}


def require_allocation_matches_lane(*, allocated_gpu_uuid: str | None, allocated_resource_id: str | None, lane: RuntimeLane) -> None:
    lane.validate()
    if allocated_gpu_uuid != lane.gpu_uuid:
        raise PermissionError("allocated GPU UUID does not match runtime lane binding")
    if allocated_resource_id != lane.compute_resource_id:
        raise PermissionError("allocated resource does not match runtime lane binding")


def lane_environment(lane: RuntimeLane) -> dict[str, str]:
    lane.validate()
    parsed = urlparse(lane.endpoint_address)
    return {"CUDA_VISIBLE_DEVICES": lane.gpu_uuid, "OLLAMA_HOST": f"{parsed.hostname}:{parsed.port}"}


def process_binding_evidence(lane: RuntimeLane, *, pid: int, process_identity: str, started_at: str | None = None) -> dict[str, Any]:
    lane.validate()
    return {"schema_version": "estate.gpu-runtime-lane-evidence.v1", "runtime_lane_id": lane.runtime_lane_id, "provider_id": lane.provider_id, "endpoint_address": lane.endpoint_address, "host_id": lane.host_id, "compute_resource_id": lane.compute_resource_id, "gpu_uuid": lane.gpu_uuid, "model_identity": lane.model_identity, "environment_binding": lane_environment(lane), "process_id": int(pid), "process_identity": process_identity, "started_at": started_at or utc_now(), "observed_at": utc_now(), "hostname": socket.gethostname()}


def endpoint_health(lane: RuntimeLane, *, timeout_seconds: float = 2.0) -> dict[str, Any]:
    lane.validate()
    url = lane.endpoint_address.rstrip("/") + "/api/tags"
    try:
        with urlopen(Request(url, method="GET"), timeout=timeout_seconds) as response:
            return {"healthy": 200 <= response.status < 300, "status": response.status, "runtime_lane_id": lane.runtime_lane_id, "observed_at": utc_now()}
    except Exception as exc:
        return {"healthy": False, "runtime_lane_id": lane.runtime_lane_id, "observed_at": utc_now(), "reason": str(exc)[:300]}


def start_ollama_lane(root: str | Path, lane: RuntimeLane, *, executable: str | None = None) -> dict[str, Any]:
    lane.validate()
    binary = executable or shutil.which("ollama")
    if not binary:
        raise FileNotFoundError("ollama executable is not available on PATH")
    env = os.environ.copy()
    env.update(lane_environment(lane))
    env["OLLAMA_KEEP_ALIVE"] = "0"
    flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
    process = subprocess.Popen([binary, "serve"], cwd=str(Path(root)), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
    evidence = process_binding_evidence(lane, pid=process.pid, process_identity=f"{Path(binary).name} serve", started_at=utc_now())
    path = Path(root) / LANE_EVIDENCE
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    rows = existing.get("lanes", []) if isinstance(existing, dict) else []
    rows = [row for row in rows if row.get("runtime_lane_id") != lane.runtime_lane_id]
    rows.append(evidence)
    path.write_text(json.dumps({"schema_version": "estate.gpu-runtime-lane-evidence.v1", "lanes": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence
