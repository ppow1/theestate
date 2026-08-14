"""Static contract tests for the Estate-owned Riverview bridge."""

from pathlib import Path


BRIDGE = Path(__file__).parents[1] / "tools" / "riverview_doorbell_bridge.cjs"


def test_bridge_exposes_only_named_operation_and_fixed_action():
    source = BRIDGE.read_text(encoding="utf-8")
    assert "ring_riverview_doorbell" in source
    assert "FIXED_WAKE_TEXT" in source
    assert "prompt/body" not in source
    assert "process.argv" in source
    assert "Runtime.evaluate" in source
    assert "targets.find" not in source
    assert "surface=work" not in source
    assert "chatgpt.com/" not in source


def test_bridge_rejects_general_browser_inputs_and_has_fail_closed_checks():
    source = BRIDGE.read_text(encoding="utf-8")
    assert "unsupported fields" in source
    assert "designated target absent" in source
    assert "designated target is ambiguous" in source
    assert "RIV-PLY-0009" in source
    assert "already_succeeded" in source
