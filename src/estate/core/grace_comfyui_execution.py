"""Bounded live ComfyUI execution for the Grace local image lane."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from estate.core.comfyui_provider_health import DEFAULT_ENDPOINT


def _endpoint_base(endpoint: str) -> str:
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("ComfyUI execution endpoint must be loopback-only HTTP")
    return endpoint.rstrip("/")


def _request(base: str, path: str, *, method: str = "GET", payload: dict[str, Any] | None = None, timeout: float = 10.0) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(base + path, data=data, method=method, headers={"Accept": "application/json", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 - base is validated loopback-only
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"ComfyUI request failed: {type(exc).__name__}") from exc


def build_sdxl_workflow(prompt: str, *, checkpoint: str, seed: int, filename_prefix: str) -> dict[str, Any]:
    """Build the smallest canonical SDXL text-to-image API workflow."""
    if not prompt.strip() or not checkpoint.strip():
        raise ValueError("prompt and checkpoint are required")
    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": checkpoint}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry, low quality, distorted, watermark, text, duplicate person", "clip": ["4", 1]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 768, "height": 1024, "batch_size": 1}},
        "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 28, "cfg": 6.5, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": filename_prefix, "images": ["8", 0]}},
    }


def execute_comfyui_image(task: dict[str, Any], *, root: Path, endpoint: str = DEFAULT_ENDPOINT, timeout_seconds: float = 900.0) -> dict[str, Any]:
    """Submit one workflow, wait for completion, and persist a local artifact copy."""
    base = _endpoint_base(endpoint)
    workflow = task.get("workflow")
    if not isinstance(workflow, dict) or not workflow:
        raise ValueError("ComfyUI workflow is required")
    client_id = str(task.get("client_id") or "estate-grace-runtime")
    submitted = _request(base, "/prompt", method="POST", payload={"prompt": workflow, "client_id": client_id}, timeout=15)
    prompt_id = submitted.get("prompt_id")
    if not isinstance(prompt_id, str) or not prompt_id:
        raise RuntimeError("ComfyUI did not return a prompt_id")
    deadline = time.monotonic() + timeout_seconds
    history: dict[str, Any] = {}
    while time.monotonic() < deadline:
        history = _request(base, "/history/" + urllib.parse.quote(prompt_id, safe=""), timeout=15)
        item = history.get(prompt_id) if isinstance(history, dict) else None
        if isinstance(item, dict) and item.get("status", {}).get("completed") is True:
            outputs = item.get("outputs") or {}
            images = [image for node in outputs.values() if isinstance(node, dict) for image in node.get("images", []) if isinstance(image, dict)]
            if not images:
                raise RuntimeError("ComfyUI completed without an image output")
            image = images[0]
            filename, subfolder, image_type = image.get("filename"), image.get("subfolder", ""), image.get("type", "output")
            if not isinstance(filename, str) or not filename:
                raise RuntimeError("ComfyUI image output has no filename")
            query = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": image_type})
            request = urllib.request.Request(base + "/view?" + query, method="GET")
            try:
                with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310 - base is validated loopback-only
                    content = response.read()
            except (urllib.error.URLError, TimeoutError) as exc:
                raise RuntimeError("ComfyUI image artifact download failed") from exc
            artifact_id = f"grace-{prompt_id}-{Path(filename).name}"
            artifact_path = root / "runtime" / "production" / "grace_momentum" / "artifacts" / artifact_id
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_bytes(content)
            return {"prompt_id": prompt_id, "artifact_id": artifact_id, "artifact_path": str(artifact_path), "artifact_bytes": len(content), "image_filename": filename, "image_subfolder": subfolder, "image_type": image_type, "provider_endpoint": base, "workflow_submitted": True, "image_generated": True, "live_provider_called": True}
        if isinstance(item, dict) and item.get("status", {}).get("status_str") == "error":
            raise RuntimeError("ComfyUI reported workflow execution failure")
        time.sleep(1.0)
    raise RuntimeError("ComfyUI execution timed out")
