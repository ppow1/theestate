from __future__ import annotations

SCHEMA_VERSION = "estate-reflection-case-v1"
CASE_STATES = (
    "evaluation_requested",
    "assessment_in_progress",
    "reflection_recommended",
    "reflection_authorized",
    "awaiting_worker_artifacts",
    "package_building",
    "package_validation_failed",
    "helen_review_required",
    "approved_for_onboarding",
    "renewal_confirmed",
    "renewal_blocked",
)
TERMINAL_STATES = ("renewal_confirmed", "renewal_blocked")
