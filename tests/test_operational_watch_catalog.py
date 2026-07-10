from estate.core.operational_watch_catalog import WATCH_CATEGORIES, default_operational_watch_descriptors, descriptor_by_id


def test_catalog_contains_required_categories_and_migrated_watches():
    descriptors = default_operational_watch_descriptors()
    categories = {d.category for d in descriptors}
    assert {"repository", "validation", "runtime-health", "queue", "service", "artifact-freshness"} <= categories <= WATCH_CATEGORIES
    ids = {d.watch_id for d in descriptors}
    assert "pending_routing_recommendation_watch" in ids
    assert "operational_target_watch" in ids


def test_descriptor_round_trips_to_background_watch_without_behavior_loss():
    desc = descriptor_by_id("stale_validation_artifact_watch")
    watch = desc.to_background_watch()
    assert watch.watch_id == desc.watch_id
    assert watch.conditions["watch_kind"] == "stale_validation_artifact"
    assert watch.action_type == desc.action_class
    assert watch.enabled is desc.enabled_by_default
