"""Provider-neutral physical compute-resource evidence and placement.

NVIDIA UUID is the durable physical identity. Runtime ordinals are observations
only. This module performs no CUDA work and no device recovery.
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


def _number(value: Any) -> float | None:
    try:
        if value in (None, "", "N/A", "[Not Supported]"):
            return None
        return float(str(value).replace("MiB", "").replace("%", "").replace("W", "").strip())
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
    observation_timestamp: str = field(default_factory=utc_now)
    evidence_sources: list[str] = field(default_factory=list)
    health_state: str = "unknown"
    health_reasons: list[str] = field(default_factory=list)
    capacity_state: str = "unknown"
    capacity_reasons: list[str] = field(default_factory=list)
    allocation_references: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not str(self.resource_id).strip() or not str(self.host_id).strip():
            raise ValueError("resource_id and host_id are required")
        if not str(self.nvidia_uuid).strip() or not str(self.name).strip():
            raise ValueError("nvidia_uuid and name are required")
        if self.health_state not in HEALTH_STATES or self.capacity_state not in CAPACITY_STATES:
            raise ValueError("invalid compute resource state")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComputeResourceRequirements:
    requires_gpu: bool = False
    minimum_vram_mib: float | None = None
    required_compute_capability: str | None = None
    required_resource_id: str | None = None
    preferred_resource_id: str | None = None
    required_gpu_uuid: str | None = None
    preferred_gpu_uuid: str | None = None
    excluded_resource_ids: tuple[str, ...] = ()
    compatibility_tags: tuple[str, ...] = ()
    reservation_reference: str | None = None
    evidence_reference: str | None = None
    freshness_seconds: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ComputeResourceRequirements":
        raw = data if isinstance(data, dict) else {}
        return cls(
            requires_gpu=bool(raw.get("requires_gpu", False)),
            minimum_vram_mib=_number(raw.get("minimum_vram_mib")),
            required_compute_capability=raw.get("required_compute_capability"),
            required_resource_id=raw.get("required_resource_id"),
            preferred_resource_id=raw.get("preferred_resource_id"),
            required_gpu_uuid=raw.get("required_gpu_uuid"),
            preferred_gpu_uuid=raw.get("preferred_gpu_uuid"),
            excluded_resource_ids=tuple(str(x) for x in raw.get("excluded_resource_ids", []) or []),
            compatibility_tags=tuple(str(x) for x in raw.get("compatibility_tags", []) or []),
            reservation_reference=raw.get("reservation_reference"),
            evidence_reference=raw.get("evidence_reference"),
            freshness_seconds=int(raw["freshness_seconds"]) if raw.get("freshness_seconds") is not None else None,
        )

    def validate(self) -> None:
        if self.minimum_vram_mib is not None and self.minimum_vram_mib < 0:
            raise ValueError("minimum_vram_mib must be non-negative")
        if self.freshness_seconds is not None and self.freshness_seconds <= 0:
            raise ValueError("freshness_seconds must be positive")
        if self.required_resource_id and self.required_resource_id in self.excluded_resource_ids:
            raise ValueError("required resource cannot be excluded")
        if self.required_gpu_uuid and self.preferred_gpu_uuid and self.required_gpu_uuid != self.preferred_gpu_uuid:
            raise ValueError("required and preferred GPU UUIDs conflict")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        value["excluded_resource_ids"] = list(self.excluded_resource_ids)
        value["compatibility_tags"] = list(self.compatibility_tags)
        return value


def canonical_resource_id(host_id: str, nvidia_uuid: str) -> str:
    return f"{host_id}:nvidia:{nvidia_uuid}"


def reconcile_runtime_ordinals(observations: Iterable[ComputeResourceObservation], runtime_devices: Iterable[dict[str, Any]]) -> list[ComputeResourceObservation]:
    devices = list(observations)
    by_uuid = {d.nvidia_uuid: d for d in devices}
    by_name = {d.name: d for d in devices}
    for item in runtime_devices:
        if not isinstance(item, dict):
            continue
        device = by_uuid.get(str(item.get("nvidia_uuid") or item.get("uuid") or "")) or by_name.get(str(item.get("name") or ""))
        try:
            ordinal = int(item["ordinal"])
        except (KeyError, TypeError, ValueError):
            continue
        if device is not None and ordinal not in device.runtime_ordinals:
            device.runtime_ordinals.append(ordinal)
            device.runtime_ordinals.sort()
    return devices


def classify_observation(observation: ComputeResourceObservation, *, now: str | None = None, freshness_seconds: int = 120, required_vram_mib: float | None = None) -> ComputeResourceObservation:
    current = _dt(now or utc_now())
    observed = _dt(observation.observation_timestamp)
    reasons: list[str] = []
    if current is None or observed is None or (current - observed).total_seconds() > freshness_seconds:
        reasons.append("telemetry is stale or timestamp is invalid")
    if not observation.visible_in_nvml:
        reasons.append("device is not visible in NVML")
    if observation.pnp_present is False or observation.pnp_problem_code not in (None, 0):
        reasons.append("Windows device presence/problem evidence is not healthy")
    if not observation.nvidia_uuid or not observation.name:
        reasons.append("physical identity is incomplete")
    if not reasons:
        observation.health_state = "healthy"
    elif any("visible" in r or "presence" in r or "identity" in r for r in reasons):
        observation.health_state = "unavailable"
    elif any("stale" in r or "timestamp" in r for r in reasons):
        observation.health_state = "stale"
    else:
        observation.health_state = "degraded"
    observation.health_reasons = reasons or ["identity and telemetry evidence is current"]
    if required_vram_mib is not None and (observation.memory_free_mib is None or observation.memory_free_mib < required_vram_mib):
        observation.capacity_state = "insufficient"
        observation.capacity_reasons = [f"free VRAM is below required {required_vram_mib:g} MiB"]
    elif observation.health_state != "healthy":
        observation.capacity_state = "unknown"
        observation.capacity_reasons = ["health evidence does not permit admission"]
    else:
        observation.capacity_state = "available"
        observation.capacity_reasons = ["capacity evidence permits admission"]
    return observation


def select_resource(observations: Iterable[ComputeResourceObservation], requirements: ComputeResourceRequirements) -> dict[str, Any]:
    requirements.validate()
    devices = list(observations)
    if not requirements.requires_gpu:
        return {"selected": None, "eligible": True, "reason": "GPU not required", "excluded": {}}
    excluded: dict[str, list[str]] = {}
    eligible: list[ComputeResourceObservation] = []
    for device in devices:
        reasons: list[str] = []
        if device.resource_id in requirements.excluded_resource_ids:
            reasons.append("resource is explicitly excluded")
        if requirements.required_resource_id and device.resource_id != requirements.required_resource_id:
            reasons.append("required physical resource does not match")
        if requirements.required_gpu_uuid and device.nvidia_uuid != requirements.required_gpu_uuid:
            reasons.append("required GPU UUID does not match")
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
    required_resource_present = not requirements.required_resource_id or any(
        d.resource_id == requirements.required_resource_id for d in eligible
    )
    required_uuid_present = not requirements.required_gpu_uuid or any(
        d.nvidia_uuid == requirements.required_gpu_uuid for d in eligible
    )
    if not required_resource_present or not required_uuid_present:
        return {"selected": None, "eligible": False, "reason": "required physical GPU is unavailable; no fallback permitted", "excluded": excluded}
    preferred = next((d for d in eligible if d.resource_id == requirements.preferred_resource_id or d.nvidia_uuid == requirements.preferred_gpu_uuid), None)
    selected = preferred or (eligible[0] if eligible else None)
    return {"selected": selected.resource_id if selected else None, "eligible": selected is not None, "reason": "preferred resource selected" if preferred else ("alternate eligible resource selected" if selected else "no eligible physical GPU"), "excluded": excluded}


def collect_nvidia_smi(*, host_id: str | None = None, runner=subprocess.run) -> list[ComputeResourceObservation]:
    query = "uuid,name,pci.bus_id,driver_version,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw,compute_mode"
    try:
        result = runner(["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5, check=False)
        if getattr(result, "returncode", 1) != 0:
            return []
        host = host_id or platform.node() or "unknown-host"
        observations: list[ComputeResourceObservation] = []
        for row in csv.reader(io.StringIO(getattr(result, "stdout", ""))):
            if len(row) < 11 or not row[0].strip() or not row[1].strip():
                continue
            uuid, name = row[0].strip(), row[1].strip()
            observations.append(classify_observation(ComputeResourceObservation(
                resource_id=canonical_resource_id(host, uuid), host_id=host, nvidia_uuid=uuid, name=name,
                pci_bus_id=row[2].strip() or None, driver_version=row[3].strip() or None,
                memory_total_mib=_number(row[4]), memory_used_mib=_number(row[5]), memory_free_mib=_number(row[6]),
                utilization_percent=_number(row[7]), temperature_c=_number(row[8]), power_draw_w=_number(row[9]),
                compute_mode=row[10].strip() or None, evidence_sources=["nvidia-smi"])))
        return observations
    except (OSError, subprocess.SubprocessError, ValueError):
        return []


def build_compute_projection(observations: Iterable[ComputeResourceObservation], *, workloads: list[dict[str, Any]] | None = None, reservations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    devices = [d.to_dict() for d in observations]
    return {"schema_version": "compute_resources.v1", "generated_at": utc_now(), "resource_count": len(devices), "resources": devices, "workloads": workloads or [], "reservations": reservations or [], "canonical_identity": "host_id + NVIDIA UUID; runtime ordinal is observational only", "safe_recovery": "classify and stop admission; no automatic reset, reconfigure, reboot, or cold cycle"}


def write_compute_projection(observations: Iterable[ComputeResourceObservation], root: str | Path | None = None, *, workloads: list[dict[str, Any]] | None = None, reservations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    base = Path(root) if root is not None else ESTATE_ROOT
    payload = build_compute_projection(observations, workloads=workloads, reservations=reservations)
    path = base / GPU_SNAPSHOT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


class ComputeReservationLedger:
    """Exclusive-resource reservation hook owned by governed scheduling."""
    def __init__(self, root: str | Path | None = None) -> None:
        self.path = (Path(root) if root is not None else ESTATE_ROOT) / GPU_RESERVATIONS

    def _load(self) -> list[dict[str, Any]]:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def active(self) -> list[dict[str, Any]]:
        return [row for row in self._load() if row.get("state") == "reserved"]

    def reserve(self, *, reservation_id: str, resource_id: str, workload_id: str, minimum_vram_mib: float | None = None) -> dict[str, Any]:
        rows = self._load()
        if any(row.get("resource_id") == resource_id and row.get("state") == "reserved" for row in rows):
            raise ValueError(f"resource is already reserved: {resource_id}")
        record = {"reservation_id": reservation_id, "resource_id": resource_id, "workload_id": workload_id, "minimum_vram_mib": minimum_vram_mib, "state": "reserved", "created_at": utc_now()}
        rows.append(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return record

    def release(self, reservation_id: str) -> bool:
        rows = self._load(); changed = False
        for row in rows:
            if row.get("reservation_id") == reservation_id and row.get("state") == "reserved":
                row["state"], row["released_at"] = "released", utc_now(); changed = True
        if changed:
            self.path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return changed
