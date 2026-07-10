from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

MATRIX_PATH = ESTATE_ROOT / "docs" / "residents" / "ingrid" / "Ingrid_Boundary_Matrix_v0_1.json"
CLASSIFICATION_ORDER = ("Public", "Estate Internal", "Restricted", "Steward Only", "Local Only")
RESTRICTED_LEVELS = {"Restricted", "Steward Only", "Local Only"}


def load_boundary_matrix(path: Path | None = None) -> dict[str, Any]:
    return json.loads((path or MATRIX_PATH).read_text(encoding="utf-8"))


def _rank(level: str) -> int:
    try:
        return CLASSIFICATION_ORDER.index(level)
    except ValueError as exc:
        raise ValueError(f"Unsupported classification: {level}") from exc


def class_boundary(matrix: dict[str, Any], artifact_class: str) -> dict[str, Any]:
    for boundary in matrix.get("artifact_classes", []):
        if boundary.get("artifact_class") == artifact_class:
            return boundary
    raise KeyError(f"Unknown artifact class: {artifact_class}")


def can_read(matrix: dict[str, Any], artifact_class: str, actor: str, actor_clearance: str) -> bool:
    boundary = class_boundary(matrix, artifact_class)
    return actor in boundary.get("allowed_readers", []) and _rank(actor_clearance) >= _rank(boundary["minimum_classification"])


def can_write(matrix: dict[str, Any], artifact_class: str, actor: str, actor_clearance: str) -> bool:
    boundary = class_boundary(matrix, artifact_class)
    return actor in boundary.get("allowed_writers", []) and _rank(actor_clearance) >= _rank(boundary["minimum_classification"])


def validate_public_summary(matrix: dict[str, Any], source_items: list[dict[str, Any]], summary_text: str) -> dict[str, Any]:
    """Validate that a public summary excludes restricted source content.

    Source items may provide a classification and optional exact protected fragments.
    Public summaries reject any Restricted, Steward Only, or Local Only fragment that is
    carried forward verbatim, and reject any item explicitly marked summary_safe=False.
    """
    violations: list[dict[str, str]] = []
    for item in source_items:
        level = item.get("classification", "Estate Internal")
        text = str(item.get("text", ""))
        fragments = item.get("protected_fragments") or ([text] if text else [])
        unsafe = level in RESTRICTED_LEVELS or item.get("summary_safe") is False
        if not unsafe:
            continue
        for fragment in fragments:
            fragment = str(fragment).strip()
            if fragment and fragment in summary_text:
                violations.append({"classification": level, "fragment": fragment[:80]})
    return {"valid": not violations, "violations": violations}


def export_allowed(source_classification: str, destination_classification: str, *, public_destination: bool = False) -> bool:
    if public_destination and source_classification != "Public":
        return False
    return _rank(destination_classification) >= _rank(source_classification)
