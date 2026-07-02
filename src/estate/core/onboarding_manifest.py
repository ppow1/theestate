import json
from pathlib import Path


MANIFEST_PATHS = [
    Path("docs/onboarding/chief_architect_onboarding_manifest.json"),
    Path("docs/onboarding/worker_onboarding_manifest.json"),
]


def _entries(manifest):
    for section in ("required_reading_order", "registry_backed_items"):
        for item in manifest.get(section, []):
            yield section, item


def check_onboarding_manifests(root=None):
    """Validate required repository-relative paths in onboarding manifests."""
    root = Path(root) if root is not None else Path.cwd()
    missing_manifests = []
    missing_required_paths = []
    checked_paths = []

    for manifest_path in MANIFEST_PATHS:
        absolute_manifest_path = root / manifest_path
        if not absolute_manifest_path.exists():
            missing_manifests.append(str(manifest_path))
            continue

        manifest = json.loads(absolute_manifest_path.read_text(encoding="utf-8"))
        for section, item in _entries(manifest):
            path = item.get("path")
            if not path or not item.get("required", False):
                continue
            checked_paths.append(path)
            if not (root / path).exists():
                missing_required_paths.append(
                    {
                        "manifest": str(manifest_path),
                        "section": section,
                        "title": item.get("title"),
                        "path": path,
                    }
                )

    return {
        "ok": not missing_manifests and not missing_required_paths,
        "manifest_paths": [str(path) for path in MANIFEST_PATHS],
        "missing_manifests": missing_manifests,
        "checked_required_paths": checked_paths,
        "missing_required_paths": missing_required_paths,
    }


def format_onboarding_manifest_check(report):
    lines = ["Estate Onboarding Manifest Check"]
    lines.append(f"Status: {'ok' if report['ok'] else 'failed'}")
    lines.append(f"Manifests: {len(report['manifest_paths'])}")
    lines.append(f"Required paths checked: {len(report['checked_required_paths'])}")

    if report["missing_manifests"]:
        lines.append("Missing manifests:")
        for path in report["missing_manifests"]:
            lines.append(f"- {path}")

    if report["missing_required_paths"]:
        lines.append("Missing required paths:")
        for item in report["missing_required_paths"]:
            lines.append(f"- {item['path']} ({item['manifest']}: {item['title']})")

    return "\n".join(lines)
