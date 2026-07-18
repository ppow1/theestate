import pytest

from estate.core import (
    create_reflection_workflow,
    load_reflection_workflow,
    reflection_workflow_status,
    transition_reflection_workflow,
    workflow_path,
)


def _create_direct(tmp_path):
    return create_reflection_workflow(
        run_id="REF-2026-0001",
        office="Chief Architect",
        officeholder="Chief Architect",
        current_implementation="Chief Architect 5",
        mailbox_id="5",
        initiation_type="direct_reflection",
        authority_reference="Steward directive 2026-07-18",
        actor="Steward",
        reason="Operational degradation