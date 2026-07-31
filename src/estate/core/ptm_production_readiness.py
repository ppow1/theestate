"""Bounded production PTM ledger and dependency/readiness resolver.

This module is deliberately limited to PTM authority.  It does not enqueue
work, select providers, create Engineering commissions, or grant acceptance.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from .ptm_ids import is_valid_ptm_id, new_ptm_id

SCHEMA_VERSION = "estate.ptm.readiness-resolution.v1"
EVENT_SCHEMA = "estate.ptm.event.v1"
EVENTS_ROOT = Path("runtime/ptm/ledger/events")
READINESS_ROOT = Path("runtime/ptm/readiness")
DEPENDENCY_STATES = {"unsatisfied", "satisfied", "waived", "unknown"}
READINESS_STATES = {"not_ready", "ready", "blocked", "waived", "unknown"}
GATE_STATES = {"pass", "fail", "waived", "unknown"}
ID_RE = re.compile(r"^[A-Za-z0-9_.:/-]+$")


class PtmReadinessError(ValueError):
    """A bounded, fail-closed resolver error."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_time(value: str) -> datetime:
    if not isinstance(value, str):
        raise PtmReadinessError("timestamp must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PtmReadinessError("timestamp is not valid ISO-8601") from exc
    if parsed.tzinfo is None:
        raise PtmReadinessError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _require_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or not ID_RE.fullmatch(value):
        raise PtmReadinessError(f"{field} is missing or invalid")
    return value


def _safe_relative_path(root: Path, relative: str, field: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or any(part == ".." for part in Path(relative).parts):
        raise PtmReadinessError(f"{field} must be repository-relative without traversal")
    candidate = (root / relative).resolve()
    root = root.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise PtmReadinessError(f"{field} escapes repository") from exc
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise PtmReadinessError(f"{field} crosses a symlink or reparse point")
    return candidate


def _fsync_parent(path: Path) -> None:
    if os.name == "nt":
        return
    try:
        fd = os.open(str(path.parent), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_create_once(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8")
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise PtmReadinessError(f"create-once collision at {path.as_posix()}") from exc
    stream = os.fdopen(fd, "wb")
    created = True
    try:
        offset = 0
        while offset < len(encoded):
            count = stream.write(encoded[offset:])
            if count is None or count <= 0 or count > len(encoded) - offset:
                raise OSError("PTM ledger write made no valid progress")
            offset += count
        stream.flush()
        os.fsync(stream.fileno())
        stream.close()
        created = False
        _fsync_parent(path)
    except BaseException as exc:
        try:
            stream.close()
        except BaseException:
            pass
        if created:
            raise PtmReadinessError(f"partial PTM record retained at {path.as_posix()}") from exc
        raise


def _event_hash(event: dict[str, Any]) -> str:
    unsigned = dict(event)
    unsigned.pop("event_hash", None)
    return hashlib.sha256(canonical_json(unsigned).encode("utf-8")).hexdigest()


def _event_path(root: Path, event: dict[str, Any]) -> Path:
    stream = re.sub(r"[^A-Za-z0-9_.-]", "_", event["stream_id"])
    return _safe_relative_path(root, (EVENTS_ROOT / stream / f"{event['sequence_number']:020d}_{event['event_id']}.json").as_posix(), "event path")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PtmReadinessError(f"malformed PTM record: {path.as_posix()}") from exc
    if not isinstance(value, dict):
        raise PtmReadinessError(f"PTM record is not an object: {path.as_posix()}")
    return value


def _validate_event(event: dict[str, Any]) -> None:
    required = ("event_id", "event_type", "event_version", "aggregate_type", "aggregate_id", "stream_id", "sequence_number", "occurred_at", "recorded_at", "actor_ref", "authority_refs", "source_refs", "idempotency_key", "payload_schema", "payload", "previous_event_hash", "event_hash", "hash_algorithm")
    for key in required:
        if key not in event:
            raise PtmReadinessError(f"PTM event missing {key}")
    if event["hash_algorithm"] != "sha256" or event["event_hash"] != _event_hash(event):
        raise PtmReadinessError(f"PTM event hash invalid: {event.get('event_id')}")
    if not is_valid_ptm_id(event["event_id"], "evt"):
        raise PtmReadinessError("PTM event_id is not a canonical event ID")
    if not isinstance(event["sequence_number"], int) or event["sequence_number"] < 1:
        raise PtmReadinessError("PTM sequence_number is invalid")
    if not isinstance(event["stream_id"], str) or not re.fullmatch(r"[A-Za-z0-9_.:-]+", event["stream_id"]):
        raise PtmReadinessError("PTM stream_id is invalid")
    if not isinstance(event["authority_refs"], list) or not isinstance(event["source_refs"], list):
        raise PtmReadinessError("PTM event references must be arrays")
    if not isinstance(event["payload"], dict):
        raise PtmReadinessError("PTM event payload must be an object")
    _parse_time(event["occurred_at"])
    _parse_time(event["recorded_at"])


def append_ptm_event(root: Path, *, event_type: str, aggregate_type: str, aggregate_id: str, stream_id: str, actor_ref: str, authority_refs: list[str], source_refs: list[dict[str, Any]], payload_schema: str, payload: dict[str, Any], idempotency_key: str, occurred_at: str, correlation_id: str | None = None, causation_id: str | None = None, event_id: str | None = None) -> dict[str, Any]:
    """Append one immutable event using the CORE-PTM-002A envelope."""
    root = Path(root).resolve()
    stream_dir = re.sub(r"[^A-Za-z0-9_.-]", "_", stream_id)
    lock_root = _safe_relative_path(root, (EVENTS_ROOT / f".locks/{stream_dir}").as_posix(), "event lock path")
    lock_root.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.mkdir(lock_root)
    except FileExistsError as exc:
        raise PtmReadinessError("PTM stream is concurrently being appended or has a stale lock") from exc
    try:
        existing = _load_events(root)
        for event in existing:
            if event["idempotency_key"] == idempotency_key:
                if event["payload"] == payload and event["event_type"] == event_type:
                    return event
                raise PtmReadinessError("conflicting PTM idempotency key")
        stream_events = [e for e in existing if e["stream_id"] == stream_id]
        sequence = max((int(e["sequence_number"]) for e in stream_events), default=0) + 1
        previous = max(stream_events, key=lambda e: int(e["sequence_number"]))["event_hash"] if stream_events else None
        now = _iso(datetime.now(timezone.utc))
        event = {
            "event_id": event_id or new_ptm_id("evt"), "event_type": event_type, "event_version": 1,
            "aggregate_type": aggregate_type, "aggregate_id": aggregate_id, "stream_id": stream_id,
            "sequence_number": sequence, "occurred_at": occurred_at, "recorded_at": now,
            "actor_ref": actor_ref, "authority_refs": list(authority_refs), "source_refs": list(source_refs),
            "causation_id": causation_id, "correlation_id": correlation_id, "command_id": None,
            "idempotency_key": idempotency_key, "payload_schema": payload_schema, "payload": payload,
            "previous_event_hash": previous, "hash_algorithm": "sha256",
        }
        event["event_hash"] = _event_hash(event)
        _validate_event(event)
        _write_create_once(_event_path(root, event), event)
        return event
    finally:
        try:
            os.rmdir(lock_root)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise PtmReadinessError("PTM stream lock cleanup failed") from exc


def _exclusive_directory_lock(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.mkdir(path)
    except FileExistsError as exc:
        raise PtmReadinessError("PTM resolution is concurrently being evaluated") from exc


def _release_directory_lock(path: Path) -> None:
    try:
        os.rmdir(path)
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise PtmReadinessError("PTM resolution lock cleanup failed") from exc


def _load_events(root: Path) -> list[dict[str, Any]]:
    directory = root / EVENTS_ROOT
    if not directory.exists():
        return []
    events: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_keys: set[tuple[str, str]] = set()
    for path in sorted(directory.rglob("*.json")):
        if path.is_symlink():
            raise PtmReadinessError(f"symlinked PTM event rejected: {path.as_posix()}")
        event = _load_json(path)
        _validate_event(event)
        expected_path = _event_path(root, event)
        if path.resolve() != expected_path.resolve():
            raise PtmReadinessError(f"foreign PTM event path rejected: {path.as_posix()}")
        if event["event_id"] in seen_ids or (event["stream_id"], event["idempotency_key"]) in seen_keys:
            raise PtmReadinessError("duplicate PTM event identity or idempotency key")
        seen_ids.add(event["event_id"])
        seen_keys.add((event["stream_id"], event["idempotency_key"]))
        events.append(event)
    for stream in {e["stream_id"] for e in events}:
        rows = sorted((e for e in events if e["stream_id"] == stream), key=lambda e: int(e["sequence_number"]))
        previous = None
        for expected, event in enumerate(rows, 1):
            if int(event["sequence_number"]) != expected or event["previous_event_hash"] != previous:
                raise PtmReadinessError(f"PTM hash chain invalid for stream {stream}")
            previous = event["event_hash"]
    return events


def _source_check(root: Path, refs: Iterable[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for ref in refs:
        if not isinstance(ref, dict):
            errors.append("source reference is not an object")
            continue
        path_value = ref.get("source_path")
        expected = ref.get("source_sha256")
        if not isinstance(path_value, str) or not isinstance(expected, str):
            errors.append("source reference is incomplete")
            continue
        path = (root / path_value).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError:
            errors.append(f"source escapes repository: {path_value}")
            continue
        try:
            path = _safe_relative_path(root, path_value, "source path")
        except PtmReadinessError as exc:
            errors.append(str(exc))
            continue
        if not path.exists() or file_sha256(path) != expected:
            errors.append(f"source digest drift: {path_value}")
    return errors


def _dependency_cycle(items: list[dict[str, Any]]) -> bool:
    graph = {str(item.get("dependency_id")): [str(x) for x in item.get("depends_on", [])] for item in items}
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(child) for child in graph.get(node, [])):
            return True
        visiting.remove(node); visited.add(node)
        return False
    return any(visit(node) for node in graph)


def _waiver_errors(item: dict[str, Any], *, objective_id: str, package_id: str | None, task_id: str, root: Path, registry: dict[str, Any] | None, observed_at: str, policy: dict[str, Any] | None) -> list[str]:
    waiver = item.get("waiver")
    if not isinstance(waiver, dict):
        return ["waiver record missing"]
    required = ("waiver_id", "granting_authority", "scope", "reason", "granted_at", "expires_at", "source_ref", "source_digest", "authority_registry_id", "authority_registry_version", "authority_registry_digest")
    errors = [f"waiver missing {key}" for key in required if not waiver.get(key)]
    try:
        if waiver.get("expires_at") and _parse_time(waiver["expires_at"]) <= _parse_time(item["observed_at"]):
            errors.append("waiver expired")
        _parse_time(waiver.get("granted_at", ""))
    except PtmReadinessError:
        errors.append("waiver timestamp invalid")
    scope = waiver.get("scope") or {}
    if scope.get("objective_id") != objective_id or scope.get("task_id") != task_id or (package_id is not None and scope.get("package_id") != package_id):
        errors.append("waiver scope does not match objective or task")
    source_ref = waiver.get("source_ref")
    if not isinstance(waiver.get("source_digest"), str) or not re.fullmatch(r"[a-f0-9]{64}", waiver.get("source_digest", "")):
        errors.append("waiver source digest invalid")
    if isinstance(source_ref, dict) and waiver.get("source_digest") != source_ref.get("source_sha256"):
        errors.append("waiver source digest does not match source reference")
    errors.extend(_source_check(root, [source_ref] if isinstance(source_ref, dict) else []))
    if registry is None:
        errors.append("waiver authority registry unavailable")
    else:
        from .ptm_waiver_authority import validate_waiver_authority
        errors.extend(validate_waiver_authority(registry, waiver, objective_id=objective_id, package_id=package_id, task_id=task_id, observed_at=observed_at))
    if policy is not None:
        from .ptm_policy import evaluate_evidence
        waiver_evidence = dict(item)
        waiver_evidence.update(waiver)
        errors.extend(evaluate_evidence(policy, waiver_evidence, evidence_class="waiver", observed_at=observed_at))
    return errors


def _existing_resolution(root: Path, replay_key: str) -> dict[str, Any] | None:
    directory = root / READINESS_ROOT
    if not directory.exists():
        return None
    for path in directory.glob("*.json"):
        if path.is_symlink():
            raise PtmReadinessError(f"symlinked readiness record rejected: {path.as_posix()}")
        record = _load_json(path)
        if record.get("replay_idempotency_key") == replay_key:
            validate_readiness_record(record, root=root)
            return record
    return None


def validate_readiness_record(record: dict[str, Any], *, root: Path | None = None) -> dict[str, Any]:
    required = ("resolution_id", "schema_version", "objective_id", "task_id", "dependency_results", "gate_checks", "readiness_state", "source_references", "source_digests", "source_high_watermark", "evaluator_identity", "freshness_policy_id", "freshness_policy_version", "freshness_policy_digest", "waiver_authority_registry_id", "waiver_authority_registry_version", "waiver_authority_registry_digest", "evaluated_at", "expires_at", "waiver_references", "conflicts", "warnings", "replay_idempotency_key", "failure_reason", "ledger_event_reference", "projection_path", "projection_digest")
    missing = [key for key in required if key not in record]
    if missing:
        raise PtmReadinessError("readiness record missing: " + ", ".join(missing))
    if record["schema_version"] != SCHEMA_VERSION or record["readiness_state"] not in READINESS_STATES:
        raise PtmReadinessError("readiness schema or state invalid")
    if not isinstance(record["dependency_results"], list) or not isinstance(record["gate_checks"], list) or not isinstance(record["source_references"], list):
        raise PtmReadinessError("readiness collections are invalid")
    if any(item.get("state") not in DEPENDENCY_STATES for item in record["dependency_results"]):
        raise PtmReadinessError("dependency state invalid")
    if any(item.get("state") not in GATE_STATES for item in record["gate_checks"]):
        raise PtmReadinessError("gate state invalid")
    _parse_time(record["evaluated_at"]); _parse_time(record["expires_at"])
    if record["freshness_policy_digest"] is not None and (not isinstance(record["freshness_policy_digest"], str) or not re.fullmatch(r"[a-f0-9]{64}", record["freshness_policy_digest"])):
        raise PtmReadinessError("freshness policy digest invalid")
    unsigned = dict(record); unsigned["projection_digest"] = None
    if record["projection_digest"] != digest(unsigned):
        raise PtmReadinessError("readiness projection digest invalid")
    if root is not None and record.get("projection_path"):
        expected = _safe_relative_path(Path(root).resolve(), record["projection_path"], "projection_path")
        if not expected.exists():
            raise PtmReadinessError("readiness projection path does not exist")
    return record


@dataclass(frozen=True)
class ReadinessResolution:
    record: dict[str, Any]

    @property
    def readiness_state(self) -> str:
        return self.record["readiness_state"]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.record)


class PtmProductionReadinessResolver:
    """The PTM-owned resolver; consumers may read its result but not recalculate it."""

    def __init__(self, root: Path, *, freshness_policy: dict[str, Any] | None = None, freshness_seconds: int | None = None, freshness_policy_id: str | None = None, freshness_policy_digest: str | None = None, waiver_registry: dict[str, Any] | None = None, evaluator_identity: str = "ptm.production-readiness-resolver@1.0.0") -> None:
        self.root = Path(root).resolve()
        self.freshness_policy = freshness_policy
        self.freshness_seconds = freshness_seconds
        self.freshness_policy_id = freshness_policy_id
        self.freshness_policy_digest = freshness_policy_digest
        self.waiver_registry = waiver_registry
        self.evaluator_identity = evaluator_identity

    def resolve_engineering_readiness(self, *, objective_id: str, enabling_project_id: str | None, task_or_package_id: str, source_high_watermark: str, observed_at: str, repository_root: Path | None = None) -> ReadinessResolution:
        objective = _require_id(objective_id, "objective_id")
        task = _require_id(task_or_package_id, "task_or_package_id")
        lock_name = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{objective}_{task}")
        lock_path = _safe_relative_path(self.root, (READINESS_ROOT / f".locks/{lock_name}").as_posix(), "readiness lock path")
        _exclusive_directory_lock(lock_path)
        try:
            return self._resolve_engineering_readiness_locked(
                objective_id=objective_id,
                enabling_project_id=enabling_project_id,
                task_or_package_id=task_or_package_id,
                source_high_watermark=source_high_watermark,
                observed_at=observed_at,
                repository_root=repository_root,
            )
        finally:
            _release_directory_lock(lock_path)

    def _resolve_engineering_readiness_locked(self, *, objective_id: str, enabling_project_id: str | None, task_or_package_id: str, source_high_watermark: str, observed_at: str, repository_root: Path | None = None) -> ReadinessResolution:
        objective_id = _require_id(objective_id, "objective_id")
        task_id = _require_id(task_or_package_id, "task_or_package_id")
        _parse_time(observed_at)
        policy = self.freshness_policy
        policy_error = None
        if policy is None and self.freshness_seconds is None:
            try:
                from .ptm_policy import load_freshness_policy
                policy = load_freshness_policy(self.root, observed_at=observed_at)
            except PtmReadinessError as exc:
                policy_error = str(exc)
        elif policy is None:
            policy = {"policy_id": self.freshness_policy_id, "policy_version": "test", "policy_digest": self.freshness_policy_digest, "readiness_resolution_maximum_age_seconds": self.freshness_seconds, "allowed_clock_skew_seconds": 120, "evidence_classes": {"accepted_dependency_completion": {"maximum_age_seconds": None, "requires_explicit_expiry": False}, "readiness_gate": {"maximum_age_seconds": self.freshness_seconds, "requires_explicit_expiry": False}, "waiver": {"maximum_age_seconds": 86400, "requires_explicit_expiry": True}}}
        policy_valid = policy is not None and policy_error is None
        registry = self.waiver_registry
        registry_error = None
        if registry is None:
            try:
                from .ptm_waiver_authority import load_waiver_registry
                registry = load_waiver_registry(self.root, observed_at=observed_at)
            except PtmReadinessError as exc:
                registry_error = str(exc)
        policy_identity = {"id": policy.get("policy_id") if policy else None, "version": policy.get("policy_version") if policy else None, "digest": policy.get("policy_digest") if policy else None}
        registry_identity = {"id": registry.get("registry_id") if registry else None, "version": registry.get("registry_version") if registry else None, "digest": registry.get("registry_digest") if registry else None}
        replay_key = digest({"objective_id": objective_id, "enabling_project_id": enabling_project_id, "task_id": task_id, "source_high_watermark": source_high_watermark, "observed_at": observed_at, "policy": policy_identity, "registry": registry_identity, "schema": SCHEMA_VERSION})
        prior = _existing_resolution(self.root, replay_key)
        if prior is not None:
            return ReadinessResolution(prior)
        events = _load_events(self.root)
        source_events = [e for e in events if e["event_type"] != "schedule.readiness_changed" and (e["aggregate_id"] == task_id or e["payload"].get("task_id") == task_id)]
        source_events.sort(key=lambda e: (e["stream_id"], int(e["sequence_number"])))
        warnings: list[str] = []
        conflicts: list[str] = []
        failure: str | None = None
        payload: dict[str, Any] = {}
        if not source_events:
            readiness = "unknown"; failure = "missing canonical PTM dependency/readiness record"; warnings.append(failure)
        else:
            latest = max(source_events, key=lambda e: (e["recorded_at"], int(e["sequence_number"])))
            if source_high_watermark != latest["event_id"]:
                readiness = "blocked"; failure = "source high-watermark mismatch"; warnings.append(failure)
            else:
                payload = latest["payload"]
                if payload.get("objective_id") != objective_id:
                    readiness = "blocked"; failure = "objective identity mismatch"; warnings.append(failure)
                elif enabling_project_id is not None and payload.get("enabling_project_id") != enabling_project_id:
                    readiness = "blocked"; failure = "enabling project identity mismatch"; warnings.append(failure)
                else:
                    dependencies = list(payload.get("dependencies") or [])
                    gates = list(payload.get("gate_checks") or [])
                    if not dependencies: warnings.append("required dependency evidence is absent")
                    if not gates: warnings.append("required gate evidence is absent")
                    for dep in dependencies:
                        if dep.get("state") not in DEPENDENCY_STATES: conflicts.append(f"invalid dependency state: {dep.get('dependency_id')}")
                        if dep.get("objective_id") and dep.get("objective_id") != objective_id: conflicts.append(f"dependency objective mismatch: {dep.get('dependency_id')}")
                        if dep.get("task_id") and dep.get("task_id") != task_id: conflicts.append(f"dependency task mismatch: {dep.get('dependency_id')}")
                        if payload.get("package_id") is not None and dep.get("package_id") and dep.get("package_id") != payload.get("package_id"): conflicts.append(f"dependency package mismatch: {dep.get('dependency_id')}")
                        if dep.get("state") == "waived":
                            errors = _waiver_errors(dep, objective_id=objective_id, package_id=payload.get("package_id"), task_id=task_id, root=self.root, registry=registry, observed_at=observed_at, policy=policy)
                            conflicts.extend(errors)
                    for gate in gates:
                        if gate.get("state") not in GATE_STATES: conflicts.append(f"invalid gate state: {gate.get('name')}")
                    if policy is not None:
                        from .ptm_policy import evaluate_evidence
                        for evidence in dependencies:
                            evidence_class = evidence.get("evidence_class") or ("waiver" if evidence.get("state") == "waived" else "accepted_dependency_completion")
                            if evidence.get("state") != "waived":
                                conflicts.extend(evaluate_evidence(policy, evidence, evidence_class=evidence_class, observed_at=observed_at))
                        for evidence in gates:
                            conflicts.extend(evaluate_evidence(policy, evidence, evidence_class=evidence.get("evidence_class", "readiness_gate"), observed_at=observed_at))
                    conflicts.extend(str(x) for x in payload.get("conflicts") or [])
                    if _dependency_cycle(dependencies):
                        conflicts.append("dependency cycle detected")
                    warnings.extend(str(x) for x in payload.get("warnings") or [])
                    source_errors = _source_check(self.root, list(payload.get("source_references") or []))
                    warnings.extend(source_errors)
                    conflicts.extend(source_errors)
                    all_expiries = [x.get("expires_at") for x in dependencies + gates if x.get("expires_at")]
                    freshness_age = policy.get("readiness_resolution_maximum_age_seconds") if policy else 0
                    freshness_expiry = _parse_time(observed_at) + timedelta(seconds=freshness_age)
                    expiry = min([_parse_time(x) for x in all_expiries] + [freshness_expiry])
                    if _parse_time(observed_at) >= expiry: conflicts.append("readiness evidence is expired")
                    if not policy_valid:
                        warnings.append(policy_error or "freshness policy unavailable")
                        failure = policy_error or "freshness policy unavailable"
                        readiness = "unknown"
                    elif conflicts or len({x.get("dependency_id") for x in dependencies}) != len(dependencies): readiness = "blocked"
                    elif any(x.get("state") == "unknown" for x in dependencies): readiness = "unknown"
                    elif any(x.get("state") == "unsatisfied" for x in dependencies): readiness = "not_ready"
                    elif any(x.get("state") == "fail" for x in gates): readiness = "blocked"
                    elif dependencies and gates and all(x.get("state") in {"satisfied", "waived"} for x in dependencies) and all(x.get("state") in {"pass", "waived"} for x in gates): readiness = "waived" if all(x.get("state") == "waived" for x in dependencies + gates) else "ready"
                    else: readiness = "unknown"
                    if conflicts and failure is None: failure = "; ".join(conflicts[:3])
        if not source_events:
            expiry = _parse_time(observed_at) + timedelta(seconds=policy.get("readiness_resolution_maximum_age_seconds", 0) if policy else 0)
        else:
            policy_expiry = _parse_time(observed_at) + timedelta(seconds=policy.get("readiness_resolution_maximum_age_seconds", 0) if policy else 0)
            expiry = min([_parse_time(x["expires_at"]) for x in (list(payload.get("dependencies") or []) + list(payload.get("gate_checks") or [])) if x.get("expires_at")] + [policy_expiry])
        record: dict[str, Any] = {
            "resolution_id": new_ptm_id("res"), "schema_version": SCHEMA_VERSION,
            "objective_id": objective_id, "campaign_id": payload.get("campaign_id"), "package_id": payload.get("package_id"),
            "task_id": task_id, "enabling_project_id": enabling_project_id,
            "dependency_results": list(payload.get("dependencies") or []), "gate_checks": list(payload.get("gate_checks") or []),
            "readiness_state": readiness, "source_references": list(payload.get("source_references") or []),
            "source_digests": {str(x.get("source_path")): x.get("source_sha256") for x in payload.get("source_references") or []},
            "source_high_watermark": source_high_watermark, "evaluator_identity": self.evaluator_identity,
            "freshness_policy_id": policy.get("policy_id") if policy else None, "freshness_policy_version": policy.get("policy_version") if policy else None, "freshness_policy_digest": policy.get("policy_digest") if policy else None,
            "waiver_authority_registry_id": registry.get("registry_id") if registry else None, "waiver_authority_registry_version": registry.get("registry_version") if registry else None, "waiver_authority_registry_digest": registry.get("registry_digest") if registry else None,
            "evaluated_at": observed_at, "expires_at": _iso(expiry), "waiver_references": [x.get("waiver") for x in payload.get("dependencies") or [] if x.get("waiver")],
            "conflicts": sorted(set(conflicts)), "warnings": sorted(set(warnings)), "replay_idempotency_key": replay_key,
            "failure_reason": failure, "ledger_event_reference": None, "projection_path": None, "projection_digest": None,
        }
        event = append_ptm_event(self.root, event_type="schedule.readiness_changed", aggregate_type="task", aggregate_id=task_id, stream_id=f"readiness:{task_id}", actor_ref=self.evaluator_identity, authority_refs=["PTM/orchestrator"], source_refs=record["source_references"], payload_schema=SCHEMA_VERSION, payload={"resolution_id": record["resolution_id"], "objective_id": objective_id, "task_id": task_id, "readiness_state": readiness, "replay_idempotency_key": replay_key}, idempotency_key=f"readiness:{replay_key}", occurred_at=observed_at)
        record["ledger_event_reference"] = event["event_id"]
        record["projection_path"] = (READINESS_ROOT / f"{record['resolution_id']}.json").as_posix()
        _safe_relative_path(self.root, record["projection_path"], "projection path")
        unsigned = dict(record); unsigned["projection_digest"] = None
        record["projection_digest"] = digest(unsigned)
        validate_readiness_record(record)
        _write_create_once(self.root / record["projection_path"], record)
        return ReadinessResolution(record)


def read_readiness(root: Path, resolution_id: str) -> dict[str, Any]:
    _require_id(resolution_id, "resolution_id")
    path = _safe_relative_path(Path(root).resolve(), (READINESS_ROOT / f"{resolution_id}.json").as_posix(), "resolution path")
    record = _load_json(path)
    return validate_readiness_record(record, root=Path(root).resolve())


def cli(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="estate ptm-readiness")
    parser.add_argument("action", choices=("resolve", "read", "validate"))
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("json", "report"), default="json")
    parser.add_argument("--objective-id")
    parser.add_argument("--enabling-project-id")
    parser.add_argument("--task-id")
    parser.add_argument("--source-high-watermark")
    parser.add_argument("--observed-at")
    parser.add_argument("--resolution-id")
    parser.add_argument("--record")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.action == "resolve":
            required = (args.objective_id, args.task_id, args.source_high_watermark, args.observed_at)
            if any(x is None for x in required):
                parser.error("resolve requires --objective-id, --task-id, --source-high-watermark, and --observed-at")
            value = PtmProductionReadinessResolver(root).resolve_engineering_readiness(objective_id=args.objective_id, enabling_project_id=args.enabling_project_id, task_or_package_id=args.task_id, source_high_watermark=args.source_high_watermark, observed_at=args.observed_at)
        elif args.action == "read":
            if not args.resolution_id: parser.error("read requires --resolution-id")
            value = read_readiness(root, args.resolution_id)
        else:
            if not args.record: parser.error("validate requires --record")
            candidate = Path(args.record).resolve()
            try:
                relative = candidate.relative_to(root).as_posix()
            except ValueError as exc:
                raise PtmReadinessError("record path escapes repository") from exc
            record_path = _safe_relative_path(root, relative, "record path")
            value = validate_readiness_record(_load_json(record_path), root=root)
    except PtmReadinessError as exc:
        print(f"PTM readiness validation failed: {exc}", file=__import__("sys").stderr)
        return 2
    rendered = value.to_dict() if isinstance(value, ReadinessResolution) else value
    if args.format == "report" and not args.json:
        print(f"PTM readiness: {rendered.get('readiness_state')} | task={rendered.get('task_id')} | resolution={rendered.get('resolution_id')}")
        if rendered.get("failure_reason"): print(f"Failure: {rendered['failure_reason']}")
        for warning in rendered.get("warnings", []): print(f"Warning: {warning}")
    else:
        print(json.dumps(rendered, indent=2, sort_keys=True))
    return 0
