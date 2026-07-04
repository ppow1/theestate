"""Capability dependency visualization for Mission Control.

This module builds a read-only projection from the Estate Capability Registry
and explicit dependency graph artifacts. It does not infer new dependencies;
missing or partial dependency data is rendered as warnings and isolated nodes.
"""

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from estate.core.dependency_graph import generate_dependency_graph
from estate.core.estate_capability_registry import generate_estate_capability_registry
from estate.core.paths import ESTATE_ROOT


def _root(root=None):
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _source_exists(root, rel):
    return bool(rel) and (root / rel).exists()


def _load_registry(root, warnings):
    path = root / "runtime" / "capabilities" / "estate_capability_registry.json"
    if path.exists():
        try:
            return _read_json(path), "runtime/capabilities/estate_capability_registry.json"
        except Exception as exc:
            warnings.append({"type": "malformed_registry_projection", "path": str(path), "message": str(exc)})
    return generate_estate_capability_registry(root, write=False), "data/registry/capabilities.json"


def _load_graph(root, warnings):
    path = root / "runtime" / "dependencies" / "dependency_graph.json"
    if path.exists():
        try:
            return _read_json(path), "runtime/dependencies/dependency_graph.json"
        except Exception as exc:
            warnings.append({"type": "malformed_dependency_projection", "path": str(path), "message": str(exc)})
    return generate_dependency_graph(root, write=False), "explicit_dependency_scan"


def _status_bucket(cap):
    maturity = str(cap.get("maturity") or "").lower()
    validation = str(cap.get("validation_status") or "").lower()
    state = str(cap.get("lifecycle_state") or cap.get("implementation_status") or "unknown")
    if maturity == "operational" or validation in {"valid", "evidence_found"}:
        readiness = "ready"
    elif validation in {"warnings", "evidence_gaps"}:
        readiness = "warning"
    elif state.lower() in {"unknown", "none", ""}:
        readiness = "unknown"
    else:
        readiness = "partial"
    return readiness


def generate_capability_dependency_visualization(root=None, write=True):
    """Build a read-only capability dependency visualization payload."""
    root = _root(root)
    warnings = []
    registry, registry_source = _load_registry(root, warnings)
    graph, graph_source = _load_graph(root, warnings)
    capabilities = [c for c in registry.get("capabilities", []) if isinstance(c, dict)]
    caps_by_id = {cap.get("id"): cap for cap in capabilities if cap.get("id")}

    upstream = defaultdict(list)
    downstream = defaultdict(list)
    explicit_edges = []
    edge_keys = set()

    raw_dependency_presence = {}
    raw_path = root / "data" / "registry" / "capabilities.json"
    if raw_path.exists():
        try:
            raw_data = _read_json(raw_path)
            raw_items = raw_data.get("capabilities", raw_data) if isinstance(raw_data, dict) else raw_data
            for raw in raw_items if isinstance(raw_items, list) else []:
                if isinstance(raw, dict) and raw.get("id"):
                    raw_dependency_presence[raw.get("id")] = "dependencies" in raw
        except Exception as exc:
            warnings.append({"type": "malformed_capability_source", "path": "data/registry/capabilities.json", "message": str(exc)})

    def add_edge(source, target, dependency_type, source_artifact):
        key = (source, target)
        if key in edge_keys:
            return
        edge_keys.add(key)
        edge = {"source": source, "target": target, "dependency_type": dependency_type, "source_artifact": source_artifact}
        explicit_edges.append(edge)
        upstream[source].append(target)
        downstream[target].append(source)

    for cap in capabilities:
        deps = cap.get("dependencies")
        has_raw_dependency_field = raw_dependency_presence.get(cap.get("id"), deps is not None)
        if not has_raw_dependency_field:
            warnings.append({"type": "missing_capability_dependency_metadata", "capability_id": cap.get("id"), "message": "Capability has no dependency metadata field."})
        elif deps == []:
            warnings.append({"type": "empty_capability_dependency_metadata", "capability_id": cap.get("id"), "message": "Capability declares no explicit dependencies."})
        for dep in deps or []:
            add_edge(cap.get("id"), str(dep), "capability_registry.dependencies", "data/registry/capabilities.json")

    for edge in graph.get("edges", []) or []:
        if not isinstance(edge, dict):
            continue
        source = edge.get("source")
        target = edge.get("target")
        if source in caps_by_id or target in caps_by_id:
            candidate = {"source": source, "target": target, "dependency_type": edge.get("dependency_type"), "source_artifact": edge.get("source_artifact")}
            if candidate not in explicit_edges:
                add_edge(source, target, edge.get("dependency_type"), edge.get("source_artifact"))

    nodes = []
    for cap_id, cap in sorted(caps_by_id.items()):
        sources = list(cap.get("source_artifact_links") or [])
        if "data/registry/capabilities.json" not in sources:
            sources.insert(0, "data/registry/capabilities.json")
        node_warnings = list(cap.get("metadata_warnings") or [])
        for rel in sources:
            if rel and not _source_exists(root, rel):
                node_warnings.append({"type": "unresolved_source_link", "message": f"Source artifact is not present: {rel}"})
        if not (upstream.get(cap_id) or downstream.get(cap_id)):
            node_warnings.append({"type": "no_explicit_relationships", "message": "No explicit upstream or downstream dependency relationship is available."})
        nodes.append({
            "id": cap_id,
            "label": cap.get("name") or cap_id,
            "type": "capability",
            "readiness": _status_bucket(cap),
            "implementation_status": cap.get("implementation_status"),
            "lifecycle_state": cap.get("lifecycle_state"),
            "validation_status": cap.get("validation_status"),
            "upstream_dependencies": sorted(set(upstream.get(cap_id, []))),
            "downstream_dependents": sorted(set(downstream.get(cap_id, []))),
            "implementation_references": [s for s in sources if s != "data/registry/capabilities.json"],
            "authoritative_artifact": "data/registry/capabilities.json",
            "source_artifact_links": sources,
            "warnings": node_warnings,
        })

    external_refs = sorted(({e["source"] for e in explicit_edges} | {e["target"] for e in explicit_edges}) - set(caps_by_id))
    for ref in external_refs:
        nodes.append({
            "id": ref,
            "label": ref,
            "type": "external_reference",
            "readiness": "unknown",
            "implementation_status": "unknown",
            "lifecycle_state": None,
            "validation_status": "unknown",
            "upstream_dependencies": sorted(set(upstream.get(ref, []))),
            "downstream_dependents": sorted(set(downstream.get(ref, []))),
            "implementation_references": [],
            "authoritative_artifact": None,
            "source_artifact_links": [],
            "warnings": [{"type": "external_reference", "message": "Referenced by explicit dependency data but absent from the capability registry."}],
        })

    readiness_counts = defaultdict(int)
    for node in nodes:
        readiness_counts[node["readiness"]] += 1
    payload = {
        "version": 1,
        "generated_at": _now(),
        "authority": "read_only_visualization_not_source_of_truth",
        "mission_control_ready": True,
        "operations_center_integration": {"panel_id": "capability_dependency_visualization", "recommended_tab": "mission-control", "read_only": True},
        "inputs": {"registry": registry_source, "dependency_graph": graph_source},
        "summary": {"node_count": len(nodes), "capability_node_count": len(caps_by_id), "edge_count": len(explicit_edges), "warning_count": len(warnings) + sum(len(n.get("warnings", [])) for n in nodes), "readiness_counts": dict(sorted(readiness_counts.items()))},
        "nodes": nodes,
        "edges": explicit_edges,
        "warnings": warnings,
        "limitations": ["Only explicit capability registry dependencies and explicit dependency graph edges are shown.", "No dependency is inferred from prose, naming, ordering, implementation references, or service names.", "Missing dependency metadata creates warnings and isolated nodes rather than fabricated edges."],
    }
    if write:
        _write_json(root / "runtime" / "capabilities" / "capability_dependency_visualization.json", payload)
        out = root / "operations" / "capabilities" / "capability_dependency_visualization.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(format_capability_dependency_visualization(payload) + "\n", encoding="utf-8")
    return payload


