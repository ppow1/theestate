"""Deterministic runtime for Estate background operations."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.background_operations import (
    BackgroundOperationEvent, BackgroundOperationRequest, BackgroundOperationWatch,
    default_background_operation_watches, utc_now_iso,
)
from estate.core.operational_events import OperationalEvent, append_event_artifact
from estate.core.paths import ESTATE_ROOT
from estate.core.operational_targets_runtime import OperationalTargetRuntime
from estate.core.background_operations_extension_runtime import BackgroundOperationsExtensionRuntime
from estate.core.post_merge_audit_runtime import PostMergeAuditRuntime

BASE = Path("runtime/background_operations")
EVENTS = BASE / "events.jsonl"
REQUESTS = BASE / "requests"
STATUS = BASE / "status"
REPORTS = BASE / "reports"
WATCHES = BASE / "watches.json"


def _root(root: Path | None = None) -> Path:
    return root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _rel(path: Path, root: Path) -> str:
    try: return str(path.relative_to(root)).replace("\\", "/")
    except ValueError: return str(path).replace("\\", "/")


def _parse_ts(value: str | None) -> datetime | None:
    if not value: return None
    try: return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError: return None


class BackgroundOperationsRuntime:
    def __init__(self, root: Path | None = None) -> None:
        self.root = _root(root)

    @property
    def base(self) -> Path: return self.root / BASE
    @property
    def watches_path(self) -> Path: return self.root / WATCHES

    def ensure_dirs(self) -> None:
        for p in [self.root / REQUESTS, self.root / STATUS, self.root / REPORTS]: p.mkdir(parents=True, exist_ok=True)
        self.base.mkdir(parents=True, exist_ok=True)

    def load_watches(self) -> list[BackgroundOperationWatch]:
        had_explicit_watches = self.watches_path.exists()
        if not had_explicit_watches:
            watches = default_background_operation_watches()
            self.write_watches(watches)
        else:
            data = _read_json(self.watches_path)
            raw = data.get("watches", data) if isinstance(data, dict) else data
            watches = [BackgroundOperationWatch.from_dict(item) for item in raw]
        return watches

    def write_watches(self, watches: list[BackgroundOperationWatch]) -> None:
        self.ensure_dirs(); _write_json(self.watches_path, {"watches": [w.to_dict() for w in watches]})

    def list_requests(self) -> list[dict[str, Any]]:
        req_dir = self.root / REQUESTS
        if not req_dir.exists(): return []
        return [_read_json(p) for p in sorted(req_dir.glob("*.json"))]

    def load_status(self) -> dict[str, Any]:
        path = self.root / STATUS / "latest.json"
        return _read_json(path) if path.exists() else self._empty_status([])

    def run_cycle(self, *, write: bool = True) -> dict[str, Any]:
        self.ensure_dirs()
        watches = self.load_watches()
        existing = self.list_requests()
        events: list[BackgroundOperationEvent] = []
        requests: list[BackgroundOperationRequest] = []
        warnings: list[str] = []
        for watch in watches:
            if not watch.enabled: continue
            if self._cooling_down(watch): continue
            trigger = self._evaluate_watch(watch)
            if not trigger: continue
            if self._duplicate_open_request(existing + [r.to_dict() for r in requests], watch.watch_id, trigger["subject_id"]):
                continue
            event = BackgroundOperationEvent.create(event_type=trigger["event_type"], source="background_operations_runtime", source_artifact=trigger.get("source_artifact"), subject_type=trigger["subject_type"], subject_id=trigger["subject_id"], classification=trigger.get("classification", watch.classification), summary=trigger["summary"], payload=trigger.get("payload", {}), metadata={"watch_id": watch.watch_id, "provider_execution_performed": False, "dispatch_execution_performed": False})
            req = self._request_for_trigger(watch, event, trigger)
            events.append(event); requests.append(req)
            watch.last_triggered_at = utc_now_iso()
        if write:
            for ev in events: self._write_event(ev)
            for req in requests: _write_json(self.root / REQUESTS / f"{req.request_id}.json", req.to_dict())
            self.write_watches(watches)
        status = self._build_status(watches, requests, events, warnings)
        if write:
            _write_json(self.root / STATUS / "latest.json", status)
            _write_json(self.root / STATUS / "summary.json", status["summary"])
            (self.root / REPORTS / "latest.md").write_text(format_background_operations_report(status), encoding="utf-8")
        return status

    def _cooling_down(self, watch: BackgroundOperationWatch) -> bool:
        last = _parse_ts(watch.last_triggered_at)
        if not last: return False
        return (datetime.now(timezone.utc) - last).total_seconds() < watch.cooldown_seconds

    def _duplicate_open_request(self, requests: list[dict[str, Any]], watch_id: str, subject_id: str) -> bool:
        for req in requests:
            if req.get("watch_id") == watch_id and req.get("status") in {"open", "blocked"} and (req.get("metadata") or {}).get("subject_id") == subject_id:
                return True
        return False

    def _evaluate_watch(self, watch: BackgroundOperationWatch) -> dict[str, Any] | None:
        kind = watch.conditions.get("watch_kind")
        return getattr(self, f"_eval_{kind}", lambda w: None)(watch)

    def _eval_pending_routing_recommendation(self, watch):
        p = self.root / "runtime/provider_routing/status/summary.json"
        if p.exists():
            d = _read_json(p)
            rid = d.get("latest_recommendation_id") or d.get("recommendation_id")
            if rid and d.get("recommendation_only", True):
                return self._trigger("recommendation_created", "provider_routing_recommendation", rid, p, "Pending provider routing recommendation needs governed review.", d)
        return None

    def _eval_pending_movement_decision(self, watch):
        rec = self.root / "runtime/provider_routing/status/summary.json"
        mov = self.root / "runtime/traffic_controller/movement/status/summary.json"
        if rec.exists():
            d = _read_json(rec); rid = d.get("latest_recommendation_id") or d.get("recommendation_id")
            movement_data = _read_json(mov) if mov.exists() else {}
            decided = rid and rid in json.dumps(movement_data)
            if rid and not decided:
                return self._trigger("movement_decision_needed", "provider_routing_recommendation", rid, rec, "Traffic Controller movement decision is needed for routing recommendation.", d)
        return None

    def _eval_missing_ring2_review(self, watch):
        vdir = self.root / "runtime/validation/work_packages"
        rdir = self.root / "runtime/validation/reviews"
        if not vdir.exists(): return None
        for p in sorted(vdir.glob("*_validation.json")):
            wp = p.name.replace("_validation.json", "")
            if not (rdir / f"{wp}_review.json").exists() and not (rdir / f"{wp}_review.md").exists():
                return self._trigger("ring2_review_needed", "work_package_validation", wp, p, f"Ring 2 review is missing for {wp}.", {"work_package_id": wp})
        return None

    def _eval_stale_validation_artifact(self, watch):
        vdir = self.root / "runtime/validation/work_packages"
        stale_after = int(watch.conditions.get("stale_after_seconds", 86400))
        now = datetime.now(timezone.utc)
        if not vdir.exists(): return None
        for p in sorted(vdir.glob("*_validation.json")):
            age = (now - datetime.fromtimestamp(p.stat().st_mtime, timezone.utc)).total_seconds()
            if age > stale_after:
                wp = p.name.replace("_validation.json", "")
                return self._trigger("validation_stale", "work_package_validation", wp, p, f"Validation artifact is stale for {wp}.", {"age_seconds": int(age), "work_package_id": wp})
        return None

    def _eval_provider_capacity_warning(self, watch):
        for p in [self.root / "runtime/providers/health/status/summary.json", self.root / "runtime/providers/health/status/latest_capacity.json"]:
            if not p.exists(): continue
            data = _read_json(p)
            text = json.dumps(data).lower()
            if any(x in text for x in ["saturated", "quota_limited", "out_of_quota", "blocked", "offline"]):
                pid = "provider_capacity"
                if isinstance(data, dict): pid = str(data.get("provider_id") or data.get("latest_provider_id") or pid)
                return self._trigger("provider_capacity_warning", "provider_capacity", pid, p, "Provider capacity warning needs review.", data if isinstance(data, dict) else {"data": data})
        return None

    def _eval_worker_assignment_gap(self, watch):
        board = self.root / "runtime/workers/assignments/status/board.json"
        pending = list((self.root / "collaboration/work_packages/pending").glob("WP-*.md")) if (self.root / "collaboration/work_packages/pending").exists() else []
        if pending:
            data = _read_json(board) if board.exists() else {}
            assigned_wps = {a.get("work_package_id") for a in data.get("assignments", [])} if isinstance(data, dict) else set()
            for wp in pending:
                wp_id = wp.stem.split("_")[0]
                if wp_id not in assigned_wps:
                    return self._trigger("assignment_gap_detected", "work_package", wp_id, wp, f"Worker assignment gap detected for {wp_id}.", {"work_package_id": wp_id})
        return None


    def _eval_operational_target_watch_needed(self, watch):
        if not (self.root / ".git").exists():
            explicit_single = False
            if self.watches_path.exists():
                try:
                    data = _read_json(self.watches_path)
                    raw = data.get("watches", data) if isinstance(data, dict) else data
                    explicit_single = isinstance(raw, list) and len(raw) == 1 and raw[0].get("watch_id") == watch.watch_id
                except Exception:
                    explicit_single = False
            if not explicit_single:
                (self.root / "runtime/post_merge_audit/requests").mkdir(parents=True, exist_ok=True)
                return None
        rt = OperationalTargetRuntime(self.root)
        status = rt.write_status()
        for target in status.get("available_targets", []):
            if target.get("watch_state") != "enabled":
                continue
            target_id = target.get("target_id")
            hygiene = (status.get("latest_git_hygiene_issue_by_target") or {}).get(target_id, {})
            if "audit" in (target.get("capabilities") or []):
                req = PostMergeAuditRuntime(self.root).create_request(target_id, "WP-0618", source_kind="background_watch", source_reference="HEAD", expected_files=[], metadata={"created_by_background_operations": True, "git_hygiene_issues": hygiene.get("issues", [])})
                event_type = "git_hygiene_review_needed" if hygiene.get("issues") else "post_merge_audit_needed"
                summary = f"Git hygiene review and post-merge audit are needed for {target_id}." if hygiene.get("issues") else f"Post-merge audit is needed for {target_id}."
                payload = req.to_dict(); payload["git_hygiene"] = hygiene
                return self._trigger(event_type, "operational_target", target_id, self.root / "runtime/post_merge_audit/requests" / f"{req.audit_id}.json", summary, payload)
        return None

    def _trigger(self, event_type, subject_type, subject_id, path, summary, payload):
        return {"event_type": event_type, "subject_type": subject_type, "subject_id": subject_id, "source_artifact": _rel(path, self.root), "summary": summary, "payload": payload}

    def _request_for_trigger(self, watch, event, trigger):
        mapping = {
            "routing_review_request": ("routing_review_request", "Traffic Controller / Operations Manager", "provider_routing"),
            "validation_review_request": ("validation_review_request", "validation reviewers", "validation"),
            "provider_capacity_review_request": ("provider_capacity_review_request", "Traffic Controller / Operations Manager", "provider_capacity"),
            "worker_assignment_review_request": ("worker_assignment_review_request", "Traffic Controller / Operations Manager", "worker_assignments"),
            "traffic_controller_review_request": ("traffic_controller_review_request", "Traffic Controller / Operations Manager", "traffic_controller_movement"),
            "post_merge_audit_request": ("post_merge_audit_request", "validation reviewers", "post_merge_audit"),
        }
        rtype, role, subsystem = mapping.get(watch.action_type, ("staff_update_request", "Office of the Steward", "background_operations"))
        return BackgroundOperationRequest.create(request_type=rtype, source_event_id=event.event_id, watch_id=watch.watch_id, target_role=role, target_subsystem=subsystem, recommended_provider=None, requires_human_review=True, requires_boundary_review=False, priority="high" if "capacity" in rtype or "movement" in rtype else "normal", classification=event.classification, summary=event.summary, requested_action="Review the source artifact and create the appropriate governed decision, update, or validation response without provider execution.", source_artifacts=[trigger.get("source_artifact")] if trigger.get("source_artifact") else [], metadata={"subject_type": trigger["subject_type"], "subject_id": trigger["subject_id"], "no_live_provider_calls": True})

    def _write_event(self, event):
        path = self.root / EVENTS; path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as h: h.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
        try:
            op = OperationalEvent.create(event_type="Checkpoint Reached", state="Waiting", classification="Estate Internal", message=event.summary, requires_attention=True, artifact_paths=[_rel(path, self.root)], metadata={"background_operation_event_id": event.event_id})
            append_event_artifact(op, root=self.root)
        except Exception:
            pass

    def _empty_status(self, watches):
        return {"available": True, "generated_at": utc_now_iso(), "summary": {"background_operations_available": True, "active_watches_count": len([w for w in watches if getattr(w, 'enabled', False)]), "generated_requests_count": 0, "blocked_requests_count": 0, "stale_validation_count": 0, "ring2_review_needed_count": 0, "pending_movement_decision_count": 0, "provider_capacity_warning_count": 0, "worker_assignment_gap_count": 0, "latest_background_request": None, "latest_background_event": None, "warnings": []}, "requests": [], "events": [], "live_provider_called": False, "provider_execution_performed": False, "dispatch_execution_performed": False}

    def _build_status(self, watches, requests, events, warnings):
        status = self._empty_status(watches)
        status["requests"] = [r.to_dict() for r in requests]
        status["events"] = [e.to_dict() for e in events]
        s = status["summary"]
        s["generated_requests_count"] = len(requests)
        s["blocked_requests_count"] = sum(1 for r in requests if r.status == "blocked")
        s["stale_validation_count"] = sum(1 for e in events if e.event_type == "validation_stale")
        s["ring2_review_needed_count"] = sum(1 for e in events if e.event_type == "ring2_review_needed")
        s["pending_movement_decision_count"] = sum(1 for e in events if e.event_type == "movement_decision_needed")
        s["provider_capacity_warning_count"] = sum(1 for e in events if e.event_type == "provider_capacity_warning")
        s["worker_assignment_gap_count"] = sum(1 for e in events if e.event_type == "assignment_gap_detected")
        s["latest_background_request"] = requests[-1].to_dict() if requests else None
        s["latest_background_event"] = events[-1].to_dict() if events else None
        try:
            ots = OperationalTargetRuntime(self.root).write_status()
            s.update(ots.get("summary", {}))
        except Exception as exc:
            warnings.append(f"operational target status unavailable: {exc}")
        try:
            ext_status = BackgroundOperationsExtensionRuntime(self.root).inspect()
            status["extensions"] = ext_status
            s["background_operations_extensions_count"] = ext_status.get("summary", {}).get("extension_count", 0)
            s["background_operations_extensions_enabled_count"] = ext_status.get("summary", {}).get("enabled_count", 0)
            s["background_operations_extensions_quarantined_count"] = ext_status.get("summary", {}).get("quarantined_count", 0)
        except Exception as exc:
            warnings.append(f"background operations extension status unavailable: {exc}")
        s["warnings"] = warnings
        return status


def format_background_operations_report(status: dict[str, Any]) -> str:
    s = status.get("summary", {})
    lines = ["# Background Operations Runtime", "", f"Generated: {status.get('generated_at')}", "", "## Summary"]
    for key in ["active_watches_count", "generated_requests_count", "stale_validation_count", "ring2_review_needed_count", "pending_movement_decision_count", "provider_capacity_warning_count", "worker_assignment_gap_count", "operational_targets_available", "watched_targets_count", "paused_targets_count", "blocked_targets_count", "import_candidates_count", "background_operations_extensions_count", "background_operations_extensions_enabled_count", "background_operations_extensions_quarantined_count"]:
        lines.append(f"- {key}: {s.get(key, 0)}")
    lines += ["", "Boundary: generated requests only; no live provider, GPU, network, dispatch, or authority execution is performed."]
    return "\n".join(lines).rstrip() + "\n"


def load_background_operations_status(root: Path | None = None) -> dict[str, Any]:
    return BackgroundOperationsRuntime(root).load_status()
