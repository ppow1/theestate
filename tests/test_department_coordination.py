import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.department_coordination import (
    DepartmentAuthority,
    DepartmentCoordination,
    DepartmentDependency,
    DepartmentRequest,
    ServiceLevelExpectation,
)


def test_department_coordination_models_requests_dependencies_and_acknowledgements():
    coordination = DepartmentCoordination.create(
        coordination_id="coord-model",
        campaign_id="camp-0633",
        title="Launch coordination",
        authority=DepartmentAuthority(approved_by="Steward", approved_at="2026-07-10T00:00:00Z", allowed_departments=["Engineering", "Operations"]),
        requests=[
            DepartmentRequest.create(
                request_id="eng-build",
                department="Engineering",
                title="Implement governed change",
                requested_by="Operations Manager",
                commitment="Provide implementation receipt",
                service_level=ServiceLevelExpectation(response_due="2026-07-11", completion_due="2026-07-12", priority="High"),
            ),
            DepartmentRequest.create(
                request_id="ops-release",
                department="Operations",
                title="Coordinate release",
                requested_by="Operations Manager",
                commitment="Sequence release after Engineering",
                dependencies=[DepartmentDependency("dep-eng", "eng-build", "Engineering implementation must complete")],
            ),
        ],
    )

    payload = coordination.to_dict()
    restored = DepartmentCoordination.from_dict(payload)

    assert restored.coordination_id == "coord-model"
    assert restored.request("eng-build").acknowledgement_state == "Pending"
    assert restored.request("ops-release").dependencies[0].state == "Waiting"


def test_department_coordination_rejects_unknown_dependency_and_boundary_escape():
    with pytest.raises(ValueError):
        DepartmentCoordination.create(
            campaign_id="camp-0633",
            title="Bad dependency",
            authority=DepartmentAuthority(approved_by="Steward", approved_at="2026-07-10T00:00:00Z"),
            requests=[DepartmentRequest.create(department="Engineering", title="Bad", requested_by="Ops", commitment="Nope", dependencies=[DepartmentDependency("dep-missing", "missing", "Missing")])],
        ).to_dict()

    with pytest.raises(PermissionError):
        DepartmentCoordination.create(
            campaign_id="camp-0633",
            title="Boundary check",
            authority=DepartmentAuthority(approved_by="Steward", approved_at="2026-07-10T00:00:00Z", allowed_departments=["Engineering"]),
            requests=[DepartmentRequest.create(department="Workforce", title="Outside", requested_by="Ops", commitment="Nope")],
        ).to_dict()


def test_request_ready_requires_acknowledgement_released_dependencies_and_clear_blockers():
    request = DepartmentRequest.create(
        department="Character Architecture",
        title="Review character boundary",
        requested_by="Operations Manager",
        commitment="Return architecture note",
        dependencies=[DepartmentDependency("dep-upstream", "eng-build", "Engineering done")],
    )

    request.acknowledgement_state = "Acknowledged"
    assert request.ready is False
    request.dependencies[0].state = "Released"
    assert request.ready is True
