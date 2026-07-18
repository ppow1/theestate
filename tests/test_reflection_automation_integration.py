from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PL0030 = ROOT / "operations/boards/parking_lot_items/PL-0030_AUTOMATED_REFLECTION_POINT_RENEWAL_PACKAGE_GENERATOR.md"
PROCESS = ROOT / "docs/operations/ChatGPT_Worker_Reflection_and_Continuity_Process_v1.md"
HINTS = ROOT / "AI_REFLECTION_HINTS.md"
TEMPLATE = ROOT / "docs/templates/ChatGPT_Worker_Reflection_Continuity_Template_v1.md"


def test_reflection_automation_governing_documents_are_complete_and_linked() -> None:
    documents = (PL0030, PROCESS, HINTS, TEMPLATE)
    for document in documents:
        assert document.is_file(), document
        assert document.read_text(encoding="utf-8").strip(), document

    pl0030 = PL0030.read_text