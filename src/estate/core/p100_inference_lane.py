"""Governed, single-lane llama.cpp placement for the Grace P100.

This module is deliberately narrower than the compute foundation: it binds one
known model service to the P100 physical UUID, derives the current runtime
ordinal from that observation, and fails closed.  It never chooses a sibling
GPU, resets hardware, or retries a lost lane.
"""
from __future__ import annotations

import json
import os
import struct
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


def _gguf_metadata(path: Path) -> dict[str, Any]:
    """Read GGUF metadata without requiring an optional third-party package."""
    def read_string(handle: Any) -> str:
        length = struct.unpack("<Q", handle.read(8))[0]
        return handle.read(length).decode("utf-8", "replace")

    scalar_sizes = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4, 7: 1, 10: 8, 11: 8, 12: 8}

    def skip_value(handle: Any, value_type: int) -> Any:
        if value_type == 8:
            return read_string(handle)
        if value_type == 9:
            element_type = struct.unpack("<I", handle.read(4))[0]
            length = struct.unpack("<Q", handle.read(8))[0]
            for _ in range(length):
                skip_value(handle, element_type)
            return None
        if value_type not in scalar_sizes:
            raise ValueError(f"unsupported GGUF metadata type: {value_type}")
        raw = handle.read(scalar_sizes[value_type])
        if value_type == 7:
            return bool(raw[0])
        formats = {0: "B", 1: "b", 2: "H", 3: "h", 4: "I", 5: "i", 6: "f", 10: "Q", 11: "q", 12: "d"}
        return struct.unpack("<" + formats[value_type], raw)[0]

    with path.open("rb") as handle:
        if handle.read(4) != b"GGUF":
            raise ValueError(f"not a GGUF file: {path}")
        handle.read(4)  # GGUF version
        handle.read(8)  # tensor count
        metadata_count = struct.unpack("<Q", handle.read(8))[0]
        metadata: dict[str, Any] = {}
        wanted = {
            "general.architecture", "general.type", "general.name", "general.basename",
            "general.size_label", "general.base_model.0.name", "general.base_model.0.repo_url",
            "clip.projector_type", "clip.vision.projection_dim", "clip.vision.block_count",
            "clip.has_vision_encoder", "qwen3vl.embedding_length", "qwen3vl.block_count",
            "qwen3vl.n_deepstack_layers",
        }
        for _ in range(metadata_count):
            key = read_string(handle)
            value_type = struct.unpack("<I", handle.read(4))[0]
            value = skip_value(handle, value_type)
            if key in wanted:
                metadata[key] = value
    return metadata


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
    multimodal_enabled: bool = False
    mmproj: Path | None = None
    mmproj_offload: bool = False

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
            multimodal_enabled=bool((raw.get("multimodal", {}) or {}).get("enabled", False)),
            mmproj=Path((raw.get("multimodal", {}) or {}).get("mmproj_path")) if (raw.get("multimodal", {}) or {}).get("mmproj_path") else None,
            mmproj_offload=bool((raw.get("multimodal", {}) or {}).get("mmproj_offload", False)),
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
    compatibility: dict[str, Any] = {"enabled": config.multimodal_enabled}
    if config.multimodal_enabled:
        if config.mmproj is None:
            errors.append("multimodal is enabled but mmproj_path is missing")
        elif not config.mmproj.is_file():
            errors.append(f"multimodal projector file is missing: {config.mmproj}")
        else:
            try:
                model_meta = _gguf_metadata(config.model)
                projector_meta = _gguf_metadata(config.mmproj)
                compatibility = {"enabled": True, "model": model_meta, "projector": projector_meta}
                if model_meta.get("general.architecture") != "qwen3vl":
                    errors.append("multimodal model architecture must be qwen3vl")
                if projector_meta.get("general.type") != "mmproj":
                    errors.append("projector GGUF general.type must be mmproj")
                if projector_meta.get("clip.projector_type") != "qwen3vl_merger":
                    errors.append("projector must use qwen3vl_merger")
                if projector_meta.get("clip.vision.projection_dim") != model_meta.get("qwen3vl.embedding_length"):
                    errors.append("projector projection dimension does not match model embedding length")
                if "32b" not in str(projector_meta.get("general.name", "")).lower() and "32b" not in str(projector_meta.get("general.base_model.0.name", "")).lower():
                    errors.append("projector metadata does not identify the Qwen3-VL 32B family")
            except (OSError, ValueError, struct.error) as exc:
                errors.append(f"multimodal GGUF metadata validation failed: {exc}")
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
        "configuration": {"gpu_layers": config.gpu_layers, "context": config.context, "host": config.host, "port": config.port, "multimodal_enabled": config.multimodal_enabled, "mmproj": str(config.mmproj) if config.mmproj else None, "mmproj_offload": config.mmproj_offload},
        "multimodal_compatibility": compatibility,
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
    if config.multimodal_enabled:
        args.extend(["--mmproj", str(config.mmproj)])
        if not config.mmproj_offload:
            args.append("--no-mmproj-offload")
    return {"argv": args, "environment": env, "resolved_target": result["target"], "endpoint": f"http://{config.host}:{config.port}"}


def health_gate_for_new_work(observation: ComputeResourceObservation) -> dict[str, Any]:
    allowed = observation.nvidia_uuid == P100_UUID and observation.name == P100_NAME and observation.dispatch_allowed and observation.health_state == "HEALTHY"
    return {"accept_new_work": allowed, "status": "HEALTHY" if allowed else "DEGRADED/LOST", "reason": "P100 identity and dispatch health are current" if allowed else "P100 health/identity gate failed; stop accepting new work"}
