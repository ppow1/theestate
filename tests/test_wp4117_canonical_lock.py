import copy
import json
from pathlib import Path

import pytest

from estate.visual_bible.canonical_lock import (
    eligibility, validate_asset_manifest, validate_lock_record,
    validate_rollback, validate_transition,
)
from estate.visual_bible.validator import ValidationError

ROOT = Path(__file__).parents[1]
EXAMPLE = ROOT / "data/visual_bibles/residents/evelyn/internal/locks/evelyn_calibration_awaiting_steward_v1.json"


def load_example():
    return json.loads(EXAMPLE.read_text())


def test_evelyn_example_is_honestly_noncanonical_and_awaiting_evidence():
    record = load_example()
    validate_lock_record(record)
    result = eligibility(record)
    assert record["state"] == "candidate"
    assert record["steward_decision"]["explicit_approval"] is False
    assert result == {"recommendation": "eligible_for_steward_review", "may_grant_canonical": False, "diagnostics": []}


def test_canonical_cannot_be_granted_without_explicit_steward_evidence():
    record = load_example()
    record["state"] = "canonical"
    with pytest.raises(ValidationError, match="explicit Steward approval"):
        validate_lock_record(record)
    assert eligibility(record)["may_grant_canonical"] is False


def test_reserved_locations_do_not_satisfy_canonical_completeness():
    record = load_example()
    record["state"] = "canonical"
    record["steward_decision"] = {"explicit_approval": True, "authority": "Steward", "decision_id": "real-id-required", "decided_at": "2026-07-21T00:00:00Z", "evidence_ref": "review.json"}
    with pytest.raises(ValidationError, match="blocking findings|accepted evidence hashes|reserved assets"):
        validate_lock_record(record)


def test_present_asset_requires_real_file_and_matching_hash(tmp_path):
    manifest = load_example()["asset_completeness"]
    item = manifest["entries"][0]
    item.update(status="present", asset_id="A", path="missing.png", hash="sha256:" + "0" * 64)
    with pytest.raises(ValidationError, match="does not exist"):
        validate_asset_manifest(manifest, root=tmp_path)


def test_state_graph_rejects_skipping_steward_review():
    old = load_example()
    old["state"] = "exploratory"
    new = copy.deepcopy(old)
    new["state"] = "canonical"
    with pytest.raises(ValidationError, match="illegal"):
        validate_transition(old, new)


def test_rollback_is_forward_history_and_steward_only():
    valid = {"action": "rollback", "authority": "Steward", "explicit_request": True,
             "from_version": "2.0.0", "restore_version": "1.0.0", "new_version": "3.0.0",
             "reason": "Steward-requested restoration", "requested_at": "2026-07-21T00:00:00Z",
             "preserve_history": True, "delete_assets": False}
    validate_rollback(valid)
    valid["authority"] = "validator"
    with pytest.raises(ValidationError, match="Steward"):
        validate_rollback(valid)


def test_schema_declares_all_governed_states():
    schema = json.loads((ROOT / "data/schemas/visual_bible/canonical_lock/canonical_lock_record_v1.schema.json").read_text())
    assert schema["properties"]["state"]["enum"] == ["exploratory", "candidate", "preferred", "provisional", "canonical", "superseded", "rejected"]
