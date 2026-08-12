"""Bounded, idempotent consultation projection.

SQL remains authoritative.  A publisher is an optional asynchronous sink;
GitHub outages therefore leave the local projection pending/failed without
blocking consultation reads or Comms8 processing.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from estate.core.consultation_store import ConsultationStore


DEFAULT_PROJECTION_DIR = Path(r"A:\theestate-data\consultations\projections")


def render_root(store: ConsultationStore, root_id: int | str) -> str:
    root = store.get_root(root_id)
    turns = store.get_turn_range(root_id)
    attempts = {item.request_id: item for turn in turns for item in store.transport_attempts(turn.logical_consultation_id)}
    lines = [
        f"# Estate Consultation {root.root_logical_id}",
        "",
        f"- Status: `{turns[-1].status if turns else root.status}`",
        f"- Objective: {root.objective or ''}",
        f"- PTM project: {root.ptm_project_id or 'standalone'}",
        f"- Tags: {', '.join(root.tags) or 'none'}",
        "",
        "## Compact summary",
        "",
        root.compact_summary or store.compact_summary(root_id)["summary"],
        "",
        "## Turns",
        "",
    ]
    for turn in turns:
        lines.extend([f"### {turn.logical_consultation_id}", "", f"- Question: {turn.question or ''}", f"- Status: `{turn.status}`", f"- Comms8 request: `{turn.ec8_request_id or 'none'}`"])
        if turn.prior_context_summary:
            lines.extend([f"- Prior summary: {turn.prior_context_summary[:1200]}"])
        if turn.response:
            content = turn.response.get("content", "") if isinstance(turn.response, dict) else str(turn.response)
            lines.extend(["", "Response:", "", content[:4000]])
        if turn.observed_result or turn.validation_evidence:
            lines.extend(["", f"Validation observed: {turn.observed_result or ''}", f"Validation evidence: {turn.validation_evidence or ''}"])
        turn_attempts = [item for item in attempts.values() if item.logical_consultation_id == turn.logical_consultation_id]
        if turn_attempts:
            lines.extend(["", "Transport attempts:"])
            for attempt in turn_attempts:
                lines.append(f"- {attempt.attempt_number}: `{attempt.request_id}` `{attempt.status}`" + (f" supersedes `{attempt.supersedes_request_id}`" if attempt.supersedes_request_id else ""))
        execution_requests = store.execution_requests(turn.logical_consultation_id)
        if execution_requests:
            lines.extend(["", "Execution requests:"])
            for execution in execution_requests:
                lines.append(f"- `{execution.execution_request_id}` capability=`{execution.required_capability or 'unspecified'}` provider=`{execution.provider_id or 'unselected'}` status=`{execution.status}`")
                for attempt in store.execution_attempts(execution.execution_request_id):
                    lines.append(f"  - attempt {attempt.attempt_number}: `{attempt.execution_attempt_id}` `{attempt.status}` provider=`{attempt.provider_id}`")
                if execution.result_reference:
                    lines.append(f"  - result: `{execution.result_reference}`")
        lines.append("")
    root_escalations = [item for item in store.escalations() if item.root_logical_id == root.root_logical_id]
    if root_escalations:
        lines.extend(["## Steward escalations", ""])
        for escalation in root_escalations:
            snapshot = escalation.snapshot if isinstance(escalation.snapshot, dict) else {}
            lines.extend([
                f"### `{escalation.escalation_id}`",
                "",
                f"- Current turn: `{escalation.current_logical_id}`",
                f"- Reason: `{escalation.reason}`",
                f"- State: `{escalation.state}`",
                f"- Overall operational confidence: `{snapshot.get('overall_confidence', 'not supplied')}`",
                f"- Unknowns: {len(snapshot.get('unknowns', [])) if isinstance(snapshot.get('unknowns'), list) else 0}",
                f"- Decision requested: {_bounded(snapshot.get('decision_requested'))}",
                "",
            ])
    return "\n".join(lines).rstrip() + "\n"


def _bounded(value: object, limit: int = 1000) -> str:
    return str(value or "")[:limit]


class ConsultationProjection:
    def __init__(self, store: ConsultationStore, *, directory: str | Path = DEFAULT_PROJECTION_DIR,
                 publisher: Callable[[str, str], str] | None = None) -> None:
        self.store = store
        self.directory = Path(directory)
        self.publisher = publisher

    def project(self, root_id: int | str) -> dict[str, str]:
        root = self.store.get_root(root_id)
        content = render_root(self.store, root_id)
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"consultation-{root.root_logical_id.replace('.', '-')}.md"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)
        reference = str(path)
        status = "pending"
        if self.publisher:
            try:
                reference = self.publisher(root.root_logical_id, content)
                status = "published"
            except Exception:
                status = "failed"
        self.store.set_github_projection(root.logical_consultation_id, status, reference)
        return {"root_consultation_id": root.root_logical_id, "status": status, "reference": reference, "path": str(path)}
