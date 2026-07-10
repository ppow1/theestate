"""Resident layered identity and continuity framework.

Layers govern access, context, expression, and memory classification for a single
canonical resident identity.  They never create substitute personalities.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "resident_layer_schema.v1"

LAYER_ORDER = ("public_social", "private_personal", "deep_bond", "local_intimate")

_CONTEXT_PRIVACY_RANK = {
    "public_profile": 0,
    "public_conversation": 0,
    "registry_metadata": 0,
    "office_context": 1,
    "session_history": 1,
    "relationship_history": 2,
    "bond_continuity": 2,
    "local_private_notes": 3,
    "local_device_context": 3,
}

_MEMORY_PRIVACY_RANK = {
    "public": 0,
    "profile": 0,
    "operational": 1,
    "personal": 1,
    "relationship": 2,
    "deep_bond": 2,
    "local_private": 3,
}


@dataclass(frozen=True)
class ResidentIdentity:
    """Canonical identity shared by every access layer for one resident."""

    resident_id: str
    continuity_id: str
    canonical_name: str
    canonical_uri: str
    role: str = ""

    @classmethod
    def from_registry_record(cls, record: Mapping[str, Any]) -> "ResidentIdentity":
        resident_id = str(record["id"])
        return cls(
            resident_id=resident_id,
            continuity_id=str(record.get("continuity_id") or f"continuity:{resident_id}"),
            canonical_name=str(record.get("name") or resident_id),
            canonical_uri=str(record.get("canonical") or f"estate://residents/{resident_id.lower()}"),
            role=str(record.get("role") or ""),
        )


@dataclass(frozen=True)
class ResidentLayer:
    """Access layer inherited from a canonical resident identity."""

    name: str
    rank: int
    eligibility_conditions: tuple[str, ...]
    allowed_context_sources: tuple[str, ...]
    memory_classes_available: tuple[str, ...]
    interaction_capabilities: tuple[str, ...]
    privacy_and_export_restrictions: tuple[str, ...]
    audit_behavior: tuple[str, ...]
    fallback_layer: str | None
    unavailable_behavior: str


@dataclass(frozen=True)
class LayerResolution:
    """Deterministic result of resolving a requested layer."""

    identity: ResidentIdentity
    layer: ResidentLayer
    requested_layer: str
    granted_layer: str
    degraded: bool
    denial_reasons: tuple[str, ...] = field(default_factory=tuple)
    personality_substitution_denied: bool = True
    schema_version: str = SCHEMA_VERSION

    def public_output_context(self, sources: Mapping[str, Any]) -> dict[str, Any]:
        """Return only context sources allowed by the granted layer."""
        allowed = set(self.layer.allowed_context_sources)
        return {key: value for key, value in sources.items() if key in allowed}

    def permits_memory_class(self, memory_class: str) -> bool:
        return memory_class in self.layer.memory_classes_available


DEFAULT_LAYERS: dict[str, ResidentLayer] = {
    "public_social": ResidentLayer(
        name="public_social",
        rank=0,
        eligibility_conditions=("public or unauthenticated surface", "no private relationship claim required"),
        allowed_context_sources=("public_profile", "public_conversation", "registry_metadata"),
        memory_classes_available=("public", "profile"),
        interaction_capabilities=("greeting", "general conversation", "public role explanation"),
        privacy_and_export_restrictions=("no private memory", "exportable public transcript only"),
        audit_behavior=("record layer", "record resident continuity id", "redact private source names"),
        fallback_layer=None,
        unavailable_behavior="deny rather than reveal private context",
    ),
    "private_personal": ResidentLayer(
        name="private_personal",
        rank=1,
        eligibility_conditions=("authenticated Steward or approved Estate operator", "private session permitted"),
        allowed_context_sources=("public_profile", "registry_metadata", "office_context", "session_history"),
        memory_classes_available=("public", "profile", "operational", "personal"),
        interaction_capabilities=("personal conversation", "operational continuity", "private preference recall"),
        privacy_and_export_restrictions=("private export requires authorization", "do not project private memory to public surfaces"),
        audit_behavior=("record eligibility basis", "record degradation", "retain privacy classification"),
        fallback_layer="public_social",
        unavailable_behavior="degrade to public_social with private context removed",
    ),
    "deep_bond": ResidentLayer(
        name="deep_bond",
        rank=2,
        eligibility_conditions=("explicit deep-bond authorization", "relationship continuity confirmed"),
        allowed_context_sources=("public_profile", "registry_metadata", "session_history", "relationship_history", "bond_continuity"),
        memory_classes_available=("public", "profile", "operational", "personal", "relationship", "deep_bond"),
        interaction_capabilities=("relationship-aware conversation", "high-trust continuity", "sensitive memory classification"),
        privacy_and_export_restrictions=("no public export", "requires explicit review for movement outside private boundary"),
        audit_behavior=("record authorization without sensitive content", "flag boundary-sensitive use"),
        fallback_layer="private_personal",
        unavailable_behavior="degrade to private_personal when deep-bond authorization is missing",
    ),
    "local_intimate": ResidentLayer(
        name="local_intimate",
        rank=3,
        eligibility_conditions=("local-only runtime", "explicit intimate-layer authorization", "no external export"),
        allowed_context_sources=("public_profile", "registry_metadata", "session_history", "relationship_history", "bond_continuity", "local_private_notes", "local_device_context"),
        memory_classes_available=("public", "profile", "operational", "personal", "relationship", "deep_bond", "local_private"),
        interaction_capabilities=("local-only high-privacy continuity", "non-exportable local context use"),
        privacy_and_export_restrictions=("local only", "no external export", "no public transcript projection"),
        audit_behavior=("local audit only", "record classification not content", "require degradation before export"),
        fallback_layer="deep_bond",
        unavailable_behavior="degrade to deep_bond or lower until eligibility is met",
    ),
}


def _normalize_layer(name: str | None) -> str:
    return (name or "public_social").strip().lower()


def _eligible(layer: ResidentLayer, grants: set[str]) -> bool:
    if layer.name == "public_social":
        return True
    if layer.name == "private_personal":
        return "private_personal" in grants or "authenticated" in grants
    if layer.name == "deep_bond":
        return "deep_bond" in grants
    if layer.name == "local_intimate":
        return "local_intimate" in grants and "local_runtime" in grants
    return False


def resolve_resident_layer(
    identity: ResidentIdentity,
    requested_layer: str | None,
    *,
    grants: Iterable[str] = (),
    layers: Mapping[str, ResidentLayer] = DEFAULT_LAYERS,
) -> LayerResolution:
    """Resolve a layer deterministically, degrading to the nearest eligible layer."""
    requested = _normalize_layer(requested_layer)
    denial_reasons: list[str] = []
    current = requested if requested in layers else "public_social"
    if requested not in layers:
        denial_reasons.append(f"unsupported_layer:{requested}")
    grant_set = {str(grant).strip().lower() for grant in grants}

    seen: set[str] = set()
    while current not in seen:
        seen.add(current)
        layer = layers[current]
        if _eligible(layer, grant_set):
            return LayerResolution(
                identity=identity,
                layer=layer,
                requested_layer=requested,
                granted_layer=layer.name,
                degraded=layer.name != requested,
                denial_reasons=tuple(denial_reasons),
            )
        denial_reasons.append(f"ineligible:{current}")
        current = layer.fallback_layer or "public_social"

    public = layers["public_social"]
    return LayerResolution(identity, public, requested, public.name, public.name != requested, tuple(denial_reasons))


def assert_no_personality_substitution(resolution: LayerResolution, proposed_identity: ResidentIdentity) -> None:
    """Reject attempts to swap the resident identity while changing layers."""
    if proposed_identity.resident_id != resolution.identity.resident_id or proposed_identity.continuity_id != resolution.identity.continuity_id:
        raise ValueError("resident layers may not substitute personality, resident id, or continuity id")


def filter_context_for_layer(resolution: LayerResolution, context: Mapping[str, Any]) -> dict[str, Any]:
    return resolution.public_output_context(context)
