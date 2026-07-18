"""Durable lifecycle records for governed ChatGPT reflection workflows.

This module records deterministic workflow state and evidence. It does not assess
whether reflection is warranted, approve onboarding, confirm renewal, retire an
implementation, or create a conversation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from estate.core.paths import ESTATE_ROOT

SCHEMA_VERSION = "reflection_workflow.v1"
WORKFLOW_DIR = Path("runtime/reflection/workflows")

STATES = (
    "evaluation_requested",
    "assessment_in_progress",
    "reflection_recommended",
    "reflection_authorized",
    "package_building",
    "package_validation_failed",
    "package_ready_for_review",
    "helen_review_required",
    "approved_for