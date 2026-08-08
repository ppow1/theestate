"""Bounded autonomous reason -> execute -> observe -> reason orchestration.

This module consumes the accepted consultation and execution-provider
contracts.  It accepts only a structured reasoning decision for execution;
ordinary prose never becomes an execution request.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import PurePosixPath
from typing import Any, Callable

from estate.core.consultation_execution import ConsultationExecutionRouter
from estate.core.consultation_store import ConsultationStore


DECISIONS = {
    "INFORMATION_ONLY",
    "EXECUTION_RECOMMENDED",
    "STEWARD_DECISION_REQUIRED",
    "MORE_REASONING_REQUIRED",
}
EVALUATIONS = {
    "VALIDATED",
    "VALIDATION_FAILED",
    "FAILED_WITH_NEW_EVIDENCE",
    "ASSUMPTION_INVALID",
    "STEWARD_DECISION_REQUIRED",
}


@dataclass(frozen=True)
class ReasoningDecision:
    classification: str
    rationale: str
    execution: dict[str, Any] | None = None
    evidence_request: dict[str, Any] | None = None


def parse_reasoning_envelope(response: Any) -> dict[str, Any] | None:
    """Parse only a complete structured response envelope, never prose."""
    if not isinstance(response, dict):
        return None
    if isinstance(response.get("structured_decision"), dict):
        return {"reasoning": response.get("content") or response.get("reasoning") or "", "decision": response["structured_decision"]}
    content = response.get("content")
    if not isinstance(content, str):
        return None
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or not isinstance(parsed.get("decision"), dict) or not isinstance(parsed.get("reasoning"), str):
        return None
    # ChatGPT has used the descriptive contract name in live responses.  It
    # is the same provider-neutral object; normalize it before validation.
    decision = parsed["decision"]
    if "execution" not in decision and isinstance(decision.get("execution_specification"), dict):
        decision = dict(decision)
        decision["execution"] = decision.pop("execution_specification")
        parsed = dict(parsed)
        parsed["decision"] = decision
    return parsed


def classify_reasoning_response(response: Any) -> ReasoningDecision:
    """Accept a structured model decision and fail closed for prose."""
    envelope = parse_reasoning_envelope(response)
    if envelope is not None:
        response = envelope["decision"]
    if not isinstance(response, dict):
        return ReasoningDecision("INFORMATION_ONLY", "No structured execution decision was supplied.")
    classification = str(response.get("classification") or response.get("decision") or "").upper()
    if classification not in DECISIONS:
        raise ValueError("unsupported_reasoning_decision")
    evidence_request = response.get("evidence_request") if classification == "MORE_REASONING_REQUIRED" else None
    if evidence_request is not None:
        if not isinstance(evidence_request, dict):
            raise ValueError("evidence_request_must_be_object")
        required = ("objective", "required_capability", "allowed_scope", "prohibited_scope", "evidence_requirements")
        missing = [field for field in required if not evidence_request.get(field)]
        if not evidence_request.get("consultation_correlation") and not evidence_request.get("consultation_id"):
            missing.append("consultation_correlation")
        if missing:
            raise ValueError("evidence_request_missing:" + ",".join(missing))
        allowed_keys = {"objective", "evidence_type", "target", "required_capability", "allowed_scope", "prohibited_scope", "evidence_requirements", "consultation_correlation", "consultation_id", "preferred_provider", "read_only"}
        unknown = sorted(set(evidence_request) - allowed_keys)
        if unknown:
            raise ValueError("evidence_request_unknown_fields:" + ",".join(unknown))
        if not isinstance(evidence_request["allowed_scope"], list) or not evidence_request["allowed_scope"] or not isinstance(evidence_request["prohibited_scope"], list) or not evidence_request["prohibited_scope"]:
            raise ValueError("evidence_request_scope_must_be_bounded_lists")
        if any(str(item).strip() in {"", ".", "/", "\\"} for item in evidence_request["allowed_scope"]):
            raise ValueError("evidence_request_allowed_scope_unbounded")
        capability = str(evidence_request["required_capability"]).strip()
        if not capability or "codex" in capability.lower():
            raise ValueError("evidence_request_capability_must_be_provider_neutral")
        correlation = evidence_request.get("consultation_correlation") or evidence_request.get("consultation_id")
        if isinstance(correlation, dict):
            correlation = correlation.get("logical_consultation_id") or correlation.get("consultation_id")
        if not isinstance(correlation, str) or not correlation.strip():
            raise ValueError("evidence_request_consultation_correlation_invalid")
        evidence_request["consultation_id"] = correlation
        capability = str(evidence_request["required_capability"]).strip()
        target = str(evidence_request.get("target") or "")
        if capability not in {"repository_read", "filesystem_read", "test_inspection", "configuration_inspection", "software_engineering_readonly"}:
            evidence_type = str(evidence_request.get("evidence_type") or "").lower()
            if target.count("/") >= 1 and ("fixture" in evidence_type or "repository" in evidence_type or "read" in capability.lower()):
                evidence_request["required_capability"] = "filesystem_read"
            else:
                raise ValueError("evidence_request_capability_unknown")
        if target.count("/") >= 1 and not all("/" in str(item) or str(item) in {".", ".."} for item in evidence_request["allowed_scope"]):
            evidence_request["allowed_scope"] = [target.rsplit("/", 1)[0]]
        if not any("/" in str(item) for item in evidence_request["prohibited_scope"]):
            evidence_request["prohibited_scope"] = ["src", "runtime", ".git"]
    execution = response.get("execution")
    if classification == "EXECUTION_RECOMMENDED":
        if not isinstance(execution, dict):
            raise ValueError("execution_spec_required")
        required = ("objective", "required_capability", "allowed_scope", "prohibited_scope", "validation_criteria")
        missing = [field for field in required if not execution.get(field)]
        if not execution.get("evidence_requirements") and not execution.get("evidence_required"):
            missing.append("evidence_requirements")
        if not execution.get("consultation_correlation") and not execution.get("consultation_id"):
            missing.append("consultation_correlation")
        if missing:
            raise ValueError("execution_spec_missing:" + ",".join(missing))
        allowed_keys = {"objective", "required_capability", "allowed_scope", "write_scope", "prohibited_scope", "evidence_requirements", "evidence_required", "validation_criteria", "consultation_correlation", "consultation_id", "preferred_provider", "timeout", "budget", "ptm_reference", "tags", "dispatch_id", "authority_reference"}
        unknown = sorted(set(execution) - allowed_keys)
        if unknown:
            raise ValueError("execution_spec_unknown_fields:" + ",".join(unknown))
        allowed_scope = execution["allowed_scope"]
        prohibited_scope = execution["prohibited_scope"]
        if not isinstance(allowed_scope, list) or not allowed_scope or not isinstance(prohibited_scope, list) or not prohibited_scope:
            raise ValueError("execution_scope_must_be_bounded_lists")
        if any(str(item).strip() in {"", ".", "/", "\\"} for item in allowed_scope):
            raise ValueError("execution_allowed_scope_unbounded")
        if any(str(item).strip() in {"", ".", "/", "\\"} for item in prohibited_scope):
            raise ValueError("execution_prohibited_scope_invalid")
        scope_values = [str(item).strip() for item in (*allowed_scope, *prohibited_scope)]
        if any(item.lower().startswith(("read ", "modify ", "run ", "do not ")) for item in scope_values):
            raise ValueError("execution_scope_must_contain_bounded_paths")
        for allowed in allowed_scope:
            for prohibited in prohibited_scope:
                left, right = PurePosixPath(str(allowed).replace("\\", "/")), PurePosixPath(str(prohibited).replace("\\", "/"))
                if left == right or left in right.parents or right in left.parents:
                    raise ValueError("execution_scope_contradiction")
        capability = str(execution["required_capability"]).strip()
        if not capability or "codex" in capability.lower():
            raise ValueError("execution_capability_must_be_provider_neutral")
        if capability not in {"software_engineering_test", "repository_read", "software_engineering_readonly", "filesystem_write"}:
            scope_text = " ".join(str(item) for item in execution.get("allowed_scope", []))
            objective_text = str(execution.get("objective") or "")
            if "fixture" in (scope_text + " " + objective_text).lower() and any(token in (capability + " " + objective_text).lower() for token in ("write", "repair", "correct", "update")):
                execution["required_capability"] = "software_engineering_test"
            else:
                raise ValueError("execution_capability_unknown")
        write_intent = " ".join((str(execution.get("objective") or ""), *(str(item) for item in execution.get("evidence_requirements") or []))).lower()
        if any(token in write_intent for token in ("repair", "modify", "write", "update", "correct")) and not execution.get("write_scope"):
            raise ValueError("execution_spec_missing:write_scope")
        correlation = execution.get("consultation_correlation") or execution.get("consultation_id")
        if isinstance(correlation, dict):
            correlation = correlation.get("logical_consultation_id") or correlation.get("consultation_id")
        if not isinstance(correlation, str) or not correlation.strip():
            raise ValueError("execution_consultation_correlation_invalid")
        execution["consultation_id"] = correlation
        execution["evidence_required"] = execution.get("evidence_requirements") or execution.get("evidence_required")
    return ReasoningDecision(classification, str(response.get("rationale") or ""), execution, evidence_request)


class AutonomousReasonExecuteLoop:
    """Compose one bounded autonomous execution cycle."""

    def __init__(self, store: ConsultationStore, router: ConsultationExecutionRouter) -> None:
        self.store = store
        self.router = router

    def accept_reasoning(self, logical_consultation_id: str, response: Any) -> dict[str, Any]:
        decision = classify_reasoning_response(response)
        if decision.classification != "EXECUTION_RECOMMENDED":
            return {"status": decision.classification.lower(), "classification": decision.classification, "rationale": decision.rationale}
        execution = decision.execution or {}
        if execution["consultation_id"] != logical_consultation_id:
            raise ValueError("execution_consultation_mismatch")
        existing = self.store.execution_requests(logical_consultation_id)
        if existing:
            # Completed evidence is historical context, not an active
            # execution request.  A later materially distinct execution
            # recommendation must be allowed to create its own request.
            active = [item for item in existing if item.status in {"queued", "running", "accepted"}]
            if active:
                return {"status": "execution_requested", "classification": decision.classification, "execution_request_id": active[-1].execution_request_id, "idempotent": True}
        request = self.router.create_request(
            logical_consultation_id,
            required_capability=str(execution["required_capability"]),
            dispatch_id=str(execution.get("dispatch_id") or f"dispatch-{logical_consultation_id.replace('.', '-')}-execution"),
            prompt_source=str(execution["objective"]),
            classification="Estate Internal",
            read_scope_paths=sorted({str(item) for item in execution["allowed_scope"]} | {"docs/prompts"}),
            write_scope_paths=[str(item) for item in execution.get("write_scope") or []],
            blocked_scope_paths=[str(item) for item in execution["prohibited_scope"]],
            expected_outputs=[str(item) for item in execution.get("evidence_required") or []],
            validation_required=True,
            decision_reference=str(execution.get("authority_reference") or "consultation-bounded-acceptance"),
            preferred_provider=execution.get("preferred_provider"),
            metadata={
                "validation_criteria": execution["validation_criteria"],
                "evidence_required": execution["evidence_required"],
                "consultation_id": logical_consultation_id,
                "sandbox": "workspace-write" if execution.get("write_scope") else "read-only",
            },
        )
        return {"status": "execution_requested", "classification": decision.classification, "execution_request_id": request.adapter_request_id}

    def execute_and_observe(self, execution_request_id: str, evaluation: dict[str, Any]) -> dict[str, Any]:
        result = self.router.execute(execution_request_id)
        link = self.store.execution_request(execution_request_id)
        if not isinstance(evaluation, dict) or str(evaluation.get("classification") or "") not in EVALUATIONS:
            raise ValueError("unsupported_execution_evaluation")
        classification = str(evaluation["classification"])
        evidence = {
            "execution_request_id": execution_request_id,
            "execution_status": result.status,
            "provider_id": result.provider_id,
            "execution_attempts": [attempt.execution_attempt_id for attempt in self.store.execution_attempts(execution_request_id)],
            "provider_evidence": evaluation.get("evidence"),
            "result_reference": link.result_reference,
        }
        self.store.append_validation(
            link.logical_consultation_id,
            observed_result=classification,
            evidence=evidence,
            status="validating" if classification == "VALIDATED" else "continuation_required",
        )
        if classification in {"VALIDATION_FAILED", "FAILED_WITH_NEW_EVIDENCE", "ASSUMPTION_INVALID"}:
            continuation = self.router.continue_from_execution(
                link.logical_consultation_id,
                execution_request_id,
                question=str(evaluation.get("revised_question") or "Reassess the recommendation using the execution evidence."),
                continuation_reason=classification.lower(),
            )
            return {"status": "reasoning_continuation_required", "classification": classification, "continuation_id": continuation.logical_consultation_id, "execution_result": result.to_dict()}
        return {"status": classification.lower(), "classification": classification, "execution_result": result.to_dict()}

    def run_bounded_cycle(self, logical_consultation_id: str, reasoning_response: Any, evaluation: dict[str, Any]) -> dict[str, Any]:
        accepted = self.accept_reasoning(logical_consultation_id, reasoning_response)
        if accepted["status"] != "execution_requested":
            return accepted
        return self.execute_and_observe(accepted["execution_request_id"], evaluation)
