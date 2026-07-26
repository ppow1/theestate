import json
from pathlib import Path

from estate.core.conversation_archive_ingestion import ingest
from estate.core.conversation_specification_extraction import extract_specifications
from estate.core.conversation_specification_reconciliation import reconcile_bundles


def test_wp4208_wp4209_wp4210_end_to_end(tmp_path: Path):
    repo = tmp_path / "repo"
    pending = repo / "collaboration/work_packages/pending/WP-9001_Test.md"
    pending.parent.mkdir(parents=True)
    pending.write_text("# Required Implementation\nPolicy schema runtime behavior decision escalation boundaries prohibited integration audit review diagnostics failure operator documentation unit test integration test validation scenario anti-pattern completion acceptance criteria.\n")
    areas = ["Policy", "Schema records", "Runtime behavior", "Decision escalation", "Boundaries prohibited",
             "Estate integration", "Audit review", "Diagnostics failure", "Operator documentation",
             "Unit tests", "Integration tests", "Validation scenarios", "Anti-patterns", "Completion criteria"]
    sections = "".join(f"<h2>{x}</h2><p>Deterministic requirements preserve source evidence and require authorized human review before any repository action occurs.</p>" for x in areas)
    archive = tmp_path / "chat.html"
    archive.write_text(f'<div data-message-author-role="assistant" data-message-id="a1"><h2>WP-9001 — Test</h2>{sections}</div>')
    ingested = ingest(archive, tmp_path / "ingested", repository_root=repo)
    extracted = extract_specifications(ingested, ["WP-9001"], tmp_path / "extracted", repository_root=repo)
    result = reconcile_bundles([extracted], ["WP-9001"], tmp_path / "reconciled", repository_root=repo)
    manifest = json.loads((result / "reconciliation_manifest.json").read_text())
    assert manifest["canonical_status"] == "non_canonical_review_required"
    assert manifest["safety"] == {"inputs_modified": False, "pending_definitions_modified": False,
                                  "canonical_destinations_written": False, "automatic_promotion": False}
