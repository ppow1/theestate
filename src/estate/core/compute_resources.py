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

HEALTH_STATES = {"HEALTHY", "DEGRADED", "LOST", "UNKNOWN"}
CAPACITY_STATES = {"available", "busy", "reserved", "insufficient", "unknown"}
GPU_HEALTH_CLASSIFICATIONS = {"HEALTHY", "DEGRADED", "CUDA_UNAVAILABLE", "NVML_UNAVAILABLE", "DEVICE_MISSING", "IDENTITY_MISMATCH", "UNSAFE_TO_DISPATCH"}
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
    expected_name: str | None = None
    expected_pci_bus_id: str | None = None
    nvidia_smi_index: int | None = None
    cuda_index: int | None = None
    windows_present: bool | None = None
    windows_problem_code: int | None = None
    cuda_present: bool | None = None
    identity_consistent: bool = True
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
    health_state: str = "UNKNOWN"
    health_reasons: list[str] = field(default_factory=list)
    capacity_state: str = "unknown"
    capacity_reasons: list[str] = field(default_factory=list)
    dispatch_allowed: bool = False
    dispatch_reason: str = "identity and health have not been established"
    health_classification: str = "UNSAFE_TO_DISPATCH"

    def __post_init__(self) -> None:
        if not self.nvidia_uuid.strip():
            raise ValueError("nvidia_uuid is required for a physical compute resource")
        if not self.resource_id.strip():
            raise ValueError("resource_id is required")
        if self.health_state not in HEALTH_STATES or self.capacity_state not in CAPACITY_STATES or self.health_classification not in GPU_HEALTH_CLASSIFICATIONS:
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
            target.cuda_index = target.runtime_ordinals[0]
            target.cuda_present = True
            target.compute_capability = item.get("compute_capability") or target.compute_capability
            target.memory_total_mib = item.get("memory_total_mib") or target.memory_total_mib
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
        observation.health_state = "UNKNOWN"
    elif reasons and any("visible" in r or "presence" in r or "identity" in r for r in reasons):
        observation.health_state = "LOST"
    elif reasons:
        observation.health_state = "DEGRADED"
    else:
        observation.health_state = "HEALTHY"
    observation.health_reasons = reasons or ["identity and telemetry evidence is current"]
    if required_vram_mib is not None and (observation.memory_free_mib is None or observation.memory_free_mib < required_vram_mib):
        observation.capacity_state = "insufficient"
        observation.capacity_reasons = [f"free VRAM is below required {required_vram_mib:g} MiB"]
    elif observation.health_state in {"LOST", "UNKNOWN"}:
        observation.capacity_state = "unknown"
        observation.capacity_reasons = ["health evidence does not permit admission"]
    else:
        observation.capacity_state = "available"
        observation.capacity_reasons = ["capacity evidence permits admission"]
    if not observation.identity_consistent or not observation.nvidia_uuid or not observation.name:
        observation.health_classification = "IDENTITY_MISMATCH"
    elif not observation.visible_in_nvml:
        observation.health_classification = "NVML_UNAVAILABLE"
    elif observation.pnp_present is False or observation.pnp_problem_code not in (None, 0):
        observation.health_classification = "DEVICE_MISSING"
    elif observation.cuda_present is False:
        observation.health_classification = "CUDA_UNAVAILABLE"
    elif observation.health_state == "DEGRADED":
        observation.health_classification = "DEGRADED"
    elif observation.health_state == "HEALTHY":
        observation.health_classification = "HEALTHY"
    else:
        observation.health_classification = "UNSAFE_TO_DISPATCH"
    observation.dispatch_allowed = observation.health_classification == "HEALTHY" and observation.capacity_state == "available"
    observation.dispatch_reason = "physical identity, Windows/NVML/CUDA visibility, and fresh telemetry agree" if observation.dispatch_allowed else "; ".join(observation.health_reasons) or observation.health_classification
    return observation


@dataclass(frozen=True)
class ExpectedGPU:
    """Stable host inventory entry; never inferred from a runtime ordinal."""
    nvidia_uuid: str
    expected_name: str
    pci_bus_id: str | None = None
    role: str | None = None


