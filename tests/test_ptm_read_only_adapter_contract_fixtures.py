from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil

import pytest

from estate.core.ptm_read_only_adapters import AdapterState, Freshness, PtmReadOnlyAdapterRuntime


FIXTURES = Path(__file__).parent / "fixtures" / "ptm_read_only_adapters"


def _sandbox(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    shutil.copytree(FIXTURES, root)
    return root


def _snapshot(root: Path) -> tuple[tuple[str, bytes, int, int], ...]:
    return tuple(
        (path.relative_to(root).as_posix(), path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )


def test_sanitized_source_slices_are_deterministic_private_safe_and_read_only(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    before = _snapshot(root)
    runtime = PtmReadOnlyAdapterRuntime(root)
    requests = {
        "parking_lot_source_adapter": ["collaboration/parking_lot/PL-9100-sanitized.md"],
        "work_package_source_adapter": [
            "collaboration/work_packages/pending/WP-9101-partial.md",
            "collaboration/work_packages/pending/WP-9102-conflict.md",
            "collaboration/work_packages/pending/WP-9103-invalid-hash.md",
        ],
        "dispatch_source_adapter": ["collaboration/evidence/WP-9104_dispatch.md"],
        "validation_source_adapter": ["collaboration/evidence/WP-9104_validation.md"],
        "acceptance_source_adapter": ["collaboration/evidence/WP-9104_acceptance.md"],
    }

    first = {name: [record.normalized() for record in runtime.adapt(name, paths)] for name, paths in requests.items()}
    second = {name: [record.normalized() for record in runtime.adapt(name, paths)] for name, paths in requests.items()}

    assert first == second
    assert before == _snapshot(root), "adapter must make zero writes or in-place normalizations"
    serialized = json.dumps(first, sort_keys=True)
    assert "private@example.invalid" not in serialized
    assert "collaboration/private/resident-note.md" not in serialized
    assert first["work_package_source_adapter"][0]["extracted_status"] == "pending"
    assert first["work_package_source_adapter"][1]["state"] == "conflict"
    assert [item["source"]["path"] for item in first["work_package_source_adapter"]] == sorted(requests["work_package_source_adapter"])


def test_hash_is_calculated_from_bytes_not_an_untrusted_source_field(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    relative = "collaboration/work_packages/pending/WP-9103-invalid-hash.md"
    expected = hashlib.sha256((root / relative).read_bytes()).hexdigest()

    record = PtmReadOnlyAdapterRuntime(root).adapt("work_package_source_adapter", [relative])[0]

    assert record.source.sha256 == expected
    assert record.source.sha256 != "0" * 64
    assert "0000000000000000" not in json.dumps(record.normalized(), sort_keys=True)


def test_absent_stale_escape_and_size_bounds_fail_closed_without_writes(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    source = root / "collaboration/parking_lot/PL-9100-sanitized.md"
    observed = datetime.fromtimestamp(source.stat().st_mtime, timezone.utc) + timedelta(days=31)
    before = _snapshot(root)
    runtime = PtmReadOnlyAdapterRuntime(root, max_file_bytes=32, max_records=1, observed_at=observed)

    missing = runtime.adapt("parking_lot_source_adapter", ["collaboration/parking_lot/absent.md"])[0]
    oversized = runtime.adapt("parking_lot_source_adapter", [source.relative_to(root).as_posix()])[0]
    assert missing.state is AdapterState.UNAVAILABLE
    assert oversized.state is AdapterState.UNAVAILABLE
    assert any("bounded file size" in warning for warning in oversized.adapter_warnings)
    with pytest.raises(ValueError, match="escapes"):
        runtime.adapt("parking_lot_source_adapter", ["../outside.md"])
    with pytest.raises(ValueError, match="bounded read"):
        runtime.adapt("parking_lot_source_adapter", ["collaboration/parking_lot/a.md", "collaboration/parking_lot/b.md"])
    assert before == _snapshot(root)

    current = PtmReadOnlyAdapterRuntime(root, observed_at=observed).adapt(
        "parking_lot_source_adapter", [source.relative_to(root).as_posix()]
    )[0]
    assert current.freshness is Freshness.STALE
    assert before == _snapshot(root)


def test_symlink_escape_is_rejected_before_read(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("private material", encoding="utf-8")
    link = root / "collaboration/parking_lot/PL-escape.md"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    with pytest.raises(ValueError, match="symlink"):
        PtmReadOnlyAdapterRuntime(root).adapt("parking_lot_source_adapter", [link.relative_to(root).as_posix()])
