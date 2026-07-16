"""Ephemeral, read-only PTM pilot projection.

The projection consumes only the frozen read-only adapter envelopes.  It never
opens a source itself and never persists a ledger, registry, or report.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Mapping

from estate.core.ptm_read_only_adapters import AdapterRecord, AdapterState, Freshness, PtmReadOnlyAdapterRuntime


PROJECTION_VERSION = "ptm-prod-pilot-v1"
_ROLES = ("portfolio", "intake", "work_package", "dispatch", "validation", "acceptance")
_EXPECTED = {"portfolio": 1, "intake": 5, "work_package": 2, "dispatch": 1, "validation": 1, "acceptance": 1}
DEFAULT_PILOT_PATHS = {
    "portfolio": ("collaboration/work_packages/campaigns/ptm-production/PTM-PROD-01_Read_Only_Discovery_and_Projection_Pilot.md",),
    "intake": (
        "collaboration/parking_lot/PL-0030-estate-performance-presentation-office.md",
        "collaboration/parking_lot/PL-0031-visual-estate-campaigns-11-20-motion-performance-canon.md",
        "collaboration/parking_lot/PL-0032-estate-engineering-provider-qualification-suite.md",
        "collaboration/parking_lot/PL-0033-stream-deck-operational-details-view.md",
        "collaboration/parking_lot/PL-0034-campaign-level-codex-execution-model.md",
    ),
    "work_package": (
        "collaboration/work_packages/pending/PROD-PTM-001A_Read_Only_Adapter_Runtime_Foundation.md",
        "collaboration/work_packages/pending/PROD-PTM-001C_Read_Only_Pilot_Projection.md",
    ),
    "dispatch": ("collaboration/work_packages/completions/DISPATCH-PTM-001_completion_receipt.md",),
    "validation": ("collaboration/work_packages/pending/TEST-PTM-001A_Automated_replay_gate_and_policy_validation_plan.md",),
    "acceptance": ("collaboration/work_packages/pending/TEST-PTM-001B_End_to_end_acceptance_validation_package_draft.md",),
}


@dataclass(frozen=True)
class PilotSelection:
    """A bounded selection of adapter records, grouped by projection role."""

    portfolio: tuple[AdapterRecord, ...]
    intake: tuple[AdapterRecord, ...]
    work_package: tuple[AdapterRecord, ...]
    dispatch: tuple[AdapterRecord, ...]
    validation: tuple[AdapterRecord, ...]
    acceptance: tuple[AdapterRecord, ...]


def build_repository_pilot(repository_root: str) -> dict[str, object]:
    """Rebuild the repository-safe default pilot through the frozen adapters."""
    runtime = PtmReadOnlyAdapterRuntime(repository_root)
    selection = PilotSelection(
        portfolio=runtime.adapt("work_package_source_adapter", DEFAULT_PILOT_PATHS["portfolio"]),
        intake=runtime.adapt("parking_lot_source_adapter", DEFAULT_PILOT_PATHS["intake"]),
        work_package=runtime.adapt("work_package_source_adapter", DEFAULT_PILOT_PATHS["work_package"]),
        dispatch=runtime.adapt("dispatch_source_adapter", DEFAULT_PILOT_PATHS["dispatch"]),
        validation=runtime.adapt("validation_source_adapter", DEFAULT_PILOT_PATHS["validation"]),
        acceptance=runtime.adapt("acceptance_source_adapter", DEFAULT_PILOT_PATHS["acceptance"]),
    )
    return build_pilot_projection(selection)


def build_pilot_projection(selection: PilotSelection) -> dict[str, object]:
    """Build a deterministic projection without reading or writing any files."""
    grouped = {role: tuple(getattr(selection, role)) for role in _ROLES}
    warnings: list[dict[str, str]] = []
    for role, records in grouped.items():
        if len(records) != _EXPECTED[role]:
            warnings.append({"code": "selection_cardinality", "role": role, "detail": f"expected {_EXPECTED[role]}, received {len(records)}"})

    items = []
    for role in _ROLES:
        for record in sorted(grouped[role], key=lambda value: value.source.path):
            items.append(_project_record(role, record, warnings))

    complete = sum(1 for item in items if item["metrics"]["audit_completeness"]["value"] is True)
    audit_value = {"complete_records": complete, "total_records": len(items)} if items else None
    return {
        "schema_version": PROJECTION_VERSION,
        "projection_kind": "ephemeral_read_only_pilot",
        "authority_notice": "Source records remain authoritative; this projection infers no acceptance or Gate decision.",
        "mutation_allowed": False,
        "canonical_event_log_persisted": False,
        "selection": {role: len(grouped[role]) for role in _ROLES},
        "metrics": {
            "cycle_time_seconds": {"value": None, "warning": "unknown: frozen adapter records do not expose authoritative lifecycle timestamps"},
            "audit_completeness": {"value": audit_value, "method": "available, current, hashed, and field-provenanced adapter records"},
            "blocked_duration_seconds": {"value": None, "warning": "unknown: frozen adapter records do not expose authoritative blocked intervals"},
        },
        "items": items,
        "warnings": sorted(warnings, key=lambda value: (value["code"], value.get("role", ""), value.get("source", ""), value["detail"])),
    }


def _project_record(role: str, record: AdapterRecord, warnings: list[dict[str, str]]) -> dict[str, object]:
    provenance = {field: path for field, path in record.field_provenance}
    reasons = list(record.adapter_warnings)
    if record.state is not AdapterState.AVAILABLE:
        reasons.append(f"adapter state is {record.state.value}")
    if record.freshness is not Freshness.CURRENT:
        reasons.append(f"freshness is {record.freshness.value}")
    if not record.source.sha256:
        reasons.append("source hash is unavailable")
    if not record.field_provenance:
        reasons.append("field provenance is unavailable")
    audit_complete = not reasons
    for reason in sorted(set(reasons)):
        warnings.append({"code": "source_warning", "role": role, "source": record.source.path, "detail": reason})
    return {
        "role": role,
        "source": {"path": record.source.path, "sha256": record.source.sha256, "byte_length": record.source.byte_length},
        "adapter": {"name": record.adapter_name, "version": record.adapter_version, "state": record.state.value, "freshness": record.freshness.value},
        # Only bounded metadata from the adapter envelope is projected.  Source
        # bodies, private payloads, and arbitrary extracted text are excluded.
        "record": {"id": record.extracted_id, "status": record.extracted_status, "private_payloads_included": False},
        "field_provenance": {key: provenance.get(key) for key in ("extracted_id", "extracted_status")},
        "metrics": {
            "cycle_time_seconds": {"value": None, "warning": "unknown: no authoritative start/completion interval"},
            "audit_completeness": {"value": audit_complete, "warnings": sorted(set(reasons))},
            "blocked_duration_seconds": {"value": None, "warning": "unknown: no authoritative blocked interval"},
        },
    }


def normalized_json(projection: Mapping[str, object]) -> str:
    """Return byte-stable, normalized machine-readable output."""
    return json.dumps(projection, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def reviewer_report(projection: Mapping[str, object]) -> str:
    """Render a concise report containing metadata only, never source payloads."""
    selection = projection["selection"]
    metrics = projection["metrics"]
    lines = [
        "# PTM read-only pilot projection report",
        "",
        str(projection["authority_notice"]),
        "",
        "## Selection",
        "",
        "| Role | Records |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {role.replace('_', ' ')} | {selection[role]} |" for role in _ROLES)
    audit = metrics["audit_completeness"]["value"]
    audit_text = "unknown" if audit is None else f"{audit['complete_records']}/{audit['total_records']} complete"
    lines.extend(["", "## Metrics", "", "- Cycle time: **unknown** (authoritative lifecycle timestamps unavailable).", f"- Audit completeness: **{audit_text}**.", "- Blocked duration: **unknown** (authoritative blocked intervals unavailable).", "", "## Provenance and warnings", ""])
    for item in projection["items"]:
        source = item["source"]
        lines.append(f"- `{item['role']}` `{source['path']}` — SHA-256 `{source['sha256'] or 'unknown'}`; state `{item['adapter']['state']}`; freshness `{item['adapter']['freshness']}`.")
    if projection["warnings"]:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- `{warning['code']}`: {warning['detail']}" for warning in projection["warnings"])
    else:
        lines.append("- No adapter or selection warnings.")
    lines.extend(["", "This report is an ephemeral projection. It records no event, mutates no source, and makes no acceptance or Gate decision.", ""])
    return "\n".join(lines)
