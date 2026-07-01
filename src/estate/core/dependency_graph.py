"""Dependency graph generation for explicit Estate artifact dependencies.

The generator only records dependencies that are present in explicit fields or
clearly labelled Markdown dependency sections. It intentionally does not infer
relationships from prose similarity or naming conventions.
"""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

JSON_INPUTS = [
    "collaboration/messages/*.json",
    "runtime/operations/operations_board.json",
    "runtime/capabilities/capability_lifecycle_report.json",
    "data/registry/capabilities.json",
    "data/registry/services.json",
]

MARKDOWN_INPUTS = [
    "collaboration/work_packages/**/*.md",
    "operations/**/*.md",
]

DEPENDENCY_KEYS = {
    "dependencies",
    "depends_on",
    "dependency_ids",
    "dependency_id",
    "blocked_by",
    "requires",
    "required_capabilities",
    "required_services",
    "work_package_dependencies",
}

ID_KEYS = ("id", "work_package_id", "capability_id", "service_id", "message_id", "name", "title")
LABELLED_DEPENDENCY_HEADING = re.compile(r"^#{1,6}\s+(?:explicit\s+)?(?:dependencies|depends on|blocked by|requires|required capabilities|required services)\s*$", re.I)
HEADING = re.compile(r"^#{1,6}\s+")
FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
FIELD_LINE = re.compile(r"^(dependencies|depends_on|dependency_ids|blocked_by|requires|required_capabilities|required_services)\s*:\s*(.+)$", re.I)
BULLET_ID = re.compile(r"^\s*[-*]\s+(?:\[[ xX]\]\s*)?(?:`([^`]+)`|([^\s:;,()]+))(?:\s*[:;,(-]\s*(.*))?$")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def estate_root(root=None):
    if root is not None:
        return Path(root)
    if ESTATE_ROOT.exists():
        return ESTATE_ROOT
    return Path.cwd()


def _rel(path, root):
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _git_value(root, *args):
    try:
        result = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
        return result.stdout.strip() or None
    except Exception:
        return None


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _as_items(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "capabilities", "services", "messages", "work_packages", "nodes"):
            if isinstance(data.get(key), list):
                return data[key]
        return [data]
    return []


def _stringify_id(value):
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        for key in ("id", "ref", "dependency", "target", "name"):
            if key in value:
                return _stringify_id(value.get(key))
    return None


def _item_id(item, fallback):
    if isinstance(item, dict):
        for key in ID_KEYS:
            value = _stringify_id(item.get(key))
            if value:
                return value
    return fallback


def _dependency_values(value):
    if value is None:
        return []
    if isinstance(value, (str, int, float, dict)):
        return [value]
    if isinstance(value, list):
        return value
    return []


