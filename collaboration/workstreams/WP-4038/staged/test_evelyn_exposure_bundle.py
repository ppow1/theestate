from evelyn_exposure_bundle import (
    EVELYN_MODEL_ID,
    EvelynEntitlement,
    build_openwebui_descriptor,
    build_portrait_profile,
    build_voice_profile,
    exposure_readiness_report,
)


def test_default_entitlement_is_staged_and_valid():
    entitlement = EvelynEntitlement()
    assert entitlement.validate() == []
    assert entitlement.model_id == EVELYN_MODEL_ID
    assert entitlement.active_gateway_registration is False
    assert entitlement.authority_grants == ()


def test_rejects_gateway_activation_and_broad_audience():
    entitlement = EvelynEntitlement(active_gateway_registration=True, allowed_audiences=("public",))
    errors = entitlement.validate()
    assert "staged package must not activate the shared gateway" in errors
    assert "allowed audiences must be restricted to Steward private or CA review" in errors


def test_openwebui_descriptor_contains_voice_and_portrait_without_permissions():
    descriptor = build_openwebui_descriptor()
    assert descriptor["id"] == "estate/evelyn"
    assert descriptor["permission"] == []
    assert descriptor["estate"]["active_gateway_registration"] is False
    assert descriptor["estate"]["voice_profile"]["adult_voice_required"] is True
    assert descriptor["estate"]["portrait_profile"]["identity_lock"]["height"] == "4ft10in"


def test_profiles_preserve_safety_identity_constraints():
    voice = build_voice_profile()
    portrait = build_portrait_profile()
    assert "not_childlike" in voice["style_tokens"]
    assert "child" in portrait["negative_prompt"]
    assert portrait["identity_lock"]["adult_status"] == "adult"


def test_readiness_report_is_install_ready_but_not_installed():
    report = exposure_readiness_report()
    assert report["ready_for_install_handoff"] is True
    assert report["shared_surfaces_modified"] is False
    assert "future install package wires shared gateway and registry" in report["blocked_until"]
