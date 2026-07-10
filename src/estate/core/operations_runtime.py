"""Operations Runtime service model and cycle coordinator.

The runtime observes local Estate artifacts and creates governed requests/status only.
It never executes providers, dispatch queues, repair logic, stash, or acceptance flows.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.background_operations_runtime import BackgroundOperationsRuntime, format_background_operations_report
from estate.core.operational_targets_runtime import OperationalTargetRuntime
from estate.core.post_merge_audit_processor import PostMergeAuditProcessor
from estate.core.merge_discovery_runtime import MergeDiscoveryRuntime
from estate.core.paths import ESTATE_ROOT

RUNTIME_BASE = Path("runtime/operations_runtime")
STATUS_DIR = RUNTIME_BASE / "status"
REPORTS_DIR = RUNTIME_BASE / "reports"
CYCLES_DIR = RUNTIME_BASE / "cycles"
HEARTBEAT = RUNTIME_BASE / "heartbeat.json"
LOCK = RUNTIME_BASE / "lock.json"
STOP_REQUEST = RUNTIME_BASE / "stop_requested.json"
ALLOWED_RUNTIME_STATES = {"idle", "starting", "running", "sleeping", "stop_requested", "stopped", "blocked", "failed"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _root(root: Path | None = None) -> Path:
    return root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


@dataclass
class OperationsRuntimeCycle:
    cycle_id: str
    started_at: str
    finished_at: str | None
    runtime_state: str
    targets_evaluated: int = 0
    watches_evaluated: int = 0
    requests_created: int = 0
    events_created: int = 0
    audits_requested: int = 0
    git_hygiene_findings: int = 0
    ring2_requests_created: int = 0
    audits_claimed: int = 0
    audits_completed: int = 0
    audits_blocked: int = 0
    audit_validation_pass: int = 0
    audit_validation_fail: int = 0
    ring2_prompts_generated: int = 0
    ring2_reviews_captured: int = 0
    audit_verdicts_published: int = 0
    merge_commits_scanned: int = 0
    work_packages_discovered: int = 0
    discoveries_ambiguous: int = 0
    discoveries_ignored: int = 0
    audit_requests_created_from_merges: int = 0
    duplicate_audit_requests_suppressed: int = 0
    canonical_candidates: int = 0
    superseded_discoveries: int = 0
    quarantined_discoveries: int = 0
    admitted_requests: int = 0
    requests_suppressed_by_grouping: int = 0
    backfill_limit_reached: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    provider_execution_performed: bool = False
    dispatch_execution_performed: bool = False
    artifacts: dict[str, str] = field(default_factory=dict)

    @classmethod
    def start(cls) -> "OperationsRuntimeCycle":
        return cls(cycle_id=f"orc-{uuid4().hex}", started_at=utc_now_iso(), finished_at=None, runtime_state="running")

    def to_dict(self) -> dict[str, Any]:
        if self.runtime_state not in ALLOWED_RUNTIME_STATES:
            raise ValueError(f"unknown runtime_state {self.runtime_state}")
        return asdict(self)


class OperationsRuntime:
    def __init__(self, root: Path | None = None) -> None:
        self.root = _root(root)
        self.background = BackgroundOperationsRuntime(self.root)
        self.targets = OperationalTargetRuntime(self.root)

    @property
    def base(self) -> Path:
        return self.root / RUNTIME_BASE

    def ensure_dirs(self) -> None:
        for rel in [STATUS_DIR, REPORTS_DIR, CYCLES_DIR]:
            (self.root / rel).mkdir(parents=True, exist_ok=True)

    def run_cycle(self, *, dry_run: bool = False, mode: str = "observe-only") -> dict[str, Any]:
        self.ensure_dirs()
        cycle = OperationsRuntimeCycle.start()
        try:
            target_status = self.targets.write_status()
            watches = self.background.load_watches()
            before_requests = len(self.background.list_requests())
            background_status = self.background.run_cycle(write=not dry_run)
            after_requests = len(self.background.list_requests()) if not dry_run else before_requests + len(background_status.get("requests", []))
            enabled_targets = [t for t in target_status.get("available_targets", []) if t.get("watch_state") == "enabled"]
            hygiene = target_status.get("latest_git_hygiene_issue_by_target") or {}
            cycle.targets_evaluated = len(enabled_targets)
            cycle.watches_evaluated = len([w for w in watches if w.enabled])
            cycle.requests_created = max(0, after_requests - before_requests) if not dry_run else len(background_status.get("requests", []))
            cycle.events_created = len(background_status.get("events", []))
            cycle.audits_requested = sum(1 for r in background_status.get("requests", []) if r.get("request_type") == "post_merge_audit_request")
            cycle.git_hygiene_findings = sum(len(v.get("issues") or []) for v in hygiene.values())
            cycle.ring2_requests_created = sum(1 for e in background_status.get("events", []) if e.get("event_type") == "ring2_review_needed")
            cycle.warnings.extend(background_status.get("summary", {}).get("warnings") or [])
            if mode in {"discover-merges", "discover-merges-and-process-audits", "discover-merges-and-process-audits-and-ring2"} and not dry_run:
                discovery = MergeDiscoveryRuntime(self.root).scan("estate-main", backfill_mode="admit")
                ms = discovery.get("summary", {})
                cycle.merge_commits_scanned = ms.get("merge_commits_scanned", 0)
                cycle.work_packages_discovered = ms.get("work_packages_discovered", 0)
                cycle.discoveries_ambiguous = ms.get("discoveries_ambiguous", 0)
                cycle.discoveries_ignored = ms.get("discoveries_ignored", 0)
                cycle.audit_requests_created_from_merges = ms.get("audit_requests_created_from_merges", 0)
                cycle.duplicate_audit_requests_suppressed = ms.get("duplicate_audit_requests_suppressed", 0)
                cycle.canonical_candidates = ms.get("canonical_candidates", 0)
                cycle.superseded_discoveries = ms.get("superseded_discoveries", 0)
                cycle.quarantined_discoveries = ms.get("quarantined_discoveries", 0)
                cycle.admitted_requests = ms.get("admitted_requests", 0)
                cycle.requests_suppressed_by_grouping = ms.get("requests_suppressed_by_grouping", 0)
                cycle.backfill_limit_reached = bool(ms.get("backfill_limit_reached", False))
            if mode in {"process-audits", "process-audits-and-ring2", "discover-merges-and-process-audits", "discover-merges-and-process-audits-and-ring2"} and not dry_run:
                audit_result = PostMergeAuditProcessor(self.root, ollama_enabled=(mode in {"process-audits-and-ring2", "discover-merges-and-process-audits-and-ring2"})).process_next()
                if audit_result.get("processed"):
                    v = audit_result.get("verdict") or {}
                    cycle.audits_claimed = 1
                    cycle.audits_completed = 1 if v.get("state") in {"completed", "ring2_required"} else 0
                    cycle.audits_blocked = 1 if v.get("state") == "blocked" else 0
                    cycle.audit_validation_pass = 1 if v.get("validation_status") in {"passed", "passed_with_findings"} else 0
                    cycle.audit_validation_fail = 1 if v.get("validation_status") in {"failed", "no_recipe"} or v.get("verdict") == "validation_failed" else 0
                    cycle.ring2_prompts_generated = 1 if (v.get("artifacts") or {}).get("ring2_prompt") else 0
                    cycle.ring2_reviews_captured = 1 if v.get("ring2_status") == "review_captured" else 0
                    cycle.audit_verdicts_published = 1 if v.get("verdict_path") else 0
            cycle.artifacts = {
                "background_status": "runtime/background_operations/status/latest.json",
                "operational_targets_status": "runtime/operational_targets/status/latest.json",
            }
            if cycle.audits_claimed:
                cycle.artifacts["post_merge_audit_status"] = "runtime/post_merge_audit/status/latest.json"
            cycle.runtime_state = "stopped"
        except Exception as exc:  # cycle status must persist failures for Office visibility
            cycle.runtime_state = "failed"
            cycle.errors.append(str(exc))
        cycle.finished_at = utc_now_iso()
        payload = cycle.to_dict()
        if not dry_run:
            self.write_status(payload)
        return payload

    def write_status(self, cycle: dict[str, Any], *, state: str | None = None) -> dict[str, Any]:
        summary = self.summary_from_cycle(cycle, state=state)
        payload = {"available": True, "generated_at": utc_now_iso(), "latest_cycle": cycle, "summary": summary, "provider_execution_performed": False, "dispatch_execution_performed": False}
        _write_json(self.root / CYCLES_DIR / f"{cycle['cycle_id']}.json", cycle)
        _write_json(self.root / STATUS_DIR / "latest.json", payload)
        _write_json(self.root / STATUS_DIR / "summary.json", summary)
        _write_json(self.root / HEARTBEAT, {"heartbeat_at": utc_now_iso(), **summary})
        (self.root / REPORTS_DIR / "latest.md").write_text(format_operations_runtime_report(payload), encoding="utf-8")
        return payload

    def load_status(self) -> dict[str, Any]:
        path = self.root / STATUS_DIR / "latest.json"
        if path.exists():
            return _read_json(path)
        return {"available": True, "generated_at": utc_now_iso(), "latest_cycle": None, "summary": self.empty_summary("idle"), "provider_execution_performed": False, "dispatch_execution_performed": False}

    def request_stop(self) -> dict[str, Any]:
        payload = {"stop_requested": True, "requested_at": utc_now_iso()}
        _write_json(self.root / STOP_REQUEST, payload)
        status = self.load_status()
        status["summary"]["operations_runtime_state"] = "stop_requested"
        _write_json(self.root / STATUS_DIR / "latest.json", status)
        _write_json(self.root / STATUS_DIR / "summary.json", status["summary"])
        return payload

    def stop_requested(self) -> bool:
        return (self.root / STOP_REQUEST).exists()

    def clear_stop_request(self) -> None:
        p = self.root / STOP_REQUEST
        if p.exists():
            p.unlink()

    def empty_summary(self, state: str) -> dict[str, Any]:
        return {"operations_runtime_available": True, "operations_runtime_state": state, "last_cycle_id": None, "last_cycle_at": None, "active_targets_count": 0, "enabled_watches_count": 0, "requests_created_last_cycle": 0, "audits_requested_last_cycle": 0, "git_hygiene_findings_count": 0, "ring2_requests_count": 0, "audits_claimed_last_cycle": 0, "audits_completed_last_cycle": 0, "audits_blocked_last_cycle": 0, "audit_validation_pass_last_cycle": 0, "audit_validation_fail_last_cycle": 0, "ring2_prompts_generated_last_cycle": 0, "ring2_reviews_captured_last_cycle": 0, "audit_verdicts_published_last_cycle": 0, "runtime_warnings": [], "merge_commits_scanned": 0, "work_packages_discovered": 0, "discoveries_ambiguous": 0, "discoveries_ignored": 0, "audit_requests_created_from_merges": 0, "duplicate_audit_requests_suppressed": 0, "canonical_candidates": 0, "superseded_discoveries": 0, "quarantined_discoveries": 0, "admitted_requests": 0, "requests_suppressed_by_grouping": 0, "backfill_limit_reached": False}

    def summary_from_cycle(self, cycle: dict[str, Any], *, state: str | None = None) -> dict[str, Any]:
        return {"operations_runtime_available": True, "operations_runtime_state": state or cycle.get("runtime_state", "stopped"), "last_cycle_id": cycle.get("cycle_id"), "last_cycle_at": cycle.get("finished_at") or cycle.get("started_at"), "active_targets_count": cycle.get("targets_evaluated", 0), "enabled_watches_count": cycle.get("watches_evaluated", 0), "requests_created_last_cycle": cycle.get("requests_created", 0), "audits_requested_last_cycle": cycle.get("audits_requested", 0), "git_hygiene_findings_count": cycle.get("git_hygiene_findings", 0), "ring2_requests_count": cycle.get("ring2_requests_created", 0), "audits_claimed_last_cycle": cycle.get("audits_claimed", 0), "audits_completed_last_cycle": cycle.get("audits_completed", 0), "audits_blocked_last_cycle": cycle.get("audits_blocked", 0), "audit_validation_pass_last_cycle": cycle.get("audit_validation_pass", 0), "audit_validation_fail_last_cycle": cycle.get("audit_validation_fail", 0), "ring2_prompts_generated_last_cycle": cycle.get("ring2_prompts_generated", 0), "ring2_reviews_captured_last_cycle": cycle.get("ring2_reviews_captured", 0), "audit_verdicts_published_last_cycle": cycle.get("audit_verdicts_published", 0), "runtime_warnings": cycle.get("warnings", []) + cycle.get("errors", []), "merge_commits_scanned": cycle.get("merge_commits_scanned", 0), "work_packages_discovered": cycle.get("work_packages_discovered", 0), "discoveries_ambiguous": cycle.get("discoveries_ambiguous", 0), "discoveries_ignored": cycle.get("discoveries_ignored", 0), "audit_requests_created_from_merges": cycle.get("audit_requests_created_from_merges", 0), "duplicate_audit_requests_suppressed": cycle.get("duplicate_audit_requests_suppressed", 0), "canonical_candidates": cycle.get("canonical_candidates", 0), "superseded_discoveries": cycle.get("superseded_discoveries", 0), "quarantined_discoveries": cycle.get("quarantined_discoveries", 0), "admitted_requests": cycle.get("admitted_requests", 0), "requests_suppressed_by_grouping": cycle.get("requests_suppressed_by_grouping", 0), "backfill_limit_reached": cycle.get("backfill_limit_reached", False)}


def format_operations_runtime_report(status: dict[str, Any]) -> str:
    s = status.get("summary", {})
    lines = ["# Operations Runtime Service Loop", "", f"Generated: {status.get('generated_at')}", "", "## Health"]
    for key in ["operations_runtime_state", "last_cycle_id", "last_cycle_at", "active_targets_count", "enabled_watches_count", "requests_created_last_cycle", "audits_requested_last_cycle", "git_hygiene_findings_count", "ring2_requests_count"]:
        lines.append(f"- {key}: {s.get(key)}")
    lines += ["", "Boundary: observes, evaluates, requests, and reports only. No provider or dispatch execution is performed."]
    return "\n".join(lines).rstrip() + "\n"


def load_operations_runtime_status(root: Path | None = None) -> dict[str, Any]:
    return OperationsRuntime(root).load_status()