def _extract_json(root, path, graph):
    rel = _rel(path, root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        graph["warnings"].append({"type": "malformed_json", "path": rel, "message": str(exc)})
        return

    graph["inputs"]["used"].append(rel)
    for index, item in enumerate(_as_items(data)):
        if not isinstance(item, dict):
            continue
        node_id = _item_id(item, f"{rel}#{index}")
        _add_node(graph, node_id, _node_kind_from_path(rel), rel, item.get("name") or item.get("title"))
        found = False
        for key, value in item.items():
            if key in DEPENDENCY_KEYS:
                found = True
                for dep in _dependency_values(value):
                    target = _stringify_id(dep)
                    if target:
                        _add_edge(graph, node_id, target, key, rel)
                    else:
                        graph["warnings"].append({"type": "malformed_reference", "path": rel, "message": f"Dependency field {key} contains an unrecognized reference."})
        if not found:
            graph["warnings"].append({"type": "missing_dependency_field", "path": rel, "message": f"{node_id} has no explicit dependency field."})


def _node_kind_from_path(rel):
    if "work_packages" in rel:
        return "work_package"
    if "capabilities" in rel:
        return "capability"
    if "services" in rel:
        return "service"
    if "messages" in rel:
        return "message"
    if rel.startswith("operations/") or "/operations" in rel:
        return "operation"
    return "artifact"


def _add_node(graph, node_id, kind, source, label=None):
    graph["_node_ids"].add(node_id)
    graph["_nodes"].setdefault(node_id, {"id": node_id, "type": kind, "label": label or node_id, "source_artifact": source})


def _add_edge(graph, source, target, dependency_type, artifact):
    graph["edges"].append({"source": source, "target": target, "dependency_type": dependency_type, "source_artifact": artifact})
    if target not in graph["_node_ids"]:
        _add_node(graph, target, "external_reference", artifact, target)


def _split_inline_deps(text):
    text = text.strip().strip("[]")
    if not text or text.lower() in {"none", "n/a", "na"}:
        return []
    return [part.strip().strip('"\'`') for part in re.split(r"[,;]", text) if part.strip()]


def _extract_markdown(root, path, graph):
    rel = _rel(path, root)
    text = path.read_text(encoding="utf-8")
    graph["inputs"]["used"].append(rel)
    fallback_id = path.stem
    node_id = fallback_id
    title = None
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            node_id = title or fallback_id
            break
    fm = FRONT_MATTER.match(text)
    if fm:
        for line in fm.group(1).splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                if key.strip().lower() in ID_KEYS:
                    node_id = value.strip().strip('"\'') or node_id
    _add_node(graph, node_id, _node_kind_from_path(rel), rel, title)

    found = False
    for line in text.splitlines():
        match = FIELD_LINE.match(line.strip())
        if match:
            found = True
            for dep in _split_inline_deps(match.group(2)):
                _add_edge(graph, node_id, dep, match.group(1).lower(), rel)

    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not LABELLED_DEPENDENCY_HEADING.match(line.strip()):
            continue
        found = True
        dep_type = line.strip().lstrip("#").strip().lower().replace(" ", "_")
        for body_line in lines[i + 1:]:
            if HEADING.match(body_line):
                break
            if not body_line.strip():
                continue
            bullet = BULLET_ID.match(body_line)
            if bullet:
                target = (bullet.group(1) or bullet.group(2) or "").strip()
                if target.lower() not in {"none", "n/a", "na"}:
                    _add_edge(graph, node_id, target, dep_type, rel)
            elif body_line.lstrip().startswith(("-", "*")):
                graph["warnings"].append({"type": "malformed_reference", "path": rel, "message": f"Could not parse dependency line: {body_line.strip()}"})
    if not found:
        graph["warnings"].append({"type": "missing_dependency_field", "path": rel, "message": f"{node_id} has no clearly labelled dependency section or field."})


def generate_dependency_graph(root=None, write=True):
    root = estate_root(root)
    graph = {
        "version": 1,
        "generated_at": _now(),
        "repository": {"branch": _git_value(root, "rev-parse", "--abbrev-ref", "HEAD"), "commit": _git_value(root, "rev-parse", "HEAD")},
        "inputs": {"used": [], "unavailable": []},
        "nodes": [],
        "edges": [],
        "orphaned_items": [],
        "warnings": [],
        "schema": {
            "nodes": "id, type, label, source_artifact",
            "edges": "source, target, dependency_type, source_artifact",
            "orphaned_items": "nodes with no incoming or outgoing explicit dependency edges",
        },
        "_nodes": {},
        "_node_ids": set(),
    }
    for pattern in JSON_INPUTS:
        paths = sorted(root.glob(pattern))
        if not paths:
            graph["inputs"]["unavailable"].append(pattern)
            graph["warnings"].append({"type": "missing_optional_artifact", "path": pattern, "message": "Optional input artifact is unavailable."})
        for path in paths:
            _extract_json(root, path, graph)
    for pattern in MARKDOWN_INPUTS:
        paths = sorted(p for p in root.glob(pattern) if "operations/dependencies/dependency_graph.md" not in _rel(p, root))
        if not paths:
            graph["inputs"]["unavailable"].append(pattern)
            graph["warnings"].append({"type": "missing_optional_artifact", "path": pattern, "message": "Optional input artifact is unavailable."})
        for path in paths:
            _extract_markdown(root, path, graph)

    connected = {e["source"] for e in graph["edges"]} | {e["target"] for e in graph["edges"]}
    graph["nodes"] = sorted(graph["_nodes"].values(), key=lambda n: n["id"])
    graph["orphaned_items"] = [n for n in graph["nodes"] if n["id"] not in connected]
    graph["summary"] = {"node_count": len(graph["nodes"]), "edge_count": len(graph["edges"]), "orphaned_item_count": len(graph["orphaned_items"]), "warning_count": len(graph["warnings"])}
    del graph["_nodes"]
    del graph["_node_ids"]
    if write:
        _write_json(root / "runtime" / "dependencies" / "dependency_graph.json", graph)
        md = format_dependency_graph_markdown(graph)
        out = root / "operations" / "dependencies" / "dependency_graph.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md + "\n", encoding="utf-8")
    return graph


def format_dependency_graph_summary(graph):
    s = graph.get("summary", {})
    return "\n".join([
        "Estate Dependency Graph",
        f"Generated: {graph.get('generated_at')}",
        f"Nodes: {s.get('node_count', 0)}",
        f"Edges: {s.get('edge_count', 0)}",
        f"Orphaned items: {s.get('orphaned_item_count', 0)}",
        f"Warnings: {s.get('warning_count', 0)}",
    ])


def format_dependency_graph_markdown(graph):
    s = graph.get("summary", {})
    lines = [
        "# Estate Dependency Graph",
        "",
        "Machine-readable output: `runtime/dependencies/dependency_graph.json`.",
        "",
        "## Summary",
        f"- Generated: {graph.get('generated_at')}",
        f"- Nodes: {s.get('node_count', 0)}",
        f"- Edges: {s.get('edge_count', 0)}",
        f"- Orphaned items: {s.get('orphaned_item_count', 0)}",
        f"- Warnings: {s.get('warning_count', 0)}",
        "",
        "## Supported dependency sources",
        "- JSON fields: `dependencies`, `depends_on`, `dependency_ids`, `dependency_id`, `blocked_by`, `requires`, `required_capabilities`, `required_services`, `work_package_dependencies`.",
        "- Markdown front matter or lines using those same field names.",
        "- Markdown sections clearly headed `Dependencies`, `Depends On`, `Blocked By`, `Requires`, `Required Capabilities`, or `Required Services`.",
        "",
        "## Graph schema",
        "- `nodes`: `{id, type, label, source_artifact}`.",
        "- `edges`: `{source, target, dependency_type, source_artifact}`.",
        "- `warnings`: missing optional inputs, malformed JSON, malformed references, and artifacts without explicit dependency fields.",
        "- `orphaned_items`: nodes with no incoming or outgoing explicit dependency edges.",
        "",
        "## CLI usage",
        "- `python -m estate.cli.main dependency-graph` writes JSON and Markdown and prints a summary.",
        "- `python -m estate.cli.main dependency-graph --json` writes outputs and prints the JSON graph.",
        "",
        "## Limitations",
        "- Only explicit fields and clearly labelled dependency sections are captured.",
        "- The generator does not infer hidden dependencies from wording, similarity, order, or proximity.",
        "- Missing inputs produce warnings rather than failures.",
        "",
        "## Edges",
    ]
    if graph.get("edges"):
        for edge in graph["edges"]:
            lines.append(f"- `{edge['source']}` -> `{edge['target']}` ({edge['dependency_type']}) — {edge['source_artifact']}")
    else:
        lines.append("- No explicit dependency edges found.")
    lines.extend(["", "## Orphaned items"])
    for node in graph.get("orphaned_items", []):
        lines.append(f"- `{node['id']}` ({node['type']}) — {node['source_artifact']}")
    if not graph.get("orphaned_items"):
        lines.append("- No orphaned items.")
    lines.extend(["", "## Warnings"])
    for warning in graph.get("warnings", []):
        lines.append(f"- {warning.get('type')}: {warning.get('path')} — {warning.get('message')}")
    if not graph.get("warnings"):
        lines.append("- No warnings.")
    return "\n".join(lines)
