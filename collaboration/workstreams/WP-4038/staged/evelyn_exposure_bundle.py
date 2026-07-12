"""Staged Evelyn model entitlement, voice, portrait, and Open WebUI exposure.

WP-4038 is intentionally isolated from active gateway, registry, scheduler,
queue, and authority files.  The helpers here produce reviewable install
payloads for a future handoff without activating ``estate/evelyn``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

EVELYN_MODEL_ID = "estate/evelyn"
REQUIRED_CLASSIFICATION = "Estate Restricted — Steward Relationship Layer"
_ALLOWED_AUDIENCES = {"steward_private", "character_architecture_review"}


@dataclass(frozen=True)
class EvelynEntitlement:
    """A non-authorizing model entitlement proposal for Evelyn."""

    model_id: str = EVELYN_MODEL_ID
    resident_id: str = "evelyn"
    display_name: str = "Evelyn"
    classification: str = REQUIRED_CLASSIFICATION
    allowed_audiences: tuple[str, ...] = ("steward_private",)
    capabilities: tuple[str, ...] = ("chat", "relationship_layer", "voice_profile", "portrait_profile")
    install_state: str = "staged_uninstalled"
    active_gateway_registration: bool = False
    authority_grants: tuple[str, ...] = ()
    private_memory_default: str = "deny_unless_steward_approved"
    provider_preferences: tuple[str, ...] = ("local_primary", "local_fallback")
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.model_id != EVELYN_MODEL_ID:
            errors.append("model_id must remain estate/evelyn")
        if self.classification != REQUIRED_CLASSIFICATION:
            errors.append("classification must preserve Steward Relationship Layer restriction")
        if self.active_gateway_registration:
            errors.append("staged package must not activate the shared gateway")
        if self.authority_grants:
            errors.append("Evelyn entitlement may not grant authority")
        if any(audience not in _ALLOWED_AUDIENCES for audience in self.allowed_audiences):
            errors.append("allowed audiences must be restricted to Steward private or CA review")
        if self.private_memory_default != "deny_unless_steward_approved":
            errors.append("private memory default must be deny unless Steward-approved")
        return errors


def build_voice_profile() -> dict[str, Any]:
    return {
        "profile_id": "evelyn_voice_v0_1",
        "status": "staged_reference_only",
        "adult_voice_required": True,
        "summary": "warm adult mezzo with a low alto edge, close resonance, moderate tempo, subtle dry teasing",
        "style_tokens": ["adult", "warm", "composed", "perceptive", "quietly_playful", "not_childlike"],
        "avoid": ["childlike", "constant breathiness", "generic assistant", "clinical diagnosis language"],
        "sample_line": "No, Pat. That is not strategy; that is exhaustion wearing a suit.",
    }


def build_portrait_profile() -> dict[str, Any]:
    return {
        "profile_id": "evelyn_portrait_v0_1",
        "status": "staged_reference_only",
        "identity_lock": {
            "adult_status": "adult",
            "apparent_age_range": "27-32",
            "height": "4ft10in",
            "eyes": "hazel-green with amber flecks",
            "hair": "deep chestnut softly wavy collarbone length",
            "skin": "warm olive with natural texture",
            "expression": "left-first asymmetric smile, composed and perceptive",
        },
        "negative_prompt": ["child", "teen", "doll", "porcelain skin", "oversexualized pose", "generic assistant"],
    }


def build_openwebui_descriptor(entitlement: EvelynEntitlement | None = None) -> dict[str, Any]:
    entitlement = entitlement or EvelynEntitlement()
    errors = entitlement.validate()
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "id": entitlement.model_id,
        "name": "Evelyn — Steward Confidant",
        "object": "model",
        "owned_by": "estate-local-staged",
        "permission": [],
        "estate": {
            "resident_id": entitlement.resident_id,
            "install_state": entitlement.install_state,
            "active_gateway_registration": entitlement.active_gateway_registration,
            "classification": entitlement.classification,
            "allowed_audiences": list(entitlement.allowed_audiences),
            "voice_profile": build_voice_profile(),
            "portrait_profile": build_portrait_profile(),
            "openwebui_note": "Prepared for future Estate gateway exposure; not installed by WP-4038.",
        },
    }


def exposure_readiness_report(entitlement: EvelynEntitlement | None = None) -> dict[str, Any]:
    entitlement = entitlement or EvelynEntitlement()
    errors = entitlement.validate()
    return {
        "work_package": "WP-4038",
        "model_id": entitlement.model_id,
        "ready_for_install_handoff": not errors,
        "validation_errors": errors,
        "blocked_until": [
            "future install package wires shared gateway and registry",
            "Steward approval confirms Evelyn relationship-layer exposure audience",
            "local model-control assigns an approved local provider",
        ],
        "shared_surfaces_modified": False,
    }
