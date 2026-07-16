from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from estate.core.ptm_read_only_adapters import AdapterState, Freshness, PtmReadOnlyAdapterRuntime


def _source(root: Path, relative: str, body: str | bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body.encode() if isinstance(body, str) else body)
    return path


def test_valid_record_is_deterministic_provenanced_and_read_only(tmp_path: Path) -> None:
    relative = "collaboration/work_packages/pending/WP-9000_demo.md"
    path = _source(tmp_path, relative, "# WP-9000 — Demo\nStatus: pending\nOwner: Chief Architect\nDependencies: WP-1\nEvidence: `collaboration/reports/evidence.md`\n")
    before = (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode)
    runtime = PtmReadOnlyAdapterRuntime(tmp_path)

    first = runtime.adapt("work_package_source_adapter", [relative])[0]
    second = runtime.adapt("work_package_source_adapter", [relative])[0]

    assert json.dumps(first.normalized(), sort_keys=True) == json.dumps(second.normalized(), sort_keys=True)
    assert first.state is AdapterState.AVAILABLE
    assert first.source.sha256 and first.field_provenance
    assert before == (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode)


def test_missing_malformed_conflicting_and_stale_sources(tmp_path: Path) -> None:
    malformed = "collaboration/parking_lot/malformed.md"
    conflict = "collaboration/work_packages/pending/WP-9.md"
    stale = "collaboration/parking_lot/PL-9-stale.md"
    _source(tmp_path, malformed, b"\xff")
    _source(tmp_path, conflict, "# WP-9\nStatus: completed\n")
    stale_path = _source(tmp_path, stale, "# PL-9 stale\n")
    observed = datetime.fromtimestamp(stale_path.stat().st_mtime, timezone.utc) + timedelta(days=31)
    runtime = PtmReadOnlyAdapterRuntime(tmp_path, observed_at=observed)

    assert runtime.adapt("parking_lot_source_adapter", ["collaboration/parking_lot/missing.md"])[0].state is AdapterState.UNAVAILABLE
    assert runtime.adapt("parking_lot_source_adapter", [malformed])[0].state is AdapterState.UNAVAILABLE
    assert runtime.adapt("work_package_source_adapter", [conflict])[0].state is AdapterState.CONFLICT
    assert runtime.adapt("parking_lot_source_adapter", [stale])[0].freshness is Freshness.STALE


def test_escaping_unallowlisted_and_oversized_inputs_fail_closed(tmp_path: Path) -> None:
    relative = "collaboration/parking_lot/PL-9.md"
    _source(tmp_path, relative, "# PL-9\n" * 10)
    runtime = PtmReadOnlyAdapterRuntime(tmp_path, max_file_bytes=10, max_records=1)

    with pytest.raises(ValueError, match="escapes"):
        runtime.adapt("parking_lot_source_adapter", ["../secret"])
    with pytest.raises(ValueError, match="allowlisted"):
        runtime.adapt("parking_lot_source_adapter", ["docs/secret.md"])
    outside = tmp_path.parent / "outside"
    outside.mkdir(exist_ok=True)
    (tmp_path / "collaboration" / "parking_lot" / "link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        runtime.adapt("parking_lot_source_adapter", ["collaboration/parking_lot/link/secret.md"])
    oversized = runtime.adapt("parking_lot_source_adapter", [relative])[0]
    assert oversized.state is AdapterState.UNAVAILABLE
    assert "ValueError" in oversized.adapter_warnings[0]
    with pytest.raises(ValueError, match="bounded read"):
        runtime.adapt("parking_lot_source_adapter", [relative, "collaboration/parking_lot/PL-10.md"])


def test_pilot_evidence_adapters_require_named_allowlisted_files(tmp_path: Path) -> None:
    paths = {
        "dispatch_source_adapter": "collaboration/evidence/demo_dispatch.md",
        "validation_source_adapter": "collaboration/evidence/demo_validation.md",
        "acceptance_source_adapter": "collaboration/evidence/demo_acceptance.md",
    }
    for adapter, relative in paths.items():
        _source(tmp_path, relative, f"# WP-9 {adapter}\n")
        assert PtmReadOnlyAdapterRuntime(tmp_path).adapt(adapter, [relative])[0].source.path == relative

    with pytest.raises(ValueError, match="dispatch-named"):
        PtmReadOnlyAdapterRuntime(tmp_path).adapt("dispatch_source_adapter", ["collaboration/evidence/other.md"])
