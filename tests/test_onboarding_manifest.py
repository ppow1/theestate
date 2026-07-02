import json
import subprocess
import sys
from pathlib import Path

from estate.core.onboarding_manifest import check_onboarding_manifests


ROOT = Path(__file__).resolve().parents[1]
CHIEF_MANIFEST = ROOT / "docs/onboarding/chief_architect_onboarding_manifest.json"
WORKER_MANIFEST = ROOT / "docs/onboarding/worker_onboarding_manifest.json"


def load_chief_manifest():
    return json.loads(CHIEF_MANIFEST.read_text(encoding="utf-8"))


def manifest_paths(manifest):
    paths = []
    for key in ("required_reading_order", "registry_backed_items"):
        paths.extend(item["path"] for item in manifest.get(key, []) if "path" in item)
    return paths


def test_manifest_files_exist():
    assert (ROOT / "docs/onboarding/Chief_Architect_Onboarding_Manifest.md").exists()
    assert CHIEF_MANIFEST.exists()
    assert (ROOT / "docs/onboarding/Worker_Onboarding_Manifest.md").exists()
    assert WORKER_MANIFEST.exists()


def test_required_manifest_paths_exist_in_repository():
    report = check_onboarding_manifests(root=ROOT)
    assert report["ok"]
    assert not report["missing_required_paths"]


def test_stale_constitution_path_is_not_used():
    text = CHIEF_MANIFEST.read_text(encoding="utf-8")
    paths = manifest_paths(load_chief_manifest())
    assert "constitution/constitution.md" in paths
    assert "constitution/Estate_Constitution.md" not in paths
    assert '"path": "constitution/Estate_Constitution.md"' not in text


def test_visual_onboarding_uses_visual_manifest():
    manifest = load_chief_manifest()
    assert manifest["visual_onboarding_entry_point"] == "docs/onboarding/visual_manifest.md"
    paths = manifest_paths(manifest)
    assert "docs/onboarding/visual_manifest.md" in paths


def test_registry_backed_staff_roster_sources_are_referenced():
    manifest = load_chief_manifest()
    registry_paths = {item["path"] for item in manifest["registry_backed_items"]}
    assert registry_paths == {
        "data/registry/personnel.json",
        "data/registry/residents.json",
        "data/registry/mailboxes.json",
    }


def test_unresolved_items_are_marked_instead_of_guessed():
    manifest = load_chief_manifest()
    roster_items = [item for item in manifest["unresolved_items"] if "staff roster" in item["title"].lower()]
    assert roster_items
    assert roster_items[0]["status"] == "unresolved"
    assert "path" not in roster_items[0]


def test_cli_onboarding_manifest_check():
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "onboarding-manifest-check", "--json"],
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src")},
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["ok"]
