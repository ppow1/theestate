from estate.core.ingrid_boundary import (
    can_read,
    can_write,
    export_allowed,
    load_boundary_matrix,
    validate_public_summary,
)


def test_boundary_matrix_covers_required_artifact_classes():
    matrix = load_boundary_matrix()
    classes = {item["artifact_class"] for item in matrix["artifact_classes"]}
    assert {
        "resident_identity_records",
        "public_interaction_layers",
        "private_interaction_layers",
        "working_journals",
        "reflection_records",
        "continuity_artifacts",
        "workforce_assessments",
        "cognitive_health_records",
        "personnel_onboarding_records",
        "mailbox_communication_content",
        "connector_derived_data",
        "protected_private_local_character_material",
        "provider_prompts_outputs",
        "office_task_board_summaries",
    } <= classes
    for boundary in matrix["artifact_classes"]:
        for field in (
            "owner",
            "minimum_classification",
            "allowed_readers",
            "allowed_writers",
            "permitted_summaries",
            "export_restrictions",
            "retention_expectations",
            "audit_requirements",
            "connector_requirements",
            "escalation_path",
        ):
            assert boundary[field]


def test_minimum_necessary_access_is_enforced():
    matrix = load_boundary_matrix()
    assert can_read(matrix, "workforce_assessments", "helen", "Restricted")
    assert not can_read(matrix, "workforce_assessments", "grace", "Restricted")
    assert not can_read(matrix, "workforce_assessments", "helen", "Estate Internal")
    assert can_write(matrix, "office_task_board_summaries", "grace", "Estate Internal")
    assert not can_write(matrix, "office_task_board_summaries", "helen", "Restricted")


def test_public_summary_rejects_private_to_public_leakage():
    matrix = load_boundary_matrix()
    result = validate_public_summary(
        matrix,
        [
            {"classification": "Public", "text": "Ingrid owns boundary review."},
            {
                "classification": "Local Only",
                "text": "protected private character source phrase",
                "protected_fragments": ["private character source phrase"],
            },
        ],
        "Public update: Ingrid owns boundary review. private character source phrase",
    )
    assert not result["valid"]
    assert result["violations"]


def test_public_summary_accepts_sanitized_boundary_notice():
    matrix = load_boundary_matrix()
    result = validate_public_summary(
        matrix,
        [{"classification": "Local Only", "text": "never summarize this protected note"}],
        "This resident has protected private-source material outside Estate Proper; consult the Steward.",
    )
    assert result["valid"]


def test_export_restrictions_block_public_export_of_non_public_sources():
    assert export_allowed("Public", "Public", public_destination=True)
    assert not export_allowed("Estate Internal", "Public", public_destination=True)
    assert not export_allowed("Restricted", "Estate Internal")
    assert export_allowed("Restricted", "Steward Only")