GRACE_EXPECTED_GPUS = (
    ExpectedGPU("GPU-6785b322-899d-8eec-e817-31d83279a414", "Tesla P100-PCIE-16GB", "04:00.0", "bounded background / secondary inference"),
    ExpectedGPU("GPU-46f3fd00-5454-4536-4196-5d8b727e14f2", "NVIDIA GeForce RTX 4090", "07:00.0", "primary latency-sensitive / interactive"),
)


def build_gpu_inventory(expected: Iterable[ExpectedGPU], observations: Iterable[ComputeResourceObservation], *, windows_devices: Iterable[dict[str, Any]] = (), runtime_devices: Iterable[dict[str, Any]] = (), now: str | None = None, freshness_seconds: int = 120) -> list[ComputeResourceObservation]:
    """Join expected physical devices to NVML, Windows, and CUDA observations."""
    observed = {item.nvidia_uuid: item for item in observations}
    windows = list(windows_devices)
    result: list[ComputeResourceObservation] = []
    for spec in expected:
        item = observed.get(spec.nvidia_uuid)
        if item is None:
            host = next(iter(observed.values())).host_id if observed else platform.node() or "unknown-host"
            item = ComputeResourceObservation(resource_id=canonical_resource_id(host, spec.nvidia_uuid), host_id=host, nvidia_uuid=spec.nvidia_uuid, name=spec.expected_name, expected_name=spec.expected_name, expected_pci_bus_id=spec.pci_bus_id, visible_in_nvml=False, windows_present=None, cuda_present=False, observed_at=now or utc_now(), evidence_sources=["expected-inventory"])
        item.expected_name = spec.expected_name
        item.expected_pci_bus_id = spec.pci_bus_id
        item.identity_consistent = item.name == spec.expected_name and (not spec.pci_bus_id or not item.pci_bus_id or item.pci_bus_id.endswith(spec.pci_bus_id))
        # PnP friendly names commonly include a vendor prefix; physical identity
        # is still established by the UUID/name/PCI evidence from nvidia-smi.
        def _device_name(value: Any) -> str:
            return str(value or "").strip().lower().removeprefix("nvidia ")
        match = next((row for row in windows if _device_name(row.get("name")) == _device_name(spec.expected_name) or (spec.pci_bus_id and str(row.get("pci_bus_id", "")).endswith(spec.pci_bus_id))), None)
        if match is not None:
            item.windows_present = bool(match.get("present", match.get("status", "OK") == "OK"))
            item.windows_problem_code = match.get("problem_code")
            item.pnp_present = item.windows_present
            item.pnp_problem_code = item.windows_problem_code
        elif item.windows_present is None:
            item.windows_present = None
        if runtime_devices:
            item.cuda_present = False
        reconcile_runtime_ordinals([item], runtime_devices)
        classify_observation(item, now=now, freshness_seconds=freshness_seconds)
        if not item.identity_consistent:
            item.health_state = "UNKNOWN"
            item.health_classification = "IDENTITY_MISMATCH"
            item.health_classification = "IDENTITY_MISMATCH"
            item.health_reasons = ["authoritative UUID/name/PCI identity mapping disagrees"]
            item.dispatch_allowed = False
            item.dispatch_reason = item.health_reasons[0]
        elif runtime_devices and item.cuda_present is False:
            item.health_state = "LOST"
            item.health_classification = "CUDA_UNAVAILABLE"
            item.health_classification = "CUDA_UNAVAILABLE"
            item.health_reasons = ["CUDA/PyTorch cannot see the expected physical device"]
            item.dispatch_allowed = False
            item.dispatch_reason = item.health_reasons[0]
        elif item.windows_present is False or item.windows_problem_code not in (None, 0):
            item.health_state = "LOST"
            item.health_classification = "DEVICE_MISSING"
            item.health_classification = "DEVICE_MISSING"
            item.health_reasons = ["Windows reports the expected physical device absent or in a problem state"]
            item.dispatch_allowed = False
            item.dispatch_reason = item.health_reasons[0]
        result.append(item)
    return result


