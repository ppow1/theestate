from estate.core.steward_awareness import (
    record_steward_interaction,
    generate_steward_awareness_runtime,
    build_context_aware_communication,
)
from estate.core.steward_command_center import generate_command_center, render_command_center_html


def test_wp4103_to_wp4107_generates_adaptive_awareness_artifacts(tmp_path):
    record_steward_interaction({"resident": "Alfred", "preferred_format": "bulleted_summary", "cadence": "batch_non_urgent_updates", "detail_level": "summary_with_drill_down", "channel": "command_center", "sentiment": "positive"}, root=tmp_path)
    record_steward_interaction({"resident": "Helen", "preferred_format": "bulleted_summary", "cadence": "batch_non_urgent_updates", "detail_level": "summary_with_drill_down", "channel": "command_center", "sentiment": "positive"}, root=tmp_path)
    record_steward_interaction({"resident": "Alfred", "preferred_format": "decision_brief", "cadence": "batch_non_urgent_updates", "detail_level": "summary_with_drill_down", "channel": "command_center", "sentiment": "positive"}, root=tmp_path)

    runtime = generate_steward_awareness_runtime(root=tmp_path, context={"urgency": "normal"}, signals={"steward_load": "high"})

    assert runtime["available"] is True
    data = runtime["data"]
    assert data["profile"]["preferences"]["preferred_format"] == "bulleted_summary"
    assert data["communication"]["recommended_mode"] == "batched_briefing"
    assert "collapse_routine_updates" in data["adaptation"]["adaptations"]
    assert "reduce_nonessential_questions" in data["support"]["recommended_behaviors"]
    assert data["relationship_review"]["relationship_health"] == "stable"
    for rel in [
        "runtime/steward/awareness/working_style_profile.json",
        "runtime/steward/awareness/context_aware_communication.json",
        "runtime/steward/awareness/interaction_adaptation.json",
        "runtime/steward/awareness/support_behavior.json",
        "runtime/steward/awareness/relationship_review.json",
    ]:
        assert (tmp_path / rel).is_file()


def test_wp4104_urgent_decision_context_recommends_immediate_recall(tmp_path):
    communication = build_context_aware_communication({"urgency": "blocking", "requires_decision": True}, root=tmp_path)

    assert communication["recommended_mode"] == "immediate_recall"
    assert communication["message_shape"]["detail_level"] == "decision_ready"


def test_command_center_includes_steward_awareness_panel(tmp_path):
    payload = generate_command_center(root=tmp_path, write=True)
    html = render_command_center_html(payload)

    assert "steward_awareness_runtime" in payload["panels"]
    assert "Steward Awareness Runtime" in html
    assert (tmp_path / "runtime/steward/command_center.html").is_file()
