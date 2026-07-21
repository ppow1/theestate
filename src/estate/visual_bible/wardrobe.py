"""WP-4113 governed wardrobe records.

Records are JSON-compatible YAML.  The loader deliberately accepts the safe JSON
subset so no executable YAML tags, aliases, or duplicate mapping keys can enter
the runtime without adding a YAML parser dependency.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .validator import ValidationError

SCOPES = ("public", "internal", "restricted", "private")
SCOPE_RANK = {scope: rank for rank, scope in enumerate(SCOPES)}
TAXONOMY = (
    "office-authoritative", "office-approachable", "business-casual",
    "casual-day", "casual-evening", "home-relaxed", "formal-day",
    "cocktail", "formal-evening", "ceremony", "seasonal-summer",
    "seasonal-winter", "rain-travel", "fitness", "dance", "hobby-specific",
    "swim", "signature-look", "private-audience",
)
LIFECYCLE_PAIRS = {
    ("draft", "experimental"), ("draft", "provisional"),
    ("in_review", "experimental"), ("in_review", "provisional"),
    ("revision_requested", "experimental"), ("revision_requested", "provisional"),
    ("approved", "provisional"), ("approved", "canonical"),
    ("rejected", "rejected"), ("retired", "retired"),
}
TRANSITIONS = {
    "draft": {"in_review"}, "in_review": {"revision_requested", "approved", "rejected"},
    "revision_requested": {"in_review", "rejected"},
    "approved": {"retired"}, "rejected": set(), "retired": set(),
}
RECORD_FILES = {
    "wardrobe_manifest.yaml", "signature_looks.yaml", "fit_rules.yaml",
    "accessories.yaml", "footwear.yaml",
}
ID_RE = re.compile(r"^(?:wd|sl|fit|fw|acc|pf|wr|wae)-[a-z0-9]+-[a-z0-9-]+-v[1-9][0-9]*$")


class WardrobeDiagnostic(dict):
    """A deterministic, serializable diagnostic."""


def _fail(code: str, pointer: str, message: str) -> None:
    raise ValidationError(f"{code} {pointer}: {message}")


def load_wardrobe_record(path: Path) -> dict[str, Any]:
    """Load JSON-compatible YAML while rejecting duplicates and unsafe YAML."""
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in items:
            if key in value:
                _fail("WARDROBE-SCHEMA-INVALID", "/", f"duplicate key {key}")
            value[key] = item
        return value
    try:
        result = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except (json.JSONDecodeError, UnicodeError) as exc:
        _fail("WARDROBE-SCHEMA-INVALID", "/", "record must use safe JSON-compatible YAML")
    if not isinstance(result, dict):
        _fail("WARDROBE-SCHEMA-INVALID", "/", "record must be a mapping")
    return result


def canonical_digest(record: dict[str, Any]) -> str:
    """Hash RFC-8785-inspired stable JSON, excluding the self-referential digest."""
    value = deepcopy(record)
    value.get("provenance", {}).pop("content_digest", None)
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_content_digest(record: dict[str, Any]) -> None:
    """Reject an in-place edit whose persisted self-declared digest is stale."""
    actual = canonical_digest(record)
    if record.get("provenance", {}).get("content_digest") != actual:
        _fail("WARDROBE-HASH-MISMATCH", "/provenance/content_digest", "content digest does not match canonical record bytes")


def _envelope(record: dict[str, Any], *, resident: str | None = None, scope: str | None = None) -> None:
    required = ("schema_version", "record_id", "revision", "resident_id", "audience_scope",
                "lifecycle_state", "canon_class", "active", "created_at", "created_by",
                "updated_at", "provenance", "steward_decision_id")
    for field in required:
        if field not in record:
            _fail("WARDROBE-MISSING-SCOPE" if field == "audience_scope" else "WARDROBE-SCHEMA-INVALID", f"/{field}", "required field missing")
    if record["audience_scope"] not in SCOPES:
        _fail("WARDROBE-MISSING-SCOPE", "/audience_scope", "invalid audience scope")
    if resident and record["resident_id"] != resident or scope and record["audience_scope"] != scope:
        _fail("WARDROBE-ID-SCOPE-MISMATCH", "/", "record owner or scope disagrees with path")
    if not ID_RE.match(record["record_id"]):
        _fail("WARDROBE-SCHEMA-INVALID", "/record_id", "malformed immutable id")
    if (record["lifecycle_state"], record["canon_class"]) not in LIFECYCLE_PAIRS:
        _fail("WARDROBE-ILLEGAL-TRANSITION", "/lifecycle_state", "illegal lifecycle/canon pair")
    if record["resident_id"] not in record["record_id"].split("-"):
        _fail("WARDROBE-ID-SCOPE-MISMATCH", "/record_id", "record id does not identify owner")
    provenance = record["provenance"]
    for field in ("source_refs", "parent_record_ids", "replacement_for", "content_digest", "schema_digest"):
        if field not in provenance:
            _fail("WARDROBE-SCHEMA-INVALID", f"/provenance/{field}", "provenance field missing")
    for digest in (provenance["content_digest"], provenance["schema_digest"]):
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            _fail("WARDROBE-SCHEMA-INVALID", "/provenance", "malformed digest")


def validate_transition(old: dict[str, Any], new: dict[str, Any]) -> None:
    _envelope(old); _envelope(new)
    if old["record_id"] != new["record_id"] or old["resident_id"] != new["resident_id"]:
        _fail("WARDROBE-ILLEGAL-TRANSITION", "/record_id", "identity is immutable")
    if new["lifecycle_state"] not in TRANSITIONS[old["lifecycle_state"]]:
        _fail("WARDROBE-ILLEGAL-TRANSITION", "/lifecycle_state", "transition is not allowed")
    if new["revision"] <= old["revision"]:
        _fail("WARDROBE-ILLEGAL-TRANSITION", "/revision", "a transition requires a later revision")


def validate_manifest(record: dict[str, Any], *, resident: str | None = None, scope: str | None = None) -> None:
    _envelope(record, resident=resident, scope=scope)
    coverage = record.get("category_coverage", [])
    categories = [item.get("category") for item in coverage]
    if len(categories) != len(set(categories)) or set(categories) != set(TAXONOMY):
        _fail("WARDROBE-SCHEMA-INVALID", "/category_coverage", "taxonomy must occur exactly once")
    for index, item in enumerate(coverage):
        if item.get("applicability") not in {"required", "optional", "not_applicable"} or not item.get("rationale"):
            _fail("WARDROBE-SCHEMA-INVALID", f"/category_coverage/{index}", "applicability and resident-specific rationale required")
    for name in ("physical_specification_ref", "facial_fingerprint_ref", "scale_profile_ref"):
        ref = record.get(name, {})
        if not ref.get("id") or ref.get("revision", 0) < 1 or not re.fullmatch(r"sha256:[0-9a-f]{64}", ref.get("digest", "")):
            _fail("WARDROBE-STALE-BINDING", f"/{name}", "immutable predecessor binding required")


def validate_fit_rule(record: dict[str, Any]) -> None:
    _envelope(record)
    for field in ("physical_specification_ref", "height_profile_ref", "measurement_profile_ref",
                  "fit_class", "tailoring_assumptions", "expected_apparent_effect",
                  "presentation_effects", "known_generation_risks"):
        if record.get(field) in (None, "", [], {}):
            _fail("WARDROBE-MISSING-FIT", f"/{field}", "complete fit behavior required")
    effects = record["presentation_effects"]
    for effect in ("shapewear", "push_up_construction", "structured_cups", "padding", "tailoring"):
        if set(effects.get(effect, {})) != {"used", "effect"}:
            _fail("WARDROBE-MISSING-FIT", f"/presentation_effects/{effect}", "used and effect are required")
    text = json.dumps(record, sort_keys=True).lower()
    if any(term in text for term in ("updates canonical height", "changes canonical measurements", "replaces physical specification")):
        _fail("WARDROBE-CANON-CONTRADICTION", "/", "presentation cannot mutate canonical physique")


def validate_prompt_fragment(record: dict[str, Any]) -> None:
    _envelope(record)
    positive = record.get("positive", {})
    negative = record.get("negative", {})
    for field in ("adult_presentation", "garment", "fabric_behavior", "fit_behavior", "proportion_preservation", "camera_and_pose"):
        if not positive.get(field):
            _fail("WARDROBE-MISSING-PROMPT", f"/positive/{field}", "positive fragment incomplete")
    for field in ("identity_drift", "proportion_drift", "garment_failures", "fit_failures", "age_and_context"):
        if not negative.get(field):
            _fail("WARDROBE-MISSING-PROMPT", f"/negative/{field}", "negative fragment incomplete")
    overlays = record.get("model_overlays", [])
    forbidden = {"resident_id", "audience_scope", "physical_specification_ref", "identity"}
    if any(forbidden & set(item.get("overrides", {})) for item in overlays):
        _fail("WARDROBE-CANON-CONTRADICTION", "/model_overlays", "adapter may not override semantic identity or scope")


def validate_footwear(record: dict[str, Any]) -> None:
    _envelope(record)
    for field in ("style", "heel_height", "platform_height", "toe_shape", "material", "color", "posture_effect", "activity_suitability", "resident_preference"):
        if record.get(field) in (None, "", [], {}):
            _fail("WARDROBE-SCHEMA-INVALID", f"/{field}", "footwear metadata missing")
    heel = record["heel_height"]
    try: Decimal(str(heel["value"]))
    except (KeyError, InvalidOperation): _fail("WARDROBE-SCHEMA-INVALID", "/heel_height", "exact numeric height required")
    if heel.get("unit") not in {"in", "cm"} or record.get("canonical_standing_height_unchanged") is not True:
        _fail("WARDROBE-HEEL-HEIGHT-MUTATION", "/heel_height", "heel is presentation only")


def validate_accessory(record: dict[str, Any]) -> None:
    _envelope(record)
    for field in ("accessory_type", "material", "color", "scale", "placement", "contexts", "resident_preference", "identity_coordination", "generation_risks"):
        if record.get(field) in (None, "", [], {}):
            _fail("WARDROBE-SCHEMA-INVALID", f"/{field}", "accessory metadata missing")


def validate_signature_look(record: dict[str, Any], *, promotion: bool = False) -> None:
    _envelope(record)
    for field in ("title", "category", "contexts", "physical_binding", "design", "fit_rule_id", "footwear_ids", "accessory_ids", "prompt_fragment_id", "distinctiveness", "evidence", "approval"):
        if record.get(field) in (None, "", [], {}):
            _fail("WARDROBE-SIGNATURE-INCOMPLETE", f"/{field}", "signature look incomplete")
    if record["category"] != "signature-look":
        _fail("WARDROBE-SIGNATURE-INCOMPLETE", "/category", "wrong category")
    if promotion:
        evidence, approval = record["evidence"], record["approval"]
        if not evidence.get("full_body_asset") or not evidence.get("portrait_crop_asset"):
            _fail("WARDROBE-SIGNATURE-INCOMPLETE", "/evidence", "approved full-body and portrait evidence required")
        if record["lifecycle_state"] != "approved" or record["canon_class"] != "canonical" or not approval.get("steward_decision_id"):
            _fail("WARDROBE-UNAUTHORIZED-APPROVAL", "/approval", "Steward-approved canonical state required")


def check_reference(owner: dict[str, Any], target: dict[str, Any]) -> None:
    if owner["resident_id"] != target["resident_id"]:
        _fail("WARDROBE-CROSS-RESIDENT-COLLISION", "/resident_id", "cross-resident inheritance prohibited")
    if SCOPE_RANK[target["audience_scope"]] > SCOPE_RANK[owner["audience_scope"]]:
        _fail("WARDROBE-AUDIENCE-LEAK", "/audience_scope", "less restricted record references more restricted content")
    if target["lifecycle_state"] in {"rejected", "retired"} and owner.get("active"):
        _fail("WARDROBE-SCHEMA-INVALID", "/active", "active record references inactive dependency")


def validate_private_activation(record: dict[str, Any], authorization: dict[str, Any] | None) -> None:
    if record["audience_scope"] == "private":
        if not authorization or authorization.get("deny_by_default") is not True or not authorization.get("expires_at"):
            _fail("WARDROBE-AUDIENCE-LEAK", "/authorization", "private access requires explicit time-bounded authorization")


def append_audit_event(events: list[dict[str, Any]], event: dict[str, Any]) -> dict[str, Any]:
    """Append a hash-chained event to the caller-owned durable event list."""
    item = deepcopy(event)
    item["previous_hash"] = events[-1]["event_hash"] if events else None
    item["event_hash"] = "sha256:" + hashlib.sha256(json.dumps(item, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    events.append(item)
    return item


def scaffold_wardrobe(root: Path, resident_id: str) -> None:
    """Create neutral scoped directories only; never clone another resident's content."""
    for scope in SCOPES:
        wardrobe = root / resident_id / scope / "wardrobe"
        for child in ("prompt_fragments", "reference_images", "rejected_variants", "revisions", "reviews", "audit"):
            (wardrobe / child).mkdir(parents=True, exist_ok=True)
            (wardrobe / child / ".gitkeep").touch(exist_ok=True)
        notes = wardrobe / "steward_notes.md"
        if not notes.exists():
            notes.write_text(f"# {resident_id} wardrobe Steward notes ({scope})\n\nNo Steward decisions recorded.\n", encoding="utf-8")
