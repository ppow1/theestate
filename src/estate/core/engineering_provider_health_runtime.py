"""Engineering provider health runtime.

Normalizes read-only provider health evidence for advisory routing and Office
consumption. It never submits prompts, starts provider jobs, or dispatches work.
"""
from __future__ import annotations

import json, os, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.provider_health import _write_json, latest_health_by_provider, utc_now_iso
from estate.core.provider_capacity import latest_capacity_by_provider

PROVIDERS = {
    "codex_cloud_web": "cloud_codex",
    "codex_cli_openai": "codex_cli",
    "local_ollama_gpu": "local_ollama",
    "local_gpu_runtime": "local_gpu",
}
CURRENT = Path("runtime/provider_health/current.json")
PROVIDERS_DIR = Path("runtime/provider_health/providers")
HISTORY = Path("runtime/provider_health/history.jsonl")
OFFICE_MD = Path("operations/engineering_capacity/provider_health.md")
DEFAULT_STALE_AFTER_SECONDS = 1800
SCHEMA_VERSION = "1.0"


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _parse_ts(value: str | None) -> datetime | None:
    if not value: return None
    try: return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception: return None


def _age_seconds(value: str | None, now: datetime) -> float | None:
    dt = _parse_ts(value)
    return None if dt is None else (now - dt).total_seconds()


def _read_json(path: Path) -> Any | None:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return None


def _polling_policy(root: Path) -> dict[str, Any]:
    for rel in ("runtime/provider_registry/codex/polling_policy.json", "runtime/codex_cli/capability_discovery/polling_policy.json"):
        data = _read_json(root / rel)
        if isinstance(data, dict): return data | {"evidence_ref": rel}
    return {"automatic_live_polling_allowed": False, "unknown_probe_cost_blocks_polling": True, "evidence_ref": "missing polling policy"}


def _capability_state(root: Path, provider_id: str, now: datetime, stale_after: int) -> tuple[str, str | None, list[str]]:
    refs=[]
    candidates = [root / "runtime/provider_registry/codex/capabilities.json", root / "runtime/codex_cli/capability_discovery/capabilities.json"] if provider_id.startswith("codex") else []
    existing = [p for p in candidates if p.exists()]
    if not candidates: return "unknown", None, refs
    if not existing: return "missing", None, refs
    p = existing[0]; refs.append(str(p.relative_to(root)))
    data = _read_json(p)
    ts = (data or {}).get("observed_at") or (data or {}).get("generated_at")
    if _age_seconds(ts, now) is not None and _age_seconds(ts, now) > stale_after: return "stale", ts, refs
    return "fresh", ts, refs


def _probe(provider_id: str, policy: dict[str, Any]) -> dict[str, Any]:
    if provider_id == "codex_cli_openai":
        exe = shutil.which("codex")
        return {"availability": "available" if exe else "offline", "provider_version": None, "warnings": [] if exe else ["codex executable not found"], "evidence_refs": ["PATH:codex"]}
    if provider_id == "local_ollama_gpu":
        exe = shutil.which("ollama")
        return {"availability": "available" if exe else "offline", "provider_version": None, "warnings": [] if exe else ["ollama executable not found"], "evidence_refs": ["PATH:ollama"]}
    if provider_id == "local_gpu_runtime":
        exe = shutil.which("nvidia-smi")
        ver = None
        if exe:
            try:
                r = subprocess.run([exe, "--query-gpu=driver_version", "--format=csv,noheader"], text=True, capture_output=True, timeout=3, check=False)
                ver = (r.stdout.splitlines() or [None])[0]
            except Exception: pass
        return {"availability": "available" if exe else "unknown", "provider_version": ver, "warnings": [] if exe else ["nvidia-smi executable not found"], "evidence_refs": ["PATH:nvidia-smi"]}
    allowed = bool(policy.get("automatic_live_polling_allowed") or policy.get("automatic_polling_allowed"))
    return {"availability": "unknown", "provider_version": None, "warnings": ["remote Codex polling skipped by WP-0534 policy" if not allowed else "remote Codex prompt-free polling not configured"], "evidence_refs": [policy.get("evidence_ref", "polling policy")]}


