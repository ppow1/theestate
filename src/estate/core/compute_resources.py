"""Provider-neutral physical compute resource evidence and placement.

GPU ordinals are observations only.  The durable identity for an NVIDIA GPU
is its UUID, qualified by host and device name.  This module deliberately
contains no CUDA work and no recovery actions; callers supply observations or
use the read-only nvidia-smi collector.
"""
from __future__ import annotations

import csv
import io
import json
import platform
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from estate.core.paths import ESTATE_ROOT

HEALTH_STATES = {"healthy", "degraded", "unavailable", "stale", "unknown"}
CAPACITY_STATES = {"available", "busy", "reserved", "insufficient", "unknown"}
GPU_SNAPSHOT = Path("runtime/compute_resources/gpus.json")
GPU_RESERVATIONS = Path("runtime/engineering_scheduler/compute_reservations.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _dt(value: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")) if value else None
    except (TypeError, ValueError):
        return None


def _num(value: Any) -> float | None:
    try:
        if value in (None, "", "N/A", "[Not Supported]"):
            return None
        return float(str(value).replace("MiB", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return None


@dataclass
class ComputeResourceObservation:
    resource_id: str
    host_id: str
    nvidia_uuid: str
    name: str
    pci_bus_id: str | None = None
    visible_in_nvml: bool = True
    pnp_present: bool | None = None
    pnp_status: str | None = None
    pnp_problem_code: int | None = None
    driver_version: str | None = None
    memory_total_mib: float | None = None
    memory_used_mib: float | None = None
    memory_free_mib: float | None = None
    utilization_percent: float | None = None
    temperature_c: float | None = None
    power_draw_w: float | None = None
    compute_mode: str | None = None
    compute_capability: str | None = None
    runtime_ordinals: list[int] = field(default_factory=list)
    observed_at: str = field(default_factory=utc_now)
    evidence_sources: list[str] = field(default_factory=list)
    health_state: str = "unknown"
    health_reasons: list[str] = field(default_factory=list)
    capacity_state: str = "unknown"
    capacity_reasons: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.nvidia_uuid.strip():
            raise ValueError("nvidia_uuid is required for a physical compute resource")
        if not self.resource_id.strip():
            raise ValueError("resource_id is required")
        if self.health_state not in HEALTH_STATES or self.capacity_state not in CAPACITY_STATES:
            raise ValueError("invalid compute resource state")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComputeResourceRequirements:
    requires_gpu: bool = False
    minimum_vram_mib: float | None = None
    required_compute_capability: str | None = None
    preferred_resource_id: str | None = None
    required_resource_id: str | None = None
    excluded_resource_ids: tuple[str, ...] = ()
    compatibility_tags: tuple[str, ...] = ()
    reservation_reference: str | None = None
    evidence_observation: str | None = None

    def validate(self) -> None:
        if self.minimum_vram_mib is not None and self.minimum_vram_mib < 0:
            raise ValueError("minimum_vram_mib must be non-negative")
        if self.required_resource_id and self.required_resource_id in self.excluded_resource_ids:
            raise ValueError("required resource cannot be excluded")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        data = asdict(self)
        for key in ("excluded_resource_ids", "compatibility_tags"):
            data[key] = list(data[key])
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ComputeResourceRequirements":
        data = data if isinstance(data, dict) else {}
        return cls(
            requires_gpu=bool(data.get("requires_gpu", False)),
            minimum_vram_mib=_num(data.get("minimum_vram_mib")),
            required_compute_capability=data.get("required_compute_capability"),
            preferred_resource_id=data.get("preferred_resource_id"),
            required_resource_id=data.get("required_resource_id"),
            excluded_resource_ids=tuple(str(x) for x in data.get("excluded_resource_ids", []) or []),
            compatibility_tags=tuple(str(x) for x in data.get("compatibility_tags", []) or []),
            reservation_reference=data.get("reservation_reference"),
            evidence_observation=data.get("evidence_observation"),
        )


def canonical_resource_id(host_id: str, nvidia_uuid: str) -> str:
    return f"{host_id}:nvidia:{nvidia_uuid}"


def reconcile_runtime_ordinals(observations: Iterable[ComputeResourceObservation], runtime_devices: Iterable[dict[str, Any]]) -> list[ComputeResourceObservation]:
    by_uuid = {o.nvidia_uuid: o for o in observations}
    by_name = {o.name: o for o in observations}
    for item in runtime_devices:
        if not isinstance(item, dict):
            continue
        target = by_uuid.get(str(item.get("nvidia_uuid") or item.get("uuid") or ""))
        if target is None:
            target = by_name.get(str(item.get("name") or ""))
        try:
            ordinal = int(item["ordinal"])
        except (KeyError, TypeError, ValueError):
            continue
        if target is not None and ordinal not in target.runtime_ordinals:
            target.runtime_ordinals.append(ordinal)
            target.runtime_ordinals.sort()
    return list(observations)


def classify_observation(observation: ComputeResourceObservation, *, now: str | None = None, freshness_seconds: int = 120, required_vram_mib: float | None = None) -> ComputeResourceObservation:
    reasons: list[str] = []
    age = None if _dt(observation.observed_at) is None or _dt(now or utc_now()) is None else (_dt(now or utc_now()) - _dt(observation.observed_at)).total_seconds()
    if age is None or age > freshness_seconds:
        reasons.append("telemetry is stale or timestamp is invalid")
    if not observation.visible_in_nvml:
        reasons.append("device is not visible in NVML")
    if observation.pnp_present is False or observation.pnp_problem_code not in (None, 0):
        reasons.append("Windows device presence/problem evidence is not healthy")
    if not observation.nvidia_uuid or not observation.name:
        reasons.append("physical identity is incomplete")
    if reasons and any("stale" in r or "timestamp" in r for r in reasons) and len(reasons) == 1:
        observation.health_state = "stale"
    elif reasons and any("visible" in r or "presence" in r or "identity" in r for r in reasons):
        observation.health_state = "unavailable"
    elif reasons:
        observation.health_state = "degraded"
    else:
        observation.health_state = "healthy"
    observation.health_reasons = reasons or ["identity and telemetry evidence is current"]
    if required_vram_mib is not None and (observation.memory_free_mib is None or observation.memory_free_mib < required_vram_mib):
        observation.capacity_state = "insufficient"
        observation.capacity_reasons = [f"free VRAM is below required {required_vram_mib:g} MiB"]
    elif observation.health_state in {"unavailable", "stale", "unknown"}:
        observation.capacity_state = "unknown"
        observation.capacity_reasons = ["health evidence does not permit admission"]
    else:
        observation.capacity_state = "available"
        observation.capacity_reasons = ["capacity evidence permits admission"]
    return observation


def select_resource(observations: Iterable[ComputeResourceObservation], requirements: ComputeResourceRequirements) -> dict[str, Any]:
    requirements.validate()
    devices = list(observations)
    eligible = []
    excluded: dict[str, list[str]] = {}
    for device in devices:
        reasons: list[str] = []
        if not requirements.requires_gpu:
            continue
        if device.resource_id in requirements.excluded_resource_ids:
            reasons.append("resource is explicitly excluded")
        if requirements.required_resource_id and device.resource_id != requirements.required_resource_id:
            reasons.append("required physical resource does not match")
        if device.health_state != "healthy":
            reasons.append(f"health is {device.health_state}")
        if device.capacity_state != "available":
            reasons.append(f"capacity is {device.capacity_state}")
        if requirements.minimum_vram_mib is not None and (device.memory_free_mib or 0) < requirements.minimum_vram_mib:
            reasons.append("minimum VRAM is unavailable")
        if requirements.required_compute_capability and device.compute_capability != requirements.required_compute_capability:
            reasons.append("compute capability does not match")
        if reasons:
            excluded[device.resource_id] = reasons
        else:
            eligible.append(device)
    if not requirements.requires_gpu:
        return {"selected": None, "eligible": True, "reason": "GPU not required", "excluded": excluded}
    if requirements.required_resource_id and not any(d.resource_id == requirements.required_resource_id for d in eligible):
        return {"selected": None, "eligible": False, "reason": "required physical GPU is unavailable; no fallback permitted", "excluded": excluded}
    preferred = next((d for d in eligible if d.resource_id == requirements.preferred_resource_id), None)
    selected = preferred or (eligible[0] if eligible else None)
    return {"selected": selected.resource_id if selected else None, "eligible": selected is not None, "reason": "preferred resource selected" if preferred else ("alternate eligible resource selected" if selected else "no eligible physical GPU"), "excluded": excluded}


def collect_nvidia_smi(*, host_id: str | None = None, runner=subprocess.run) -> list[ComputeResourceObservation]:
    query = "uuid,name,pci.bus_id,driver_version,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw,compute_mode"
    try:
        result = runner(["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5, check=False)
        if getattr(result, "returncode", 1) != 0:
            return []
        rows = csv.reader(io.StringIO(getattr(result, "stdout", "")))
        host = host_id or platform.node() or "unknown-host"
        devices = []
        for row in rows:
            if len(row) < 11:
                continue
            uuid = row[0].strip()
            name = row[1].strip()
            if not uuid or not name:
                continue
            devices.append(classify_observation(ComputeResourceObservation(resource_id=canonical_resource_id(host, uuid), host_id=host, nvidia_uuid=uuid, name=name, pci_bus_id=row[2].strip() or None, driver_version=row[3].strip() or None, memory_total_mib=_num(row[4]), memory_used_mib=_num(row[5]), memory_free_mib=_num(row[6]), utilization_percent=_num(row[7]), temperature_c=_num(row[8]), power_draw_w=_num(row[9]), compute_mode=row[10].strip() or None, evidence_sources=["nvidia-smi"])))
        return devices
    except (OSError, subprocess.SubprocessError, ValueError):
        return []


def build_compute_projection(observations: Iterable[ComputeResourceObservation], *, workloads: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    devices = [o.to_dict() for o in observations]
    return {"schema_version": "compute_resources.v1", "generated_at": utc_now(), "resource_count": len(devices), "resources": devices, "workloads": workloads or [], "canonical_identity": "host_id + NVIDIA UUID; runtime ordinal is observational only", "safe_recovery": "classify and stop admission; no automatic reset, reconfigure, reboot, or cold cycle"}


def write_compute_projection(observations: Iterable[ComputeResourceObservation], root: str | Path | None = None, *, workloads: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    base = Path(root) if root is not None else ESTATE_ROOT
    payload = build_compute_projection(observations, workloads=workloads)
    path = base / GPU_SNAPSHOT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


class ComputeReservationLedger:
    """Reservation hook used by the existing governed scheduler; not a scheduler."""
    def __init__(self, root: str | Path | None = None) -> None:
        self.path = (Path(root) if root is not None else ESTATE_ROOT) / GPU_RESERVATIONS

    def _load(self) -> list[dict[str, Any]]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def reserve(self, *, reservation_id: str, resource_id: str, workload_id: str, minimum_vram_mib: float | None = None) -> dict[str, Any]:
        rows = [r for r in self._load() if r.get("state") == "reserved"]
        if any(r.get("resource_id") == resource_id for r in rows):
            raise ValueError(f"resource is already reserved: {resource_id}")
        record = {"reservation_id": reservation_id, "resource_id": resource_id, "workload_id": workload_id, "minimum_vram_mib": minimum_vram_mib, "state": "reserved", "created_at": utc_now()}
        rows.append(record); self.path.parent.mkdir(parents=True, exist_ok=True); self.path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8"); return record

    def release(self, reservation_id: str) -> bool:
        rows = self._load(); changed = False
        for row in rows:
            if row.get("reservation_id") == reservation_id and row.get("state") == "reserved": row["state"] = "released"; row["released_at"] = utc_now(); changed = True
        if changed: self.path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return changed
