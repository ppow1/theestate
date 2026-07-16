from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from estate.core.ptm_pilot_projection import PilotSelection, build_pilot_projection, normalized_json, reviewer_report
from estate.core.ptm_read_only_adapters import PtmReadOnlyAdapterRuntime


def _write(root: Path, relative: str, body: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _selection(root: Path, *, observed_at: datetime | None = None, conflict: bool = False) -> PilotSelection:
    sources = {
        "portfolio": ["collaboration/work_packages/campaigns/demo.md"],
        "intake": [f"collaboration/parking_lot/PL-{number}.md" for number in range(1, 6)],
        "work_package": ["collaboration/work_packages/pending/WP-1.md", "collaboration/work_packages/pending/WP-2.md"],
        "dispatch": ["collaboration/evidence/pilot_dispatch.md"],
        "validation": ["collaboration/evidence/pilot_validation.md"],
        "acceptance": ["collaboration/evidence/pilot_acceptance.md"],
    }
    for role, paths in sources.items():
        for index, relative in enumerate(paths):
            status = "completed" if conflict and role == "work_package" and index == 0 else ("pending" if role == "work_package" else ("campaigns" if role == "portfolio" else "current"))
            _write(root, relative, f"# WP-{index + 10} private-token-SHOULD-NOT-LEAK\nStatus: {status}\nOwner: Chief Architect\n")
    runtime = PtmReadOnlyAdapterRuntime(root, observed_at=observed_at)
    return PilotSelection(
        portfolio=runtime.adapt("work_package_source_adapter", sources["portfolio"]),
        intake=runtime.adapt("parking_lot_source_adapter", sources["intake"]),
        work_package=runtime.adapt("work_package_source_adapter", sources["work_package"]),
        dispatch=runtime.adapt("dispatch_source_adapter", sources["dispatch"]),
        validation=runtime.adapt("validation_source_adapter", sources["validation"]),
        acceptance=runtime.adapt("acceptance_source_adapter", sources["acceptance"]),
    )


def test_repeated_rebuild_is_byte_equivalent_and_has_complete_provenance(tmp_path: Path) -> None:
    selection = _selection(tmp_path)

    first = build_pilot_projection(selection)
    second = build_pilot_projection(selection)

    assert normalized_json(first) == normalized_json(second)
    assert first["selection"] == {"portfolio": 1, "intake": 5, "work_package": 2, "dispatch": 1, "validation": 1, "acceptance": 1}
    assert all(item["source"]["sha256"] for item in first["items"])
    assert all(all(item["field_provenance"].values()) for item in first["items"])
    assert first["canonical_event_log_persisted"] is False
    assert first["mutation_allowed"] is False


def test_unknown_metrics_warning_coverage_and_private_payload_protection(tmp_path: Path) -> None:
    projection = build_pilot_projection(_selection(tmp_path))
    machine = normalized_json(projection)
    report = reviewer_report(projection)

    assert projection["metrics"]["cycle_time_seconds"]["value"] is None
    assert projection["metrics"]["blocked_duration_seconds"]["value"] is None
    assert all(item["metrics"]["cycle_time_seconds"]["value"] is None for item in projection["items"])
    assert "private-token-SHOULD-NOT-LEAK" not in machine
    assert "private-token-SHOULD-NOT-LEAK" not in report
    assert "acceptance or Gate decision" in report
    json.loads(machine)


def test_stale_missing_and_conflicting_sources_fail_closed(tmp_path: Path) -> None:
    selection = _selection(tmp_path, conflict=True)
    missing = "collaboration/evidence/missing_validation.md"
    runtime = PtmReadOnlyAdapterRuntime(tmp_path)
    selection = PilotSelection(**{**selection.__dict__, "validation": runtime.adapt("validation_source_adapter", [missing])})
    stale_time = datetime.now(timezone.utc) + timedelta(days=31)
    stale_runtime = PtmReadOnlyAdapterRuntime(tmp_path, observed_at=stale_time)
    selection = PilotSelection(**{**selection.__dict__, "acceptance": stale_runtime.adapt("acceptance_source_adapter", ["collaboration/evidence/pilot_acceptance.md"])})

    projection = build_pilot_projection(selection)
    warned_sources = {warning.get("source") for warning in projection["warnings"]}

    assert "collaboration/work_packages/pending/WP-1.md" in warned_sources
    assert missing in warned_sources
    assert "collaboration/evidence/pilot_acceptance.md" in warned_sources
    assert projection["metrics"]["audit_completeness"]["value"]["complete_records"] < 11


def test_projection_and_adapters_do_not_write_sources(tmp_path: Path, monkeypatch) -> None:
    selection = _selection(tmp_path)
    before = {path.relative_to(tmp_path): (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode) for path in tmp_path.rglob("*.md")}

    def reject_write(*args, **kwargs):
        raise AssertionError("projection attempted a write")

    monkeypatch.setattr(Path, "write_text", reject_write)
    monkeypatch.setattr(Path, "write_bytes", reject_write)
    build_pilot_projection(selection)
    after = {path.relative_to(tmp_path): (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode) for path in tmp_path.rglob("*.md")}

    assert before == after


def test_wrong_selection_cardinality_is_explicit_not_inferred(tmp_path: Path) -> None:
    selection = _selection(tmp_path)
    selection = PilotSelection(**{**selection.__dict__, "intake": selection.intake[:4]})

    projection = build_pilot_projection(selection)

    assert {warning["code"] for warning in projection["warnings"]} == {"selection_cardinality"}
    assert projection["selection"]["intake"] == 4