def evaluate_provider(provider_id: str, *, root: str | Path | None = None, now: datetime | None = None, stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS) -> dict[str, Any]:
    rootp=_root(root); now=now or datetime.now(timezone.utc); observed=now.replace(microsecond=0).isoformat().replace("+00:00","Z")
    manual = latest_health_by_provider(rootp).get(provider_id); cap = latest_capacity_by_provider(rootp).get(provider_id)
    policy=_polling_policy(rootp); probe=_probe(provider_id, policy); warnings=list(probe["warnings"]); reasons=[]; refs=list(probe["evidence_refs"])
    cap_state = cap.capacity_state if cap else "unknown"; active=cap.active_jobs if cap else 0; queue=cap.queue_depth if cap else 0
    last_cap = cap.checked_at if cap else None; cap_stale = _age_seconds(last_cap, now) is None or (_age_seconds(last_cap, now) or 0) > stale_after_seconds
    reg_state, last_disc, reg_refs = _capability_state(rootp, provider_id, now, stale_after_seconds); refs += reg_refs
    auth = "unknown"; runtime = probe["availability"]
    if manual:
        refs.append("runtime/providers/health/records")
        if manual.status in {"blocked", "offline"}: runtime = "offline"
        if manual.status == "available": runtime = "available"
        auth = manual.metadata.get("authentication_state") or auth
    if provider_id.startswith("codex") and auth == "unknown": auth = "unknown"
    latency = manual.metadata.get("latency_ms") if manual else None
    succ = int((manual.metadata.get("recent_success_count") if manual else 0) or 0); fail = int((manual.metadata.get("recent_failure_count") if manual else 0) or 0)
    consec = int((manual.metadata.get("consecutive_failures") if manual else 0) or 0); failure_rate = fail / max(1, succ + fail)
    last_success = manual.metadata.get("last_success_at") if manual else None; last_failure = manual.metadata.get("last_failure_at") if manual else None
    disabled = manual and manual.metadata.get("disabled") is True; maintenance = manual and manual.metadata.get("maintenance") is True
    if disabled: reasons.append("provider explicitly disabled")
    if maintenance: reasons.append("provider in maintenance")
    if runtime == "offline": reasons.append("provider runtime unavailable or manually offline")
    if auth in {"invalid", "missing", "unauthenticated"}: reasons.append("authentication is not ready")
    if reg_state in {"missing", "stale"}: reasons.append(f"capability registry is {reg_state}")
    if cap_stale: reasons.append("capacity evidence is missing or stale")
    if cap_state in {"saturated", "quota_limited"}: reasons.append(f"capacity is {cap_state}")
    if consec >= 3 or failure_rate >= .5: reasons.append("recent failure threshold exceeded")
    if isinstance(latency,(int,float)) and latency > 30000: reasons.append("observed latency is degraded")
    if queue >= 10: reasons.append("queue depth is high")
    is_stale = cap_stale or reg_state == "stale"
    if maintenance: state="maintenance"
    elif runtime == "offline" or disabled or auth in {"invalid","missing","unauthenticated"}: state="offline"
    elif not manual and runtime == "unknown": state="unknown"
    elif any(x in reasons for x in ["capacity is saturated", "capacity is quota_limited"]) or consec or failure_rate >= .2 or is_stale or (isinstance(latency,(int,float)) and latency>10000) or queue>=5: state="degraded"
    elif runtime == "available" and auth != "invalid" and not is_stale: state="healthy"
    else: state="unknown"
    recommended = state == "healthy" and auth not in {"invalid","missing","unauthenticated"} and cap_state not in {"saturated","quota_limited"} and not disabled
    return {"schema_version":SCHEMA_VERSION,"provider_id":provider_id,"provider_type":PROVIDERS[provider_id],"observed_at":observed,"last_success_at":last_success,"last_failure_at":last_failure,"availability":probe["availability"],"authentication_state":auth,"runtime_state":runtime,"capability_registry_state":reg_state,"capacity_state":cap_state,"latency_ms":latency,"recent_success_count":succ,"recent_failure_count":fail,"recent_failure_rate":failure_rate,"consecutive_failures":consec,"queue_depth":queue,"active_jobs":active,"provider_version":probe["provider_version"],"last_discovery_at":last_disc,"last_capacity_snapshot_at":last_cap,"stale_after_seconds":stale_after_seconds,"is_stale":is_stale,"health_state":state,"health_reasons":reasons or ["no blocking health reasons observed"],"warnings":warnings,"evidence_refs":sorted(set(refs)),"recommended_for_dispatch":recommended}


def collect_provider_health(*, root: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    rootp=_root(root); providers=[evaluate_provider(pid, root=rootp) for pid in PROVIDERS]
    payload={"schema_version":SCHEMA_VERSION,"generated_at":utc_now_iso(),"constraints":{"advisory_only":True,"does_not_submit_prompts":True,"does_not_dispatch":True},"providers":providers}
    if write:
        _write_json(rootp / CURRENT, payload)
        for p in providers: _write_json(rootp / PROVIDERS_DIR / f"{p['provider_id']}.json", p)
        (rootp / HISTORY).parent.mkdir(parents=True, exist_ok=True)
        with (rootp / HISTORY).open("a", encoding="utf-8") as fh: fh.write(json.dumps(payload, sort_keys=True)+"\n")
        (rootp / OFFICE_MD).parent.mkdir(parents=True, exist_ok=True); (rootp / OFFICE_MD).write_text(format_provider_health_report(payload), encoding="utf-8")
    return payload


def load_current_provider_health(*, root: str | Path | None = None) -> dict[str, Any]:
    data=_read_json(_root(root)/CURRENT)
    return data if isinstance(data, dict) else collect_provider_health(root=root, write=True)


def format_provider_health_report(payload: dict[str, Any]) -> str:
    lines=["# Engineering Provider Health", "", f"Generated: {payload.get('generated_at')}", "", "Advisory only: this surface does not dispatch or submit provider prompts.", "", "Provider | Health | Auth | Fresh | Last success | Last failure | Latency | Failure rate | Active | Queue | Capacity | Dispatch eligible | Reasons / warnings"]
    for p in payload.get("providers",[]):
        lines.append(f"{p['provider_id']} | {p['health_state']} | {p['authentication_state']} | {not p['is_stale']} | {p.get('last_success_at') or ''} | {p.get('last_failure_at') or ''} | {p.get('latency_ms')} | {p.get('recent_failure_rate')} | {p.get('active_jobs')} | {p.get('queue_depth')} | {p.get('capacity_state')} | {p.get('recommended_for_dispatch')} | {'; '.join((p.get('health_reasons') or []) + (p.get('warnings') or []))}")
    return "\n".join(lines).rstrip()+"\n"
