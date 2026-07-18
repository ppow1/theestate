from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "operations/continuity/Chief_Architect_5_Execution_Handoff_Addendum.md"


def test_reconstructed_handoff_is_structurally_complete() -> None:
    raw = HANDOFF.read_bytes()
    text = raw.decode("utf-8")

    assert raw
    required_headings = (
        "## Document Status, Scope, and Provenance",
        "## 1. Exact Current Assignment",
        "### Assignment purpose",
        "### Completion condition",
        "## 2. Current Execution Status",
        "### Completed work",
        "### Partially completed work",
        "### Unstarted work",
        "### Blocked work",
        "### Failed attempts",
        "### Last successful action",
        "### Next executable action",
        "## 3. Officeholder Backlog at the Historical Handoff",
        "## 4. Repository and Evidence References",
        "## 5. Latest Failure or Blocker",
        "## 6. Renewal Start Command",
        "## 7. Known Uncertainties and Verification Requirements",
        "## 8. Clean-End and Completeness Declaration",
    )
    for heading in required_headings:
        assert heading in text, heading

    for provenance in (
        "Repository verified",
        "Historical reconstruction",
        "Steward reported",
        "Uncertain",
        "Current verification required",
    ):
        assert provenance in text

    placeholder_patterns = (
        r"\bTBD\b",
        r"\bTODO\b",
        r"\[insert[^]]*\]",
        r"<placeholder>",
    )
    assert not any(re.search(pattern, text, re.IGNORECASE) for pattern in placeholder_patterns)
    assert text.endswith(
        "Current repository evidence and the governing process take precedence.\n"
    )


def test_reconstructed_handoff_repository_references_exist() -> None:
    text = HANDOFF.read_text(encoding="utf-8")
    referenced_paths = set(
        re.findall(
            r"`((?:AI_REFLECTION_HINTS\.md|(?:docs|operations|collaboration|src|tests)/[^`\n]+))`",
            text,
        )
    )

    assert referenced_paths
    missing = sorted(path for path in referenced_paths if not (ROOT / path).exists())
    assert not missing, missing
