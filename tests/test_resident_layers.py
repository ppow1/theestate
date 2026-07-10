import pytest

from estate.core.resident_layers import (
    ResidentIdentity,
    assert_no_personality_substitution,
    filter_context_for_layer,
    resolve_resident_layer,
)


def identity():
    return ResidentIdentity(
        resident_id="RES-000001",
        continuity_id="continuity:RES-000001",
        canonical_name="Alfred",
        canonical_uri="estate://residents/res-000001",
        role="Coordinates the Estate.",
    )


def test_identity_and_continuity_persist_across_layer_changes():
    base = identity()
    public = resolve_resident_layer(base, "public_social")
    private = resolve_resident_layer(base, "private_personal", grants={"authenticated"})
    deep = resolve_resident_layer(base, "deep_bond", grants={"deep_bond"})

    assert {public.identity.resident_id, private.identity.resident_id, deep.identity.resident_id} == {"RES-000001"}
    assert {public.identity.continuity_id, private.identity.continuity_id, deep.identity.continuity_id} == {"continuity:RES-000001"}
    assert public.identity.canonical_name == private.identity.canonical_name == deep.identity.canonical_name == "Alfred"


def test_layer_resolution_is_deterministic_and_degrades_safely():
    base = identity()
    first = resolve_resident_layer(base, "local_intimate", grants={"authenticated"})
    second = resolve_resident_layer(base, "local_intimate", grants={"authenticated"})

    assert first.granted_layer == second.granted_layer == "private_personal"
    assert first.degraded is True
    assert first.denial_reasons == second.denial_reasons == ("ineligible:local_intimate", "ineligible:deep_bond")


def test_unsupported_layer_degrades_to_public_social():
    resolution = resolve_resident_layer(identity(), "unnamed_confidant", grants={"local_intimate", "local_runtime"})

    assert resolution.granted_layer == "public_social"
    assert resolution.degraded is True
    assert "unsupported_layer:unnamed_confidant" in resolution.denial_reasons


def test_private_context_cannot_leak_to_public_output():
    resolution = resolve_resident_layer(identity(), "public_social")
    context = {
        "public_profile": "Alfred is the Manager of Administration.",
        "public_conversation": "Hello.",
        "session_history": "private turn",
        "relationship_history": "private relationship memory",
        "local_private_notes": "local secret",
    }

    assert filter_context_for_layer(resolution, context) == {
        "public_profile": "Alfred is the Manager of Administration.",
        "public_conversation": "Hello.",
    }
    assert not resolution.permits_memory_class("personal")
    assert not resolution.permits_memory_class("deep_bond")


def test_personality_substitution_is_explicitly_denied():
    resolution = resolve_resident_layer(identity(), "deep_bond", grants={"deep_bond"})
    with pytest.raises(ValueError, match="may not substitute personality"):
        assert_no_personality_substitution(
            resolution,
            ResidentIdentity(
                resident_id="RES-000999",
                continuity_id="continuity:RES-000999",
                canonical_name="Confidant",
                canonical_uri="estate://residents/res-000999",
            ),
        )
