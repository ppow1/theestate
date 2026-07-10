import json
from pathlib import Path

from estate.core.helen_readiness import build_readiness


def test_helen_readiness_writes_deterministic_gate_artifacts():
    payload = build_readiness(write=True)
    assert payload["schema_version"] == "helen_operational_readiness.v1"
    assert payload["resident"] == "Helen"
    assert payload["overall_status"] in {"ready", "ready_with_limitations", "not_ready"}
    assert payload["authority_flags"] == {
        "constitutional_authority_granted": False,
        "provider_execution_performed": False,
        "operational_queue_control_performed": False,
        "grace_appointed_or_activated": False,
    }
    assert len(payload["gates"]) == 10
    assert Path("runtime/residents/helen/readiness.json").is_file()
    assert Path("operations/residents/helen/Helen_Operational_Readiness_Report.md").is_file()


def test_grace_gate_blocks_missing_or_unperformed_evidence_without_appointment():
    payload = build_readiness(write=True)
    g10 = next(g for g in payload["gates"] if g["gate_id"] == "G10")
    assert g10["passed"] is True
    assert payload["authority_flags"]["grace_appointed_or_activated"] is False
    registry = json.loads(Path("data/registry/residents.json").read_text())
    assert all(entry.get("name") != "Grace" for entry in registry)


def test_cli_helen_readiness_json(capsys):
    from estate.cli.main import main
    try:
        main(["helen-readiness", "--json"])
    except SystemExit as exc:
        assert exc.code in (None, 0, 2)
    data = json.loads(capsys.readouterr().out)
    assert data["resident"] == "Helen"
    assert data["authority_flags"]["constitutional_authority_granted"] is False
