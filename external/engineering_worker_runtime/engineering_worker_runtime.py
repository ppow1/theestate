"""Generic, bounded Engineering worker runtime.

The runtime owns technical interpretation, planning, provider selection,
provider invocation, work-product validation, and truthful disposition.  It
does not own Dispatch authority or institutional acceptance.
"""
from __future__ import annotations

import argparse
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LIFECYCLE_STATES = {
    "received", "planned", "executing", "validation_required",
    "completed", "blocked", "failed",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _write(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _commission(package: dict[str, Any]) -> dict[str, Any]:
    commission = package.get("commission")
    if not isinstance(commission, dict):
        raise ValueError("generic commission is required")
    result = dict(commission)
    result["commission_id"] = _text(result.get("commission_id"), "commission_id")
    result["requested_outcome"] = _text(result.get("requested_outcome"), "requested_outcome")
    criteria = result.get("acceptance_criteria")
    if not isinstance(criteria, list) or not criteria:
        raise ValueError("acceptance_criteria must be a non-empty list")
    result["acceptance_criteria"] = criteria
    result["required_capabilities"] = [str(x) for x in result.get("required_capabilities") or []]
    result["allowed_providers"] = [str(x) for x in result.get("allowed_providers") or []]
    result["constraints"] = [str(x) for x in result.get("constraints") or []]
    return result


def _capability_catalog(package: dict[str, Any]) -> list[dict[str, Any]]:
    catalog = package.get("provider_catalog")
    if not isinstance(catalog, list):
        raise ValueError("provider_catalog is required")
    providers = []
    for provider in catalog:
        if not isinstance(provider, dict):
            continue
        provider_id = provider.get("provider_id")
        capabilities = provider.get("capabilities")
        if isinstance(provider_id, str) and isinstance(capabilities, list):
            providers.append(dict(provider))
    return providers


def _select_provider(commission: dict[str, Any], providers: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    required = set(commission["required_capabilities"])
    allowed = set(commission["allowed_providers"])
    candidates = []
    for provider in providers:
        if allowed and provider["provider_id"] not in allowed:
            continue
        if provider.get("status") not in {None, "implemented", "operationally_validated", "institutionalized"}:
            continue
        if not required.issubset(set(provider.get("capabilities") or [])):
            continue
        if provider.get("available", True) is False:
            continue
        candidates.append(provider)
    if not candidates:
        return None, "No registered available provider declares all required capabilities."
    candidates.sort(key=lambda item: (bool(item.get("requires_network")), str(item["provider_id"])))
    selected = candidates[0]
    return selected, "Selected the first available registered provider whose declared capabilities cover the commission requirements."


def _invoke_provider(provider: dict[str, Any], commission: dict[str, Any], plan: dict[str, Any], evidence: Path, attempt: int) -> dict[str, Any]:
    """Invoke the explicitly registered deterministic local adapter.

    Other provider kinds fail closed until a concrete adapter is registered.
    The deterministic adapter is useful for bounded local artifact work and is
    intentionally named in its receipt; it is never presented as an external
    model or image-generation service.
    """
    adapter_kind = provider.get("adapter_kind") or provider.get("implementation_kind")
    if adapter_kind != "deterministic_local_artifact":
        return {
            "status": "blocked",
            "provider_id": provider["provider_id"],
            "attempt": attempt,
            "reason": f"No concrete adapter is registered for implementation kind '{adapter_kind}'.",
            "artifacts": [],
        }
    artifact = evidence / f"work_product_attempt_{attempt}.json"
    payload = {
        "schema_version": "estate.engineering.work-product.v1",
        "commission_id": commission["commission_id"],
        "requested_outcome": commission["requested_outcome"],
        "artifact_type": commission.get("artifact_type", "structured_work_product"),
        "produced_by": provider["provider_id"],
        "attempt": attempt,
        "plan_id": plan["plan_id"],
    }
    _write(artifact, payload)
    receipt = {
        "schema_version": "estate.engineering.provider-receipt.v1",
        "receipt_id": f"provider-receipt-{commission['commission_id']}-{attempt}",
        "provider_id": provider["provider_id"],
        "adapter_kind": adapter_kind,
        "commission_id": commission["commission_id"],
        "attempt": attempt,
        "status": "succeeded",
        "artifact_references": [str(artifact)],
        "artifact_sha256": {_sha256(artifact): str(artifact)},
        "created_at": utc_now(),
    }
    receipt_path = _write(evidence / f"provider_receipt_attempt_{attempt}.json", receipt)
    return {
        "status": "succeeded",
        "provider_id": provider["provider_id"],
        "attempt": attempt,
        "receipt_path": str(receipt_path),
        "receipt": receipt,
        "artifacts": [str(artifact)],
    }


def _criterion_passes(criterion: Any, provider_result: dict[str, Any], commission: dict[str, Any]) -> tuple[bool, str]:
    if isinstance(criterion, dict):
        kind = criterion.get("kind")
        if kind == "artifact_exists":
            ok = bool(provider_result.get("artifacts")) and all(Path(p).is_file() for p in provider_result["artifacts"])
            return ok, "artifact exists" if ok else "required artifact is missing"
        if kind == "provider_receipt":
            ok = Path(str(provider_result.get("receipt_path", ""))).is_file()
            return ok, "provider receipt exists" if ok else "provider receipt is missing"
        if kind == "artifact_type":
            expected = str(criterion.get("value"))
            actual = commission.get("artifact_type")
            return actual == expected, f"artifact_type={actual!r}, expected {expected!r}"
        if kind == "artifact_contains":
            needle = str(criterion.get("value"))
            text = " ".join(Path(p).read_text(encoding="utf-8") for p in provider_result.get("artifacts", []) if Path(p).is_file())
            return needle in text, f"artifact contains requested value: {needle!r}"
        return False, f"unsupported acceptance criterion kind: {kind!r}"
    if criterion == "artifact_exists":
        return _criterion_passes({"kind": "artifact_exists"}, provider_result, commission)
    if criterion == "provider_receipt":
        return _criterion_passes({"kind": "provider_receipt"}, provider_result, commission)
    return False, f"acceptance criterion requires a typed validator: {criterion!r}"


def run_worker(package: dict[str, Any], worktree: Path, evidence: Path) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    commission = _commission(package)
    providers = _capability_catalog(package)
    max_retries = int(package.get("retry_policy", {}).get("max_retries", 0))
    status = "received"
    events.append({"state": status, "at": utc_now(), "commission_id": commission["commission_id"]})
    plan = {
        "schema_version": "estate.engineering.execution-plan.v1",
        "plan_id": f"eng-plan-{commission['commission_id']}",
        "commission_id": commission["commission_id"],
        "interpreted_commission": {"requested_outcome": commission["requested_outcome"], "required_capabilities": commission["required_capabilities"], "artifact_type": commission.get("artifact_type")},
        "steps": ["interpret_commission", "select_provider", "invoke_provider", "validate_work_product"],
        "created_at": utc_now(),
    }
    plan_path = _write(evidence / "execution_plan.json", plan)
    status = "planned"
    events.append({"state": status, "at": utc_now(), "plan_path": str(plan_path)})
    provider, rationale = _select_provider(commission, providers)
    if provider is None:
        result = {"schema_version": "estate.engineering.worker-result.v2", "status": "blocked", "final_disposition": "blocked", "reason": rationale, "events": events, "plan": plan, "plan_path": str(plan_path), "commission": commission, "provider_selection": {"provider_id": None, "selection_rationale": rationale}, "provider_result": {"status": "blocked", "reason": rationale, "artifacts": []}, "validation": {"passed": False, "checks": [], "reason": "provider selection did not produce an eligible provider"}, "retry_history": [], "authority": {"engineering_validated": False, "institutional_acceptance_granted": False}}
        return _write(evidence / "worker_result.json", result) and result
    selection = {"provider_id": provider["provider_id"], "capabilities": provider.get("capabilities", []), "selection_rationale": rationale, "selected_at": utc_now()}
    retry_history: list[dict[str, Any]] = []
    for attempt in range(1, max_retries + 2):
        status = "executing"
        events.append({"state": status, "at": utc_now(), "attempt": attempt, "provider_id": provider["provider_id"]})
        provider_result = _invoke_provider(provider, commission, plan, evidence, attempt)
        status = "validation_required"
        events.append({"state": status, "at": utc_now(), "attempt": attempt})
        checks = []
        for criterion in commission["acceptance_criteria"]:
            passed, detail = _criterion_passes(criterion, provider_result, commission)
            checks.append({"criterion": criterion, "passed": passed, "detail": detail})
        validation = {"validation_id": f"eng-validation-{commission['commission_id']}-{attempt}", "commission_id": commission["commission_id"], "attempt": attempt, "checks": checks, "passed": all(item["passed"] for item in checks), "validated_at": utc_now()}
        _write(evidence / f"validation_attempt_{attempt}.json", validation)
        if provider_result.get("status") == "succeeded" and validation["passed"]:
            status = "completed"
            events.append({"state": status, "at": utc_now(), "attempt": attempt})
            result = {"schema_version": "estate.engineering.worker-result.v2", "status": status, "final_disposition": "completed", "commission": commission, "plan": plan, "plan_path": str(plan_path), "provider_selection": selection, "provider_result": provider_result, "validation": validation, "retry_history": retry_history, "events": events, "authority": {"engineering_validated": True, "institutional_acceptance_granted": False}}
            return _write(evidence / "worker_result.json", result) and result
        retry_history.append({"attempt": attempt, "provider_status": provider_result.get("status"), "validation_passed": validation["passed"], "reason": provider_result.get("reason") or "commission-specific validation failed"})
        if attempt <= max_retries:
            continue
        final = "blocked" if provider_result.get("status") == "blocked" else "failed"
        events.append({"state": final, "at": utc_now(), "attempt": attempt})
        result = {"schema_version": "estate.engineering.worker-result.v2", "status": final, "final_disposition": final, "commission": commission, "plan": plan, "plan_path": str(plan_path), "provider_selection": selection, "provider_result": provider_result, "validation": validation, "retry_history": retry_history, "events": events, "authority": {"engineering_validated": False, "institutional_acceptance_granted": False}}
        return _write(evidence / "worker_result.json", result) and result
    raise RuntimeError("worker lifecycle exhausted without disposition")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generic bounded Engineering Worker Runtime")
    parser.add_argument("--package", required=True)
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args()
    package = _read(Path(args.package))
    worktree = Path(args.worktree)
    evidence = Path(args.evidence)
    worktree.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    result = run_worker(package, worktree, evidence)
    print(json.dumps({"status": result["status"], "commission_id": result.get("commission", {}).get("commission_id")}, sort_keys=True))
    return 0 if result["status"] in {"completed", "blocked", "failed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
