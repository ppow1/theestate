from estate.core.visual_runtime import build_visual_runtime, format_visual_runtime_summary, validate_visual_runtime


def test_visual_runtime_validates_campaign_04_manifests():
    report = validate_visual_runtime()
    assert report["ok"], report["diagnostics"]
    assert report["counts"]["identities"] >= 5
    assert report["counts"]["gallery_entries"] >= 5
    assert report["counts"]["timeline_events"] >= 2


def test_visual_runtime_builds_integrated_payload():
    payload = build_visual_runtime()
    assert payload["schema_version"] == "estate_visual_runtime.v1"
    assert payload["validation"]["ok"] is True
    assert payload["resident_visual_identity"]["work_package"] == "WP-4073"
    assert payload["timeline"]["work_package"] == "WP-4082"
    summary = format_visual_runtime_summary(payload)
    assert "Estate Visual Runtime" in summary
    assert "Validation: ok" in summary
