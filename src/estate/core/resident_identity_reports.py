"""Auditable resident identity-composition campaign reports."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_gateway import ACTIVE_RESIDENT_MODELS, chat_completion
from estate.core.resident_identity_composition import compose_resident_identity

REPORT_DIR = Path("runtime/reports/resident_personality_fidelity")
QUESTIONS = [
    "What should I do first when the Estate feels noisy?",
    "Explain your boundary in one paragraph.",
]


def _root(root=None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def covered_residents() -> list[str]:
    """Return every current single-resident gateway surface exactly once."""
    return list(dict.fromkeys(ACTIVE_RESIDENT_MODELS.values()))


def build_identity_composition_matrix(root=None, *, write: bool = False) -> dict[str, Any]:
    rootp = _root(root)
    rows = []
    for resident in covered_residents():
        comp = compose_resident_identity(resident, surface_id="open-webui-single-resident", root=rootp, task_instructions="campaign identity audit")
        rows.append({
            "resident_id": resident,
            "identity_hash": comp.get("identity_version_or_source_hash"),
            "failed_closed": comp.get("failed_closed"),
            "layers": [layer.get("layer") for layer in comp.get("included_context_layers", [])],
            "source_artifacts": comp.get("source_artifacts", []),
            "missing_sources": comp.get("missing_sources", []),
            "detected_contradictions": comp.get("detected_contradictions", []),
        })
    payload = {"schema_version": "resident_personality_fidelity_matrix.v1", "generated_at": _now(), "covered_residents": covered_residents(), "rows": rows}
    if write:
        out = rootp / REPORT_DIR / "identity_composition_matrix.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def build_conversational_differentiation_report(root=None, *, write: bool = False) -> dict[str, Any]:
    rootp = _root(root)
    responses = []
    for question in QUESTIONS:
        for resident in covered_residents():
            code, body = chat_completion({"model": f"estate/{resident}", "messages": [{"role": "user", "content": question}], "metadata": {"session_id": f"campaign08-{resident}-{abs(hash(question))}"}}, root=rootp)
            text = body.get("choices", [{}])[0].get("message", {}).get("content", "") if code == 200 else ""
            responses.append({"question": question, "resident_id": resident, "http_status": code, "response": text, "recognition_cues": _recognition_cues(resident)})
    payload = {"schema_version": "resident_personality_fidelity_differentiation.v1", "generated_at": _now(), "questions": QUESTIONS, "responses": responses, "blind_recognition_review": [{"sample_id": f"blind-{i+1:03d}", "response": r["response"], "expected_resident_id": r["resident_id"], "review_instruction": "Hide expected_resident_id before Steward review."} for i, r in enumerate(responses)], "remaining_issues": ["Deterministic fallback responses are intentionally terse when no local LLM is available; source-loaded prompts and fallback phrasing still remain resident-specific."]}
    if write:
        out = rootp / REPORT_DIR / "conversational_differentiation_report.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _recognition_cues(resident: str) -> list[str]:
    return {
        "alfred": ["Chief of Staff", "routing", "Steward attention"],
        "helen": ["workforce", "onboarding", "health"],
        "ingrid": ["privacy", "classification", "boundary"],
        "grace": ["sequence", "checkpoints", "handoffs"],
        "evelyn": ["private Steward counsel", "reflection", "relationship layer"],
        "eleanor": ["provenance", "institutional memory", "ledger"],
        "marie": ["evidence", "research", "uncertainty"],
        "judy": ["legal risk", "compliance", "contracts"],
    }.get(resident, [])