def format_capability_dependency_visualization(payload):
    s = payload.get("summary", {})
    lines = [
        "# Capability Dependency Visualization",
        "",
        "Read-only visualization for Mission Control and architectural review. This artifact is not a source of truth.",
        "",
        f"Generated: {payload.get('generated_at')}",
        "",
        "## Summary",
        f"- Nodes: {s.get('node_count', 0)}",
        f"- Capability nodes: {s.get('capability_node_count', 0)}",
        f"- Edges: {s.get('edge_count', 0)}",
        f"- Warnings: {s.get('warning_count', 0)}",
        f"- Readiness: {s.get('readiness_counts', {})}",
        "",
        "## Nodes",
    ]
    for node in payload.get("nodes", []):
        links = ", ".join(f"`{link}`" for link in node.get("source_artifact_links") or []) or "No registry link available"
        lines += [
            "",
            f"### {node.get('label')} ({node.get('id')})",
            f"- Type: {node.get('type')}",
            f"- Readiness: {node.get('readiness')}",
            f"- Implementation state: {node.get('implementation_status')}",
            f"- Lifecycle state: {node.get('lifecycle_state')}",
            f"- Validation state: {node.get('validation_status')}",
            f"- Upstream dependencies: {', '.join(node.get('upstream_dependencies') or []) or 'None explicitly recorded'}",
            f"- Downstream dependents: {', '.join(node.get('downstream_dependents') or []) or 'None explicitly recorded'}",
            f"- Authoritative artifact: `{node.get('authoritative_artifact') or 'unresolved external reference'}`",
            f"- Source links: {links}",
        ]
        for warning in node.get("warnings") or []:
            lines.append(f"  - Warning: {warning.get('type')} — {warning.get('message')}")
    lines += ["", "## Edges"]
    if payload.get("edges"):
        lines.extend(f"- `{e.get('source')}` -> `{e.get('target')}` ({e.get('dependency_type')}) — `{e.get('source_artifact')}`" for e in payload.get("edges", []))
    else:
        lines.append("- No explicit capability dependency edges were found.")
    lines += ["", "## Limitations"]
    lines.extend(f"- {item}" for item in payload.get("limitations", []))
    if payload.get("warnings"):
        lines += ["", "## Warnings"]
        lines.extend(f"- {w.get('type')}: {w.get('message')}" for w in payload.get("warnings", []))
    return "\n".join(lines)


def format_capability_dependency_visualization_summary(payload):
    s = payload.get("summary", {})
    return "\n".join([
        "Capability Dependency Visualization",
        f"Generated: {payload.get('generated_at')}",
        f"Nodes: {s.get('node_count', 0)}",
        f"Edges: {s.get('edge_count', 0)}",
        f"Warnings: {s.get('warning_count', 0)}",
    ])
