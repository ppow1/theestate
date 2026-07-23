"""Evelyn v1 local ComfyUI turnaround and T-pose pipeline.

The module is intentionally conservative: immutable source images are verified,
normalized derivatives are created in the versioned Evelyn workspace, every
generation is candidate-only, and runtime capability checks decide which
profiles may run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import yaml

from estate.core.paths import ESTATE_ROOT

SCHEMA_VERSION = "evelyn_turnaround_pipeline.v1"
PROFILE_SCHEMA_VERSION = "evelyn_generation_profiles.v1"
SOURCE_ANGLES = ("front", "left", "rear")
TURNAROUND_ANGLES = (
    "front",
    "front_left_45",
    "left_profile",
    "rear_left_45",
    "rear",
    "rear_right_45",
    "right_profile",
    "front_right_45",
)
SOURCE_FILES = {
    "front": "Evelyn_Front_V1_Candidate.png",
    "left": "Evelyn_Left_V1_Candidate.png",
    "rear": "Evelyn_Rear_V1_Candidate.png",
}
DEFAULT_PROFILE_PATH = Path("config/visual_generation/evelyn_generation_profiles.yaml")
DEFAULT_ENDPOINT = "http://127.0.0.1:8188"
GRAY_RGB = (128, 128, 128)


def root_path(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def now_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_prefixed(path: Path) -> str:
    return "sha256:" + sha256_file(path)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not parse to a mapping")
    return data


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_profile_registry(root: Path, profile_path: Path | None = None) -> dict[str, Any]:
    path = root / (profile_path or DEFAULT_PROFILE_PATH)
    registry = read_yaml(path)
    if registry.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise ValueError(f"Unsupported profile registry schema: {registry.get('schema_version')}")
    return registry


def source_manifest_path(root: Path, registry: dict[str, Any]) -> Path:
    source = registry["source_set"]
    return root / source["root"] / source["manifest"]


def source_root(root: Path, registry: dict[str, Any]) -> Path:
    return root / registry["source_set"]["root"]


def verify_source_set(root: Path, registry: dict[str, Any]) -> dict[str, Any]:
    manifest_path = source_manifest_path(root, registry)
    manifest = read_yaml(manifest_path)
    diagnostics: list[dict[str, str]] = []
    sources: dict[str, Any] = {}
    if manifest.get("resident") != "evelyn":
        diagnostics.append({"code": "EVELYN-SOURCE-RESIDENT", "severity": "error", "message": "Manifest resident is not evelyn."})
    policy = manifest.get("source_policy") or {}
    if policy.get("immutable_originals") is not True or policy.get("modify_in_place") is not False:
        diagnostics.append({"code": "EVELYN-SOURCE-POLICY", "severity": "error", "message": "Manifest does not declare immutable no-edit sources."})
    images = manifest.get("images") if isinstance(manifest.get("images"), dict) else {}
    for angle in SOURCE_ANGLES:
        record = images.get(angle) if isinstance(images.get(angle), dict) else {}
        expected_file = SOURCE_FILES[angle]
        if record.get("file") != expected_file:
            diagnostics.append({"code": "EVELYN-SOURCE-FILE", "severity": "error", "message": f"{angle} source file mismatch."})
            continue
        path = manifest_path.parent / expected_file
        if not path.is_file():
            diagnostics.append({"code": "EVELYN-SOURCE-MISSING", "severity": "error", "message": f"Missing source image {expected_file}."})
            continue
        actual = sha256_file(path).upper()
        expected = str(record.get("sha256", "")).upper()
        if actual != expected:
            diagnostics.append({"code": "EVELYN-SOURCE-HASH", "severity": "error", "message": f"{angle} SHA-256 mismatch."})
        sources[angle] = {
            "path": str(path.relative_to(root)),
            "sha256": actual,
            "bytes": path.stat().st_size,
        }
    return {
        "schema_version": "evelyn_source_verification.v1",
        "status": "fail" if diagnostics else "pass",
        "manifest": str(manifest_path.relative_to(root)),
        "manifest_sha256": sha256_file(manifest_path).upper(),
        "sources": sources,
        "diagnostics": diagnostics,
    }


def normalize_source_set(root: Path, registry: dict[str, Any]) -> dict[str, Any]:
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - environment guard
        raise RuntimeError("Pillow is required for Evelyn source normalization.") from exc
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - environment guard
        raise RuntimeError("NumPy is required for Evelyn source normalization.") from exc

    verification = verify_source_set(root, registry)
    if verification["status"] != "pass":
        raise ValueError("Source verification failed; refusing normalization.")
    output_root = root / registry["normalized_output_root"]
    output_root.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Any] = {}
    for angle, source in verification["sources"].items():
        src = root / source["path"]
        image = Image.open(src).convert("RGB")
        arr = np.asarray(image).astype("int16")
        h, w = arr.shape[:2]
        corner = max(12, min(w, h) // 20)
        samples = np.concatenate(
            [
                arr[:corner, :corner].reshape(-1, 3),
                arr[:corner, -corner:].reshape(-1, 3),
                arr[-corner:, :corner].reshape(-1, 3),
                arr[-corner:, -corner:].reshape(-1, 3),
            ],
            axis=0,
        )
        bg = np.median(samples, axis=0)
        distance = np.sqrt(((arr - bg) ** 2).sum(axis=2))
        mask = distance > 34
        mask = _largest_foreground_component(mask)
        ys, xs = np.where(mask)
        if len(xs) == 0 or len(ys) == 0:
            bbox = (0, 0, w, h)
        else:
            bbox = (max(0, xs.min() - 8), max(0, ys.min() - 8), min(w, xs.max() + 9), min(h, ys.max() + 9))
        alpha = Image.fromarray((mask.astype("uint8") * 255), mode="L")
        subject = Image.new("RGBA", image.size, (0, 0, 0, 0))
        subject.paste(image.convert("RGBA"), (0, 0), alpha)
        cropped = subject.crop(bbox)
        target_h = int(h * 0.92)
        scale = target_h / max(1, cropped.height)
        target_w = max(1, min(int(cropped.width * scale), int(w * 0.92)))
        target_h = max(1, min(int(cropped.height * scale), int(h * 0.92)))
        resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", image.size, GRAY_RGB + (255,))
        x = (w - target_w) // 2
        y = h - target_h - int(h * 0.035)
        canvas.alpha_composite(resized, (x, max(0, y)))
        _scrub_source_ui_regions(canvas, angle)
        out = output_root / f"evelyn_v1_{angle}_normalized_gray.png"
        canvas.convert("RGB").save(out)
        outputs[angle] = {
            "source": source,
            "path": str(out.relative_to(root)),
            "sha256": sha256_prefixed(out),
            "background_rgb": list(GRAY_RGB),
            "bbox": list(map(int, bbox)),
        }
    manifest = {
        "schema_version": "evelyn_normalized_source_manifest.v1",
        "resident_id": "evelyn",
        "canonical": False,
        "source_verification": verification,
        "outputs": outputs,
        "policy": {
            "source_images_modified": False,
            "background_rgb": list(GRAY_RGB),
            "derived_candidate_inputs": True,
        },
    }
    manifest_path = output_root / "normalized_source_manifest.json"
    write_json(manifest_path, manifest)
    manifest["manifest_path"] = str(manifest_path.relative_to(root))
    return manifest


def _scrub_source_ui_regions(canvas: Any, angle: str) -> None:
    """Clear known source-capture guide marks from non-anatomy corner zones."""
    from PIL import ImageDraw

    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    boxes = [
        (0, 0, int(w * 0.23), int(h * 0.20)),
        (int(w * 0.78), 0, w, int(h * 0.21)),
        (0, int(h * 0.84), int(w * 0.24), h),
        (int(w * 0.78), int(h * 0.82), w, h),
    ]
    if angle == "front":
        boxes.append((int(w * 0.74), 0, w, int(h * 0.16)))
    for box in boxes:
        draw.rectangle(box, fill=GRAY_RGB + (255,))


def _largest_foreground_component(mask: Any) -> Any:
    """Remove disconnected UI marks while keeping the main body component."""
    try:
        import numpy as np
        from scipy import ndimage
    except ImportError:  # pragma: no cover - normalization already requires numpy
        return mask
    labels, count = ndimage.label(mask)
    if count <= 1:
        return mask
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    h, w = mask.shape
    central = labels[int(h * 0.05):int(h * 0.98), int(w * 0.25):int(w * 0.75)]
    central_counts = np.bincount(central.ravel(), minlength=len(sizes))
    central_counts[0] = 0
    scores = central_counts.astype("int64") * 1000 + sizes.astype("int64")
    selected = int(scores.argmax())
    if selected == 0 or central_counts[selected] < 100:
        selected = int(sizes.argmax())
    if selected == 0 or sizes[selected] < 100:
        return mask
    return labels == selected


def create_front_tpose_pose_asset(root: Path, registry: dict[str, Any]) -> dict[str, Any]:
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Pillow is required for pose asset creation.") from exc
    defaults = registry["common_generation"]
    w, h = int(defaults["width"]), int(defaults["height"])
    out_root = root / registry["pose_asset_root"]
    out_root.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    c = w // 2
    pts = {
        "nose": (c, int(h * 0.125)),
        "neck": (c, int(h * 0.205)),
        "r_shoulder": (int(w * 0.31), int(h * 0.23)),
        "r_elbow": (int(w * 0.18), int(h * 0.23)),
        "r_wrist": (int(w * 0.07), int(h * 0.23)),
        "l_shoulder": (int(w * 0.69), int(h * 0.23)),
        "l_elbow": (int(w * 0.82), int(h * 0.23)),
        "l_wrist": (int(w * 0.93), int(h * 0.23)),
        "r_hip": (int(w * 0.42), int(h * 0.50)),
        "l_hip": (int(w * 0.58), int(h * 0.50)),
        "r_knee": (int(w * 0.40), int(h * 0.72)),
        "l_knee": (int(w * 0.60), int(h * 0.72)),
        "r_ankle": (int(w * 0.38), int(h * 0.94)),
        "l_ankle": (int(w * 0.62), int(h * 0.94)),
    }
    bones = [
        ("nose", "neck"),
        ("neck", "r_shoulder"),
        ("r_shoulder", "r_elbow"),
        ("r_elbow", "r_wrist"),
        ("neck", "l_shoulder"),
        ("l_shoulder", "l_elbow"),
        ("l_elbow", "l_wrist"),
        ("neck", "r_hip"),
        ("neck", "l_hip"),
        ("r_hip", "l_hip"),
        ("r_hip", "r_knee"),
        ("r_knee", "r_ankle"),
        ("l_hip", "l_knee"),
        ("l_knee", "l_ankle"),
    ]
    colors = [(255, 0, 0), (255, 128, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 128, 255), (128, 0, 255)]
    for idx, (a, b) in enumerate(bones):
        draw.line([pts[a], pts[b]], fill=colors[idx % len(colors)], width=9)
    for idx, point in enumerate(pts.values()):
        x, y = point
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=colors[idx % len(colors)])
    png = out_root / "evelyn_true_tpose_front_openpose_v1.png"
    image.save(png)
    spec = {
        "schema_version": "evelyn_pose_control.v1",
        "pose_id": "evelyn_true_tpose_front_openpose_v1",
        "canonical": False,
        "description": "Derived 2D front T-pose OpenPose-style control image for candidate generation only.",
        "image": str(png.relative_to(root)),
        "sha256": sha256_prefixed(png),
        "canvas": {"width": w, "height": h},
        "points": {k: list(v) for k, v in pts.items()},
        "constraints": ["front view", "arms horizontal", "feet visible", "head-to-toe framing"],
    }
    spec_path = out_root / "evelyn_true_tpose_front_openpose_v1.json"
    write_json(spec_path, spec)
    spec["spec_path"] = str(spec_path.relative_to(root))
    return spec


def create_front_tpose_silhouette_asset(root: Path, registry: dict[str, Any]) -> dict[str, Any]:
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Pillow is required for pose asset creation.") from exc
    defaults = registry["common_generation"]
    w, h = int(defaults["width"]), int(defaults["height"])
    out_root = root / registry["pose_asset_root"]
    out_root.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    c = w // 2
    fill = (235, 235, 235)
    draw.ellipse((c - 43, int(h * 0.07), c + 43, int(h * 0.17)), fill=fill)
    draw.rounded_rectangle((c - 54, int(h * 0.18), c + 54, int(h * 0.53)), radius=40, fill=fill)
    draw.rounded_rectangle((int(w * 0.07), int(h * 0.215), int(w * 0.93), int(h * 0.255)), radius=18, fill=fill)
    draw.polygon([(c - 48, int(h * 0.51)), (c - 16, int(h * 0.51)), (c - 45, int(h * 0.94)), (c - 78, int(h * 0.94))], fill=fill)
    draw.polygon([(c + 16, int(h * 0.51)), (c + 48, int(h * 0.51)), (c + 78, int(h * 0.94)), (c + 45, int(h * 0.94))], fill=fill)
    png = out_root / "evelyn_true_tpose_front_silhouette_v1.png"
    image.save(png)
    spec = {
        "schema_version": "evelyn_pose_control.v1",
        "pose_id": "evelyn_true_tpose_front_silhouette_v1",
        "canonical": False,
        "description": "Derived 2D front T-pose silhouette control image for candidate generation only.",
        "image": str(png.relative_to(root)),
        "sha256": sha256_prefixed(png),
        "canvas": {"width": w, "height": h},
        "constraints": ["front view", "arms horizontal", "feet visible", "head-to-toe framing", "non-OpenPose fallback control"],
    }
    spec_path = out_root / "evelyn_true_tpose_front_silhouette_v1.json"
    write_json(spec_path, spec)
    spec["spec_path"] = str(spec_path.relative_to(root))
    return spec


def _json_url(endpoint: str, path: str, timeout: int = 20) -> Any:
    with urllib.request.urlopen(endpoint.rstrip("/") + path, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def comfy_inventory(endpoint: str = DEFAULT_ENDPOINT) -> dict[str, Any]:
    object_info = _json_url(endpoint, "/object_info")
    system_stats = _json_url(endpoint, "/system_stats")

    def choices(node: str, input_name: str) -> list[str]:
        spec = object_info.get(node, {}).get("input", {}).get("required", {}).get(input_name)
        if isinstance(spec, list) and spec and isinstance(spec[0], list):
            return [str(item) for item in spec[0]]
        return []

    return {
        "schema_version": "comfyui_inventory.v1",
        "endpoint": endpoint,
        "system_stats": system_stats,
        "nodes": sorted(object_info.keys()),
        "checkpoints": choices("CheckpointLoaderSimple", "ckpt_name"),
        "controlnets": choices("ControlNetLoader", "control_net_name"),
        "ipadapter_files": choices("IPAdapterModelLoader", "ipadapter_file"),
        "clip_vision": choices("CLIPVisionLoader", "clip_name"),
    }


def validate_profiles(registry: dict[str, Any], inventory: dict[str, Any]) -> dict[str, Any]:
    nodes = set(inventory.get("nodes", []))
    checkpoints = set(inventory.get("checkpoints", []))
    controlnets = set(inventory.get("controlnets", []))
    ipadapter = set(inventory.get("ipadapter_files", []))
    clip_vision = set(inventory.get("clip_vision", []))
    results = []
    for profile in registry.get("profiles", []):
        missing: list[str] = []
        for node in profile.get("required_nodes", []):
            if node not in nodes:
                missing.append(f"node:{node}")
        required = profile.get("required_models") or {}
        for name in required.get("checkpoint", []):
            if name not in checkpoints:
                missing.append(f"checkpoint:{name}")
        for name in required.get("controlnet", []):
            if name not in controlnets:
                missing.append(f"controlnet:{name}")
        for name in required.get("ipadapter", []):
            if name not in ipadapter:
                missing.append(f"ipadapter:{name}")
        for name in required.get("clip_vision", []):
            if not any(name in candidate for candidate in clip_vision):
                missing.append(f"clip_vision:{name}")
        disabled_reason = profile.get("disabled_reason") if not profile.get("enabled", False) else None
        compatible = bool(profile.get("enabled", False)) and not missing
        results.append(
            {
                "id": profile.get("id"),
                "label": profile.get("label"),
                "enabled": bool(profile.get("enabled", False)),
                "compatible": compatible,
                "workflow": profile.get("workflow"),
                "checkpoint": profile.get("checkpoint"),
                "missing": missing,
                "disabled_reason": disabled_reason,
            }
        )
    return {
        "schema_version": "evelyn_profile_validation.v1",
        "status": "pass" if all(item["compatible"] or not item["enabled"] for item in results) else "fail",
        "profiles": results,
    }


def tpose_positive_prompt(angle: str) -> str:
    angle_text = angle.replace("_", " ")
    return "\n".join(
        [
            "full-body professional studio character reference photograph of Evelyn",
            "one unambiguously adult woman, adult age presentation",
            "extremely petite 4 feet 10 inch adult frame, compact proportions",
            "small delicate bone structure, subtle hourglass silhouette",
            "warm hazel eyes, soft brunette hair with natural movement",
            "tasteful neutral one-piece swimsuit, barefoot, no accessories",
            "true T-pose, both arms extended horizontally in a straight line",
            "standing upright, legs straight, feet visible, head-to-toe framing",
            "hands and fingertips fully visible inside the frame with clear side margins",
            f"{angle_text} view, neutral gray studio background",
            "camera at body-center height, 50 mm reference lens intent",
            "photorealistic skin texture, natural anatomy, identity reference candidate",
            "candidate review artifact only, not canonical and not approved",
        ]
    )


def negative_prompt() -> str:
    return "\n".join(
        [
            "child, teenager, minor, underage, juvenile",
            "average height, tall woman, long legs, elongated torso, runway proportions",
            "sexualized pose, provocative pose, lingerie, transparent fabric",
            "arms down, arms bent, asymmetric arms, cropped arms, cropped hands, cropped fingertips, cropped feet, cropped head",
            "skeleton, bones, stick figure, wireframe, pose rig, mannequin, puppet",
            "multiple people, duplicate body, extra limbs, missing limbs",
            "extra fingers, missing fingers, deformed anatomy, distorted face",
            "cartoon, anime, illustration, painting, text, caption, watermark, logo",
        ]
    )


def build_sdxl_openpose_workflow(
    profile: dict[str, Any],
    registry: dict[str, Any],
    *,
    angle: str,
    seed: int,
    filename_prefix: str,
    pose_image_name: str,
) -> dict[str, Any]:
    defaults = registry["common_generation"]
    controlnet = profile["required_models"]["controlnet"][0]
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": int(defaults["steps"]),
                "cfg": float(defaults["cfg"]),
                "sampler_name": defaults["sampler_name"],
                "scheduler": defaults["scheduler"],
                "denoise": float(defaults["denoise"]),
                "model": ["4", 0],
                "positive": ["12", 0],
                "negative": ["12", 1],
                "latent_image": ["5", 0],
            },
        },
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": profile["checkpoint"]}},
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": int(defaults["width"]),
                "height": int(defaults["height"]),
                "batch_size": 1,
            },
        },
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": tpose_positive_prompt(angle), "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative_prompt(), "clip": ["4", 1]}},
        "10": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": controlnet}},
        "11": {"class_type": "LoadImage", "inputs": {"image": pose_image_name}},
        "12": {
            "class_type": "ControlNetApplyAdvanced",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "control_net": ["10", 0],
                "image": ["11", 0],
                "strength": float(defaults["controlnet_strength"]),
                "start_percent": float(defaults["controlnet_start_percent"]),
                "end_percent": float(defaults["controlnet_end_percent"]),
                "vae": ["4", 2],
            },
        },
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": filename_prefix, "images": ["8", 0]}},
    }


def upload_image(endpoint: str, image_path: Path, *, name: str | None = None) -> str:
    try:
        import requests
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("requests is required for ComfyUI image upload.") from exc
    upload_name = name or image_path.name
    with image_path.open("rb") as handle:
        response = requests.post(
            endpoint.rstrip("/") + "/upload/image",
            files={"image": (upload_name, handle, "image/png")},
            data={"overwrite": "true", "type": "input"},
            timeout=60,
        )
    response.raise_for_status()
    payload = response.json()
    return str(payload.get("name") or upload_name)


def submit_prompt(endpoint: str, workflow: dict[str, Any], *, client_id: str) -> str:
    data = json.dumps({"prompt": workflow, "client_id": client_id}).encode("utf-8")
    request = urllib.request.Request(endpoint.rstrip("/") + "/prompt", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return str(payload["prompt_id"])


def wait_for_history(endpoint: str, prompt_id: str, *, timeout_seconds: int = 900, poll_seconds: float = 2.5) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        history = _json_url(endpoint, "/history/" + urllib.parse.quote(prompt_id), timeout=60)
        if prompt_id in history:
            entry = history[prompt_id]
            status = entry.get("status") or {}
            if status.get("completed") is True or status.get("status_str") in {"success", "error"}:
                return entry
        time.sleep(poll_seconds)
    raise TimeoutError(f"Timed out waiting for ComfyUI prompt {prompt_id}")


def download_history_images(endpoint: str, history: dict[str, Any], destination: Path, root: Path) -> list[dict[str, Any]]:
    destination.mkdir(parents=True, exist_ok=True)
    outputs = []
    for node_output in (history.get("outputs") or {}).values():
        for image in node_output.get("images", []):
            params = urllib.parse.urlencode(
                {
                    "filename": image["filename"],
                    "subfolder": image.get("subfolder", ""),
                    "type": image.get("type", "output"),
                }
            )
            with urllib.request.urlopen(endpoint.rstrip("/") + "/view?" + params, timeout=120) as response:
                data = response.read()
            out = destination / image["filename"]
            out.write_bytes(data)
            outputs.append(
                {
                    "path": str(out.relative_to(root)),
                    "sha256": "sha256:" + sha256_bytes(data),
                    "comfyui": image,
                }
            )
    return outputs


def make_contact_sheet(root: Path, image_records: list[dict[str, Any]], output_path: Path) -> dict[str, Any]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Pillow is required for comparison sheets.") from exc
    thumb_w, thumb_h = 256, 384
    label_h = 54
    columns = max(1, min(4, len(image_records)))
    rows = (len(image_records) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + label_h)), (128, 128, 128))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for idx, record in enumerate(image_records):
        image = Image.open(root / record["path"]).convert("RGB")
        image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (idx % columns) * thumb_w + (thumb_w - image.width) // 2
        y = (idx // columns) * (thumb_h + label_h)
        sheet.paste(image, (x, y))
        label = f"{record.get('profile_id', 'unknown')}\nseed {record.get('seed', '')}"
        draw.multiline_text(((idx % columns) * thumb_w + 8, y + thumb_h + 4), label[:80], fill=(0, 0, 0), font=font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)
    return {"path": str(output_path.relative_to(root)), "sha256": sha256_prefixed(output_path), "count": len(image_records)}


def compatible_profiles_for_intent(registry: dict[str, Any], validation: dict[str, Any], intent: str) -> list[dict[str, Any]]:
    compatible = {item["id"] for item in validation["profiles"] if item["compatible"]}
    return [
        profile
        for profile in registry.get("profiles", [])
        if profile.get("id") in compatible and intent in set(profile.get("intents") or [])
    ]


def prepare_assets(root: Path, registry: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_source_set(root, registry)
    pose = create_front_tpose_pose_asset(root, registry)
    silhouette = create_front_tpose_silhouette_asset(root, registry)
    manifest = {
        "schema_version": "evelyn_pipeline_prepared_assets.v1",
        "resident_id": "evelyn",
        "canonical": False,
        "normalized_sources": normalized,
        "pose_controls": {"front_tpose_openpose": pose, "front_tpose_silhouette": silhouette},
    }
    output = root / registry["pose_asset_root"] / "prepared_assets_manifest.json"
    write_json(output, manifest)
    manifest["manifest_path"] = str(output.relative_to(root))
    return manifest


def run_bounded_front_tpose(root: Path, registry: dict[str, Any], *, endpoint: str, samples_per_profile: int | None = None) -> dict[str, Any]:
    verification = verify_source_set(root, registry)
    if verification["status"] != "pass":
        raise ValueError("Source verification failed; refusing generation.")
    prepared = prepare_assets(root, registry)
    inventory = comfy_inventory(endpoint)
    validation = validate_profiles(registry, inventory)
    profiles = compatible_profiles_for_intent(registry, validation, "true_t_pose_front")
    run_id = "evelyn_front_tpose_" + now_id()
    output_root = root / registry["derived_output_root"] / run_id
    workflows_root = output_root / "workflows"
    history_root = output_root / "history"
    images_root = output_root / "candidates"
    workflow_records = []
    image_records: list[dict[str, Any]] = []
    samples = int(samples_per_profile or registry["campaign_defaults"]["bounded_front_tpose_candidates_per_profile"])
    pose_path = root / prepared["pose_controls"]["front_tpose_silhouette"]["image"]
    pose_upload_name = upload_image(endpoint, pose_path, name="evelyn_true_tpose_front_silhouette_v1.png")
    for profile_index, profile in enumerate(profiles):
        for sample_index in range(samples):
            seed = int(registry["common_generation"]["seed_base"]) + profile_index * 1000 + sample_index
            prefix = f"EstateEvelyn/{run_id}/{profile['id']}/front_tpose_candidate_{sample_index + 1:03d}"
            workflow = build_sdxl_openpose_workflow(
                profile,
                registry,
                angle="front",
                seed=seed,
                filename_prefix=prefix,
                pose_image_name=pose_upload_name,
            )
            workflow_path = workflows_root / profile["id"] / f"front_tpose_candidate_{sample_index + 1:03d}.json"
            write_json(workflow_path, workflow)
            prompt_id = submit_prompt(endpoint, workflow, client_id=run_id)
            history = wait_for_history(endpoint, prompt_id)
            history_path = history_root / profile["id"] / f"{prompt_id}.json"
            write_json(history_path, history)
            if (history.get("status") or {}).get("status_str") == "error":
                workflow_records.append(
                    {
                        "profile_id": profile["id"],
                        "seed": seed,
                        "prompt_id": prompt_id,
                        "workflow": str(workflow_path.relative_to(root)),
                        "history": str(history_path.relative_to(root)),
                        "status": "error",
                    }
                )
                continue
            downloaded = download_history_images(endpoint, history, images_root / profile["id"], root)
            for record in downloaded:
                record.update({"profile_id": profile["id"], "label": profile["label"], "seed": seed, "angle": "front", "state": "candidate"})
                image_records.append(record)
            workflow_records.append(
                {
                    "profile_id": profile["id"],
                    "seed": seed,
                    "prompt_id": prompt_id,
                    "workflow": str(workflow_path.relative_to(root)),
                    "history": str(history_path.relative_to(root)),
                    "status": "generated" if downloaded else "no_output_images",
                    "outputs": downloaded,
                }
            )
    sheet = None
    if image_records:
        sheet = make_contact_sheet(root, image_records, output_root / "comparison" / "front_tpose_profile_comparison.png")
    manifest = {
        "schema_version": "evelyn_front_tpose_bounded_run.v1",
        "run_id": run_id,
        "resident_id": "evelyn",
        "canonical": False,
        "review_status": "pending_steward_review",
        "endpoint": endpoint,
        "source_verification": verification,
        "prepared_assets": prepared["manifest_path"],
        "profile_validation": validation,
        "profiles_attempted": [profile["id"] for profile in profiles],
        "samples_per_profile": samples,
        "workflow_records": workflow_records,
        "image_records": image_records,
        "comparison_sheet": sheet,
        "operator_pause": "Bounded front T-pose comparison complete; pause for Steward review before full campaign.",
    }
    manifest_path = output_root / "run_manifest.json"
    write_json(manifest_path, manifest)
    manifest["manifest_path"] = str(manifest_path.relative_to(root))
    return manifest


def inspect_pipeline(root: Path, registry: dict[str, Any], *, endpoint: str) -> dict[str, Any]:
    source = verify_source_set(root, registry)
    payload: dict[str, Any] = {"schema_version": SCHEMA_VERSION, "source_verification": source}
    try:
        inventory = comfy_inventory(endpoint)
        payload["comfyui_inventory"] = {
            "endpoint": inventory["endpoint"],
            "checkpoints": inventory["checkpoints"],
            "controlnets": inventory["controlnets"],
            "ipadapter_files": inventory["ipadapter_files"],
            "clip_vision": inventory["clip_vision"],
            "node_count": len(inventory["nodes"]),
        }
        payload["profile_validation"] = validate_profiles(registry, inventory)
    except Exception as exc:
        payload["comfyui_error"] = str(exc)
    return payload


def write_inspection(root: Path, registry: dict[str, Any], *, endpoint: str) -> dict[str, Any]:
    payload = inspect_pipeline(root, registry, endpoint=endpoint)
    path = root / "artifacts" / "visual_generation" / "evelyn_turnaround_pipeline" / ("inspection_" + now_id() + ".json")
    write_json(path, payload)
    payload["artifact_path"] = str(path.relative_to(root))
    return payload


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evelyn v1 multimodel T-pose pipeline")
    parser.add_argument("--root", type=Path, default=root_path())
    parser.add_argument("--profile-registry", type=Path, default=DEFAULT_PROFILE_PATH)
    parser.add_argument("--endpoint", default=os.environ.get("COMFYUI_ENDPOINT", DEFAULT_ENDPOINT))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inspect")
    sub.add_parser("prepare")
    sub.add_parser("validate-profiles")
    generate = sub.add_parser("generate-front-tpose")
    generate.add_argument("--samples-per-profile", type=int)
    args = parser.parse_args(list(argv) if argv is not None else None)
    root = args.root.resolve()
    registry = load_profile_registry(root, args.profile_registry)
    if args.command == "inspect":
        payload = write_inspection(root, registry, endpoint=args.endpoint)
    elif args.command == "prepare":
        payload = prepare_assets(root, registry)
    elif args.command == "validate-profiles":
        payload = validate_profiles(registry, comfy_inventory(args.endpoint))
    elif args.command == "generate-front-tpose":
        payload = run_bounded_front_tpose(root, registry, endpoint=args.endpoint, samples_per_profile=args.samples_per_profile)
    else:  # pragma: no cover
        raise AssertionError(args.command)
    print(json.dumps(payload, indent=2, sort_keys=True))
    if isinstance(payload, dict) and payload.get("status") == "fail":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
