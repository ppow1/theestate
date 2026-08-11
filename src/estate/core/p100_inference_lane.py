"""Governed, single-lane llama.cpp placement for the Grace P100.

This module is deliberately narrower than the compute foundation: it binds one
known model service to the P100 physical UUID, derives the current runtime
ordinal from that observation, and fails closed.  It never chooses a sibling
GPU, resets hardware, or retries a lost lane.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from estate.core.compute_resources import (
    ComputeResourceObservation,
    ComputeResourceRequirements,
    build_grace_gpu_preflight,
    canonical_resource_id,
    discover_grace_gpus,
    select_resource,
)

P100_UUID = "GPU-6785b322-899d-8eec-e817-31d83279a414"
P100_NAME = "Tesla P100-PCIE-16GB"
DEFAULT_MODEL = Path(r"A:\AI\Models\GGUF\qwen3-32b-vl-instruct-polaris-hi16-heretic-uncensored-q5_k_m.gguf")
DEFAULT_BACKEND = Path(r"A:\AI\Tools\llama.cpp\cuda\llama-server.exe")


@dataclass(frozen=True)
class P100LaneConfig:
    model: Path = DEFAULT_MODEL
    backend: Path = DEFAULT_BACKEND
    host: str = "127.0.0.1"
    port: int = 18080
    context: int = 4096
    gpu_layers: int = 42
    extra_args: tuple[str, ...] = ()
    environment: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "P100LaneConfig":
        return cls(
            model=Path(raw.get("model", DEFAULT_MODEL)),
            backend=Path(raw.get("backend", DEFAULT_BACKEND)),
            host=str(raw.get("host", "127.0.0.1")),
            port=int(raw.get("port", 18080)),
            context=int(raw.get("context", 4096)),
            gpu_layers=int(raw.get("gpu_layers", 42)),
            extra_args=tuple(str(x) for x in raw.get("extra_args", []) or []),
            environment={str(k): str(v) for k, v in (raw.get("environment", {}) or {}).items()},
        )


def load_config(path: str | Path) -> P100LaneConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("P100 lane configuration must be a JSON object")
    return P100LaneConfig.from_dict(raw)


def _p100_resource(observations: Iterable[ComputeResourceObservation]) -> ComputeResourceObservation:
    rows = list(observations)
    target = next((row for row in rows if row.nvidia_uuid == P100_UUID), None)
    if target is None:
        raise RuntimeError("P100 target identity is not present; lane remains stopped")
    if target.name != P100_NAME:
        raise RuntimeError(f"P100 identity mismatch: expected {P100_NAME}, observed {target.name}")
    if not target.dispatch_allowed:
        raise RuntimeError(f"P100 is not dispatch eligible: {target.dispatch_reason}")
    if target.cuda_index is None and len(target.runtime_ordinals) == 1:
        # Hand-built/test observations may carry the normalized ordinal list
        # without the convenience field populated by runtime reconciliation.
        target.cuda_index = target.runtime_ordinals[0]
    if target.cuda_index is None or len(target.runtime_ordinals) != 1:
        raise RuntimeError("P100 CUDA/PyTorch runtime ordinal is not uniquely established")
    required = canonical_resource_id(target.host_id, P100_UUID)
    placement = select_resource(rows, ComputeResourceRequirements(requires_gpu=True, required_resource_id=required))
    if not placement["eligible"] or placement["selected"] != required:
        raise RuntimeError(f"P100 is not dispatch eligible: {placement['reason']}")
    if any(row.nvidia_uuid != P100_UUID and row.cuda_index == target.cuda_index for row in rows):
        raise RuntimeError("P100 runtime ordinal is ambiguous with another physical GPU")
    return target


def preflight_lane(config: P100LaneConfig, observations: Iterable[ComputeResourceObservation] | None = None) -> dict[str, Any]:
    rows = list(observations) if observations is not None else discover_grace_gpus()
    errors: list[str] = []
    try:
        target = _p100_resource(rows)
    except RuntimeError as exc:
        target = None
        errors.append(str(exc))
    if not config.model.is_file():
        errors.append(f"model file is missing: {config.model}")
    if not config.backend.is_file():
        errors.append(f"llama-server executable is missing: {config.backend}")
    return {
        "ready": not errors,
        "errors": errors,
        "backend": str(config.backend),
        "model": str(config.model),
        "target": {
            "physical_uuid": P100_UUID,
            "physical_name": P100_NAME,
            "nvidia_smi_index": target.nvidia_smi_index if target else None,
            "runtime_ordinal": target.cuda_index if target else None,
            "dispatch_allowed": bool(target and target.dispatch_allowed),
        },
        "configuration": {"gpu_layers": config.gpu_layers, "context": config.context, "host": config.host, "port": config.port},
        "compute_preflight": build_grace_gpu_preflight(observations=rows),
        "no_fallback": True,
    }


def build_launch_plan(config: P100LaneConfig, observations: Iterable[ComputeResourceObservation]) -> dict[str, Any]:
    result = preflight_lane(config, observations)
    if not result["ready"]:
        raise RuntimeError("P100 lane preflight failed: " + "; ".join(result["errors"]))
    ordinal = result["target"]["runtime_ordinal"]
    # Restrict visibility before llama.cpp starts.  Inside the child, the
    # resolved physical P100 becomes CUDA0; this prevents sibling fallback.
    env = dict(os.environ)
    env.update(config.environment)
    env["CUDA_VISIBLE_DEVICES"] = str(ordinal)
    args = [
        str(config.backend), "--model", str(config.model), "--host", config.host,
        "--port", str(config.port), "--ctx-size", str(config.context),
        "--gpu-layers", str(config.gpu_layers), "--device", "CUDA0",
        *config.extra_args,
    ]
    return {"argv": args, "environment": env, "resolved_target": result["target"], "endpoint": f"http://{config.host}:{config.port}"}


def health_gate_for_new_work(observation: ComputeResourceObservation) -> dict[str, Any]:
    allowed = observation.nvidia_uuid == P100_UUID and observation.name == P100_NAME and observation.dispatch_allowed and observation.health_state == "HEALTHY"
    return {"accept_new_work": allowed, "status": "HEALTHY" if allowed else "DEGRADED/LOST", "reason": "P100 identity and dispatch health are current" if allowed else "P100 health/identity gate failed; stop accepting new work"}
