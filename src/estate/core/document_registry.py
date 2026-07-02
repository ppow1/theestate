import json
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

REGISTRY_PATH = ESTATE_ROOT / "data" / "registry" / "documents.json"


def _effective_root(root=ESTATE_ROOT):
    root = Path(root)
    if (root / "data" / "registry" / "documents.json").exists():
        return root
    cwd = Path.cwd()
    if (cwd / "data" / "registry" / "documents.json").exists():
        return cwd
    return root


def load_document_registry(root=ESTATE_ROOT):
    path = _effective_root(root) / "data" / "registry" / "documents.json"
    return json.loads(path.read_text(encoding="utf-8"))


def validate_document_registry(root=ESTATE_ROOT):
    root = _effective_root(root)
    registry = load_document_registry(root)
    documents = registry.get("documents", [])
    ids = [doc.get("id") for doc in documents]
    duplicate_ids = sorted({doc_id for doc_id in ids if ids.count(doc_id) > 1})
    missing_paths = []
    schema_errors = []
    required_fields = {
        "id",
        "title",
        "path",
        "category",
        "status",
        "audience",
        "source_of_truth",
        "notes",
        "superseded_paths",
        "resolved",
    }

    for index, doc in enumerate(documents):
        missing_fields = sorted(required_fields - set(doc))
        if missing_fields:
            schema_errors.append({"index": index, "id": doc.get("id"), "missing_fields": missing_fields})
        if doc.get("resolved") and not (root / doc.get("path", "")).exists():
            missing_paths.append(doc.get("path"))

    stale_constitution_current = [
        doc.get("id")
        for doc in documents
        if doc.get("path") == "constitution/Estate_Constitution.md"
    ]

    return {
        "ok": not duplicate_ids and not missing_paths and not schema_errors and not stale_constitution_current,
        "registry_path": str(Path("data/registry/documents.json")),
        "document_count": len(documents),
        "duplicate_ids": duplicate_ids,
        "missing_paths": missing_paths,
        "schema_errors": schema_errors,
        "stale_constitution_current": stale_constitution_current,
    }


def format_document_registry(registry):
    lines = [registry.get("title", "Estate Document Registry")]
    lines.append(f"Schema version: {registry.get('schema_version')}")
    lines.append(f"Documents: {len(registry.get('documents', []))}")
    for doc in registry.get("documents", []):
        marker = "resolved" if doc.get("resolved") else "unresolved"
        lines.append(f"{doc['id']} | {doc['title']} | {doc['path']} | {marker}")
    return "\n".join(lines)