def discover_grace_gpus(*, expected: Iterable[ExpectedGPU] = GRACE_EXPECTED_GPUS, host_id: str | None = None, now: str | None = None) -> list[ComputeResourceObservation]:
    """Perform bounded read-only inventory across the existing local signals."""
    nvml = collect_nvidia_smi(host_id=host_id)
    return build_gpu_inventory(expected, nvml, windows_devices=collect_windows_display_devices(), runtime_devices=collect_pytorch_devices(), now=now)


def build_grace_gpu_preflight(*, expected: Iterable[ExpectedGPU] = GRACE_EXPECTED_GPUS, observations: Iterable[ComputeResourceObservation] | None = None, now: str | None = None) -> dict[str, Any]:
    """Return fail-closed dual-GPU admission evidence before workload dispatch."""
    expected_list = list(expected)
    inventory = list(observations) if observations is not None else discover_grace_gpus(expected=expected_list, now=now)
    safe = len(inventory) == len(expected_list) and all(item.dispatch_allowed for item in inventory)
    return {
        "schema_version": "dual_gpu_preflight.v1",
        "generated_at": utc_now(),
        "expected_gpu_count": len(expected_list),
        "observed_gpu_count": len(inventory),
        "dual_gpu_dispatch_safe": safe,
        "dispatch_policy": "require every expected physical GPU; no ordinal fallback; no CPU fallback; no recovery actions",
        "resources": [item.to_dict() for item in inventory],
        "overall_health": "HEALTHY" if safe else "UNSAFE_TO_DISPATCH",
    }


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
        if device.health_state != "HEALTHY":
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
    query = "index,uuid,name,pci.bus_id,driver_version,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw,compute_mode"
    try:
        result = runner(["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5, check=False)
        if getattr(result, "returncode", 1) != 0:
            return []
        rows = csv.reader(io.StringIO(getattr(result, "stdout", "")))
        host = host_id or platform.node() or "unknown-host"
        devices = []
        for row in rows:
            if len(row) < 12:
                continue
            try:
                smi_index = int(row[0].strip())
            except ValueError:
                continue
            uuid = row[1].strip()
            name = row[2].strip()
            if not uuid or not name:
                continue
            devices.append(classify_observation(ComputeResourceObservation(resource_id=canonical_resource_id(host, uuid), host_id=host, nvidia_uuid=uuid, name=name, pci_bus_id=row[3].strip() or None, nvidia_smi_index=smi_index, driver_version=row[4].strip() or None, memory_total_mib=_num(row[5]), memory_used_mib=_num(row[6]), memory_free_mib=_num(row[7]), utilization_percent=_num(row[8]), temperature_c=_num(row[9]), power_draw_w=_num(row[10]), compute_mode=row[11].strip() or None, evidence_sources=["nvidia-smi"])))
        return devices
    except (OSError, subprocess.SubprocessError, ValueError):
        return []


def collect_pytorch_devices() -> list[dict[str, Any]]:
    """Read-only CUDA/PyTorch enumeration; no allocation or kernel is run."""
    try:
        import torch
        if not torch.cuda.is_available():
            return []
        devices = []
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            devices.append({"ordinal": i, "name": torch.cuda.get_device_name(i), "cuda_present": True, "compute_capability": f"{props.major}.{props.minor}", "memory_total_mib": round(props.total_memory / 1024**2, 2)})
        return devices
    except Exception:
        return []


def collect_windows_display_devices(*, runner=subprocess.run) -> list[dict[str, Any]]:
    """Read-only Windows PnP display evidence, kept injectable for fixtures."""
    command = "Get-PnpDevice -Class Display | Where-Object {$_.FriendlyName -match 'NVIDIA|Tesla|GeForce'} | Select-Object FriendlyName,Status,ProblemCode | ConvertTo-Json -Compress"
    try:
        result = runner(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True, timeout=5, check=False)
        if getattr(result, "returncode", 1) != 0 or not getattr(result, "stdout", "").strip():
            return []
        data = json.loads(result.stdout)
        rows = data if isinstance(data, list) else [data]
        return [{"name": row.get("FriendlyName", ""), "status": row.get("Status"), "problem_code": row.get("ProblemCode"), "present": row.get("Status") == "OK"} for row in rows if isinstance(row, dict)]
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
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
