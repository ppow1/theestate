import json

import pytest

from estate.core.reflection_worker_request import (
    build_reflection_worker_request,
    write_reflection_worker_request,
)


def test_build_request_preserves_authority_boundaries():
    payload = build_reflection_worker_request(
        request_id="RWR-0001",
        worker="employee.12",
        office="Chief Architect",
        assignment="Inspect the continuity package for structural defects.",
        authority_reference="Steward authorization 2026-07-18",
        deliverables=["findings report"],
        constraints=["do not approve renewal"],
        related_artifacts=["operations/continuity/example.md"],
    )

    assert payload["request_id"] == "RWR-0001"
    assert payload["destination"] == "employee.12"
    assert payload["status"] == "open"
    assert payload["requires_ack"] is True
    assert payload["ack_status"] == "pending"
    assert payload["authority_boundaries"] == {
        "may_approve_renewal": False,
        "may_grant_constitutional_authority": False,
        "may_control_operational_queues": False,
        "may_execute_providers": False,
        "may_merge_code": False,
    }


def test_build_request_rejects_missing_required_input():
    with pytest.raises(ValueError, match="missing required input"):
        build_reflection_worker_request(
            request_id="",
            worker="employee.12",
            office="Chief Architect",
            assignment="Inspect package.",
            authority_reference="Steward authorization",
        )


def test_write_request_is_idempotent_for_equivalent_payload(tmp_path):
    kwargs = {
        "request_id": "RWR-0002",
        "worker": "employee.12",
        "office": "Chief Architect",
        "assignment": "Check the execution handoff.",
        "authority_reference": "Steward authorization 2026-07-18",
        "deliverables": ["handoff findings"],
        "root": tmp_path,
    }

    first = write_reflection_worker_request(**kwargs)
    original = json.loads(first.read_text(encoding="utf-8"))
    second = write_reflection_worker_request(**kwargs)
    replay = json.loads(second.read_text(encoding="utf-8"))

    assert second == first
    assert replay == original


def test_write_request_rejects_conflicting_duplicate(tmp_path):
    first = write_reflection_worker_request(
        request_id="RWR-0003",
        worker="employee.12",
        office="Chief Architect",
        assignment="Inspect package A.",
        authority_reference="Steward authorization",
        root=tmp_path,
    )

    assert first.exists()
    with pytest.raises(ValueError, match="conflicting request already exists"):
        write_reflection_worker_request(
            request_id="RWR-0003",
            worker="employee.12",
            office="Chief Architect",
            assignment="Inspect package B.",
            authority_reference="Steward authorization",
            root=tmp_path,
        )


def test_write_request_uses_deterministic_message_path(tmp_path):
    path = write_reflection_worker_request(
        request_id="RWR 004 / Alpha",
        worker="employee.12",
        office="Chief Architect",
        assignment="Inspect naming behavior.",
        authority_reference="Steward authorization",
        root=tmp_path,
    )

    assert path == (
        tmp_path
        / "collaboration"
        / "messages"
        / "reflection_worker_request_rwr_004_alpha.json"
    )
