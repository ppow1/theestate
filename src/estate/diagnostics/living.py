"""Deterministic implementation provenance and living-cookbook maintenance.

The module deliberately has no model/provider import.  Reasoned maintenance is
represented as durable pending work; an Estate capability router may consume it.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

VERSION = "1.0.0"
ROOTS = ("src", "tools", "scripts", "docs", "standards", "schemas", "collaboration", "operations")
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules", "browser_profiles", "runtime", "generated", "evidence", "secrets", "credentials"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".pid", ".lock", ".key", ".pem", ".p12", ".sqlite", ".db"}
SOURCE = Path("docs/operations/troubleshooting/cookbook.json")
GENERATED = Path("docs/operations/troubleshooting/generated")
SCHEMA = Path("schemas/troubleshooting/implementation_manifest_v1.schema.json")
PACKET_SCHEMA = Path("schemas/troubleshooting/diagnostic_impact_packet_v1.schema.json")
ACCEPTED_MANIFEST = Path("operations/diagnostics/accepted-implementation-manifest.json")
BASELINE_HISTORY = Path("operations/diagnostics/accepted-implementation-manifest.history.jsonl")
COMPONENTS = {
    "continuous_momentum_engine": ("src/estate/core/continuous_momentum_engine.py", "src/estate/core/cme_"),
    "comms8": ("src/estate/core/comms8", "src/estate/comms8"),
    "consultation_store": ("src/estate/core/consultation",),
    "reason_execute_orchestration": ("src/estate/core/execution", "src/estate/core/reason"),
    "model_control": ("src/estate/model_control/",),
    "resident_gateway": ("src/estate/core/resident_gateway", "src/estate/core/resident_interaction"),
    "work_package_system": ("collaboration/work_packages/",),
    "ptm": ("src/estate/ptm/", "schemas/ptm/"),
    "audit": ("src/estate/core/audit", "audit/"),
    "discovery": ("src/estate/core/estate_discovery", "config/discovery/"),
    "living_diagnostics": ("src/estate/diagnostics/", "tools/estate_diagnostics", "docs/operations/troubleshooting/", "schemas/troubleshooting/"),
}


def utc_now() -> str:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    dt = datetime.fromtimestamp(int(epoch), timezone.utc) if epoch else datetime.now(timezone.utc)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root: Path, *args: str, check: bool = False) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if check and result.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed")
    return result.stdout.rstrip()


def excluded(path: Path) -> bool:
    lower = {part.lower() for part in path.parts}
    return bool(lower & EXCLUDED_PARTS) or path.suffix.lower() in EXCLUDED_SUFFIXES or any(token in path.name.lower() for token in ("token", "cookie", "password", "secret"))


def component_for(path: str) -> str | None:
    return next((component for component, prefixes in COMPONENTS.items() if any(path.startswith(prefix) for prefix in prefixes)), None)


def artifact_type(path: Path) -> str:
    return {".py":"python", ".ps1":"powershell", ".js":"javascript", ".html":"html", ".css":"css", ".json":"json", ".yaml":"yaml", ".yml":"yaml", ".sql":"sql", ".md":"markdown"}.get(path.suffix.lower(), "other")


def enumerate_artifacts(root: Path) -> list[Path]:
    files: list[Path] = []
    for governed in ROOTS:
        base = root / governed
        if base.exists():
            files.extend(p for p in base.rglob("*") if p.is_file() and not excluded(p.relative_to(root)) and p.relative_to(root) not in {ACCEPTED_MANIFEST, BASELINE_HISTORY})
    return sorted(set(files), key=lambda p: p.relative_to(root).as_posix())


def generate_manifest(root: Path, generated_at: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    head = git(root, "rev-parse", "HEAD") or "UNKNOWN"
    branch = git(root, "branch", "--show-current") or "DETACHED"
    porcelain = git(root, "status", "--porcelain=v1", "--untracked-files=all").splitlines()
    raw_changed = {line[3:].split(" -> ")[-1].replace("\\", "/") for line in porcelain if len(line) > 3}
    changed = sorted(path for path in raw_changed if path.split("/", 1)[0] in ROOTS and not excluded(Path(path)))
    tracked_blobs = {}
    for line in git(root, "ls-files", "--stage").splitlines():
        if "\t" in line:
            metadata, path = line.split("\t", 1); tracked_blobs[path] = metadata.split()[1]
    # One history walk supplies provenance for every tracked artifact.  Do not
    # turn this into one Git subprocess per file: an Estate checkout has tens
    # of thousands of governed files.
    last_commits: dict[str, tuple[str, str]] = {}
    history = git(root, "log", "--format=@@%H%x00%cI", "--name-only", "--", *ROOTS)
    commit_sha = commit_time = "UNKNOWN"
    for line in history.splitlines():
        if line.startswith("@@"):
            values = line[2:].split("\x00", 1)
            commit_sha, commit_time = values[0], values[1] if len(values) > 1 else "UNKNOWN"
        elif line and line not in last_commits:
            last_commits[line] = (commit_sha, commit_time)
    artifacts = []
    for file in enumerate_artifacts(root):
        rel = file.relative_to(root).as_posix()
        tracked = rel in tracked_blobs
        blob = tracked_blobs.get(rel, "LOCAL_REVISION")
        component = component_for(rel)
        schema_version = None
        if file.suffix == ".json" and "schema" in file.name.lower():
            try:
                data = json.loads(file.read_text(encoding="utf-8")); schema_version = data.get("$id") or data.get("version")
            except (ValueError, OSError):
                schema_version = "UNKNOWN"
        artifacts.append({
            "path": rel, "artifact_type": artifact_type(file), "content_hash": f"sha256:{sha256(file)}",
            "git_blob_sha": blob or "UNKNOWN", "state": "UNTRACKED" if not tracked else ("MODIFIED" if rel in changed else "TRACKED"),
            "last_commit_sha": last_commits.get(rel, ("UNKNOWN", "UNKNOWN"))[0],
            "last_commit_timestamp": last_commits.get(rel, ("UNKNOWN", "UNKNOWN"))[1],
            "component_id": component or "NOT_MAPPED", "component_version": VERSION if component == "living_diagnostics" else "NOT_DECLARED",
            "interface_versions": [], "schema_version": schema_version or "NOT_APPLICABLE", "lineage": ["PL-0040"] if component == "living_diagnostics" else [],
        })
    return {"manifest_version":"1.0.0", "generated_at":generated_at or utc_now(), "generator_version":VERSION,
            "repository":root.name, "repository_revision":head, "branch":branch, "ref":head,
            "dirty_state":{"dirty":bool(changed), "changed_paths":changed}, "worktree_identity":str(root),
            "artifact_roots":list(ROOTS), "exclusion_rules":{"parts":sorted(EXCLUDED_PARTS), "suffixes":sorted(EXCLUDED_SUFFIXES), "sensitive_name_tokens":["token","cookie","password","secret"]},
            "components":[{"component_id":c,"version":VERSION if c == "living_diagnostics" else "NOT_DECLARED"} for c in sorted(COMPONENTS)], "artifacts":artifacts}


@dataclass
class DiagnosticsRepository:
    root: Path

    def source(self) -> dict[str, Any]:
        return json.loads((self.root / SOURCE).read_text(encoding="utf-8"))

    def generated(self, name: str) -> dict[str, Any]:
        return json.loads((self.root / GENERATED / name).read_text(encoding="utf-8"))

    def search(self, phrase: str) -> list[dict[str, Any]]:
        tokens = re.findall(r"[a-z0-9_]+", phrase.lower())
        ranked = []
        for item in self.generated("search-index.json")["entries"]:
            fields = {"failure_codes":6,"symptoms":5,"title":4,"keywords":3,"workflow":2,"probe_summary":1,"recovery_summary":1}
            score = sum(weight * sum(token in " ".join(item.get(field, []) if isinstance(item.get(field), list) else [str(item.get(field, ""))]).lower() for token in tokens) for field, weight in fields.items())
            if score: ranked.append((score, item))
        return [item for _, item in sorted(ranked, key=lambda row:(-row[0], row[1]["checkpoint_id"]))]

    def checkpoint(self, checkpoint_id: str) -> dict[str, Any] | None:
        return next((x for x in self.generated("search-index.json")["entries"] if x["checkpoint_id"] == checkpoint_id), None)

    def affected(self, dependencies: Iterable[str]) -> list[dict[str, Any]]:
        needles = set(dependencies)
        return [x for x in self.generated("search-index.json")["entries"] if needles & set(x["source_dependencies"] + [x["component_id"]])]


def applicability(checkpoint: dict[str, Any], artifacts: dict[str, dict[str, Any]]) -> tuple[str, list[dict[str, str]]]:
    if checkpoint.get("status") == "PROPOSED": return "PROPOSED", []
    differences = []
    validated = checkpoint.get("validated_against", {}).get("files", {})
    for path in checkpoint.get("source_dependencies", []):
        current = artifacts.get(path)
        previous = validated.get(path)
        if current is None: differences.append({"dependency":path,"reason":"MISSING_DEPENDENCY","previous":str(previous or "UNKNOWN"),"current":"MISSING"})
        elif not previous: differences.append({"dependency":path,"reason":"VALIDATION_METADATA_MISSING","previous":"UNKNOWN","current":current["content_hash"]})
        elif previous != current["content_hash"]: differences.append({"dependency":path,"reason":"CONTENT_CHANGED","previous":previous,"current":current["content_hash"]})
    return ("REVALIDATION_REQUIRED" if differences else "VALIDATED"), differences


def _render_mermaid_svg(source: str) -> str:
    """Render the supported flowchart subset into an inline, offline SVG.

    The authored Mermaid remains the portable diagram contract, while the HTML
    contains graphical nodes and edges rather than an unprocessed source block.
    """
    nodes_in_source = re.findall(r"([A-Za-z0-9_]+)(?:\[([^]]+)\])?", source.split("\n", 1)[-1])
    labels: dict[str, str] = {}
    ordered: list[str] = []
    pairs: list[tuple[str, str]] = []
    for node, label in nodes_in_source:
        if node not in ordered: ordered.append(node)
        if label: labels[node] = label
    pairs = list(zip(ordered, ordered[1:]))
    if not ordered:
        return '<p class="warning">Diagram could not be rendered from the supported Mermaid flowchart subset.</p>'
    width, box_w, gap, y = max(760, len(ordered) * 170), 140, 30, 35
    positions = {node: (20 + i * (box_w + gap), y) for i, node in enumerate(ordered)}
    lines = []
    for left, right in pairs:
        x1, y1 = positions[left]; x2, y2 = positions[right]
        lines.append(f'<line x1="{x1+box_w}" y1="{y1+35}" x2="{x2}" y2="{y2+35}" marker-end="url(#arrow)"/>')
    nodes = [f'<g><rect x="{x}" y="{ny}" width="{box_w}" height="70" rx="8"/><text x="{x+box_w/2}" y="{ny+41}" text-anchor="middle">{html.escape(labels.get(node, node))}</text></g>' for node, (x, ny) in positions.items()]
    return f'<svg class="process-diagram" role="img" aria-label="Seven-step troubleshooting process" viewBox="0 0 {width} 140" xmlns="http://www.w3.org/2000/svg"><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z"/></marker></defs>{"".join(lines)}{"".join(nodes)}</svg>'


def _render_html(source: dict[str, Any], manifest: dict[str, Any], entries: list[dict[str, Any]], report: dict[str, Any]) -> str:
    counts = report["checkpoint_counts"]
    cards = []
    for cp in entries:
        failures = ", ".join(cp["failure_codes"]) or "none"
        warning = '<p class="warning">Dependency changed: revalidation required. Do not treat this guidance as proven.</p>' if cp["status"] == "REVALIDATION_REQUIRED" else ""
        cards.append(f'''<article id="{html.escape(cp['checkpoint_id'])}"><h2>{html.escape(cp['checkpoint_id'])} — {html.escape(cp['title'])}</h2><span class="badge {cp['status'].lower()}">{cp['status']}</span>{warning}<p><b>Workflow:</b> {html.escape(cp['workflow'])} · <b>Subsystem:</b> {html.escape(cp['subsystem'])}</p><p><b>Expected:</b> {html.escape(cp['expected_input'])} → {html.escape(cp['expected_output'])}</p><p><b>Authority:</b> {html.escape(cp['authority'])}</p><p><b>Probe:</b> {html.escape(cp['probe_summary'])}</p><p><b>Smallest safe recovery:</b> {html.escape(cp['recovery_summary'])}</p><p><b>Do not:</b> {html.escape('; '.join(cp['prohibited_actions']))}</p><p><b>Failure codes:</b> {html.escape(failures)}</p><details><summary>Applicability / provenance</summary><pre>{html.escape(canonical_json({'checkpoint_revision':cp['checkpoint_revision'],'validated_against':cp['validated_against'],'current_repository_revision':manifest['repository_revision'],'differences':cp['differences'],'knowledge_provenance':cp['knowledge_provenance']}))}</pre></details></article>''')
    options = "".join(f'<li><a href="#{html.escape(x["checkpoint_id"])}">{html.escape(x["checkpoint_id"])} {html.escape(x["title"])}</a></li>' for x in entries)
    diagram = _render_mermaid_svg(source['diagrams']['seven_step'])
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Estate Living Troubleshooting</title><style>body{{font:16px system-ui;max-width:1100px;margin:auto;padding:2rem;background:#f7f8fa;color:#172033}}@media(prefers-color-scheme:dark){{body{{background:#10141d;color:#edf1f7}}article,.panel{{background:#181f2b}}a{{color:#8fc7ff}}}}article,.panel{{background:canvas;border:1px solid #8893a4;border-radius:10px;padding:1rem;margin:1rem 0}}.badge{{padding:.25rem .6rem;border-radius:1rem;background:#cdd5df}}.validated{{background:#9be3b0}}.revalidation_required,.unknown{{background:#ffd078}}.proposed{{background:#c7b8ff}}.warning{{border-left:5px solid #d97706;padding:.7rem;background:#fff2ce;color:#4b3100}}input{{width:100%;padding:.7rem}}pre{{white-space:pre-wrap}}.diagram-scroll{{overflow-x:auto}}.process-diagram{{min-width:760px;width:100%;height:auto}}.process-diagram rect{{fill:#e8f1ff;stroke:#315a8a;stroke-width:2}}.process-diagram line{{stroke:#315a8a;stroke-width:2}}.process-diagram text{{fill:#172033;font:14px system-ui}}@media print{{input,script{{display:none}}}}</style></head><body><h1>START HERE WHEN SOMETHING IS BROKEN</h1><p>Identify the workflow; find the last proven checkpoint and next unproven checkpoint; inspect its authority; run the narrow probe; repair the smallest boundary; validate downstream recovery; preserve evidence.</p><section class="panel"><h2>Freshness</h2><p>Repository <code>{manifest['repository_revision']}</code> · branch <code>{html.escape(manifest['branch'])}</code> · {'DIRTY' if manifest['dirty_state']['dirty'] else 'clean'} · generated {manifest['generated_at']}</p><p>Cookbook {source['document_revision']} · VALIDATED {counts.get('VALIDATED',0)} · REVALIDATION_REQUIRED {counts.get('REVALIDATION_REQUIRED',0)} · STALE/UNKNOWN {counts.get('STALE',0)+counts.get('UNKNOWN',0)} · PROPOSED {counts.get('PROPOSED',0)}</p></section><input id="q" placeholder="Search checkpoints"><nav><h2>Workflow navigation</h2><ul id="nav">{options}</ul></nav><section class="panel diagram-scroll" data-diagram-language="mermaid"><h2>Seven-step process</h2>{diagram}<details><summary>Mermaid source</summary><pre>{html.escape(source['diagrams']['seven_step'])}</pre></details></section>{''.join(cards)}<script>const q=document.querySelector('#q');q.oninput=()=>document.querySelectorAll('article').forEach(x=>x.hidden=!x.innerText.toLowerCase().includes(q.value.toLowerCase()));</script></body></html>'''


def build(root: Path, generated_at: str | None = None, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    root = root.resolve(); started = time.perf_counter(); out = root / GENERATED; out.mkdir(parents=True, exist_ok=True)
    manifest = manifest or generate_manifest(root, generated_at)
    source = DiagnosticsRepository(root).source(); artifacts = {x["path"]:x for x in manifest["artifacts"]}; entries=[]
    for cp in source["checkpoints"]:
        state, differences = applicability(cp, artifacts)
        item = dict(cp); item["status"] = state; item["differences"] = differences; item["source_document"] = SOURCE.as_posix(); entries.append(item)
    entries.sort(key=lambda x:x["checkpoint_id"])
    counts = {status:sum(x["status"] == status for x in entries) for status in ("VALIDATED","REVALIDATION_REQUIRED","STALE","UNKNOWN","PROPOSED")}
    report = {"report_version":"1.0.0","generated_at":manifest["generated_at"],"mode":"build","implementation_state":"CURRENT_LOCAL_STATE","checkpoint_counts":counts,"pending_reasoning_review":sum(x["status"] == "REVALIDATION_REQUIRED" for x in entries),"reasoning_provider_required":False,"provider_independence":"Stage 1 completed without an AI provider","duration_seconds":0}
    index = {"index_version":"1.0.0","generated_at":manifest["generated_at"],"entries":entries}
    for name, payload in (("implementation-manifest.json",manifest),("search-index.json",index),("freshness-report.json",report)):
        (out/name).write_text(canonical_json(payload),encoding="utf-8")
    (out/"index.html").write_text(_render_html(source,manifest,entries,report),encoding="utf-8")
    return {"artifact_count":len(manifest["artifacts"]),"checkpoint_count":len(entries),"checkpoint_counts":counts,"output":str(out),"duration_seconds":round(time.perf_counter()-started,3)}


def _validate_manifest(payload: Any) -> list[str]:
    errors = []
    required = {"manifest_version", "generated_at", "repository", "repository_revision", "artifacts"}
    if not isinstance(payload, dict): return ["baseline must be a JSON object"]
    errors.extend(f"missing required field: {key}" for key in sorted(required - payload.keys()))
    if payload.get("manifest_version") != "1.0.0": errors.append("manifest_version must be 1.0.0")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list): errors.append("artifacts must be an array")
    elif any(not isinstance(x, dict) or not isinstance(x.get("path"), str) or not isinstance(x.get("content_hash"), str) for x in artifacts): errors.append("every artifact requires string path and content_hash")
    return errors


def validate_impact_packet(payload: Any) -> list[str]:
    """Validate the safety-critical packet contract without optional packages."""
    if not isinstance(payload, dict): return ["packet must be a JSON object"]
    allowed = {"packet_version","change_id","work_package_id","estate_change_id","author_provenance","changed_files","changed_components","changed_interfaces","changed_schemas","behavior_before","behavior_after","expected_inputs","expected_outputs","dependencies_read","dependencies_called","resources_written","new_failure_modes","changed_failure_modes","removed_failure_modes","new_or_changed_logs","new_or_changed_status_codes","tests_added_or_changed","validation_evidence","recommended_checkpoint_impacts","preliminary_troubleshooting_notes","prohibited_recovery_actions","activation_restart_impact","source_revision","confidence"}
    required = {"packet_version","change_id","author_provenance","changed_files","source_revision","confidence"}
    errors = [f"missing required field: {x}" for x in sorted(required - payload.keys())]
    errors += [f"unknown field: {x}" for x in sorted(payload.keys() - allowed)]
    if payload.get("packet_version") != "1.0.0": errors.append("packet_version must be 1.0.0")
    for field in ("change_id", "source_revision"):
        if not isinstance(payload.get(field), str) or not payload.get(field, "").strip(): errors.append(f"{field} must be a non-empty string")
    provenance = payload.get("author_provenance")
    if not isinstance(provenance, dict) or not isinstance(provenance.get("kind"), str): errors.append("author_provenance.kind is required")
    changed = payload.get("changed_files")
    if not isinstance(changed, list) or not changed or any(not isinstance(x, str) or not x or x.startswith("/") or ".." in Path(x).parts or "\\" in x for x in changed): errors.append("changed_files must contain safe repository-relative paths")
    if payload.get("confidence") not in {"PROVEN","SUPPORTED","CANDIDATE","UNKNOWN"}: errors.append("confidence is invalid")
    array_fields = allowed - {"packet_version","change_id","work_package_id","estate_change_id","author_provenance","behavior_before","behavior_after","activation_restart_impact","source_revision","confidence"}
    for field in array_fields:
        if field in payload and not isinstance(payload[field], list): errors.append(f"{field} must be an array")
    return errors


def advance_accepted_baseline(root: Path, *, actor: str, reason: str, expected_revision: str | None = None) -> dict[str, Any]:
    """Explicitly initialize/advance the accepted implementation baseline."""
    root = root.resolve(); destination = root / ACCEPTED_MANIFEST
    current = generate_manifest(root)
    if expected_revision and current["repository_revision"] != expected_revision:
        raise ValueError("current repository revision does not match expected revision")
    previous_revision = None
    action = "INITIALIZED"
    if destination.exists():
        try: previous = json.loads(destination.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc: raise ValueError(f"existing accepted baseline is unreadable: {exc}") from exc
        errors = _validate_manifest(previous)
        if errors: raise ValueError("existing accepted baseline is invalid: " + "; ".join(errors))
        previous_revision = previous["repository_revision"]; action = "ADVANCED"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(canonical_json(current), encoding="utf-8")
    event = {"event_version":"1.0.0","action":action,"accepted_at":utc_now(),"actor":actor,"reason":reason,"previous_revision":previous_revision,"accepted_revision":current["repository_revision"],"manifest_sha256":"sha256:"+sha256(destination)}
    history = root / BASELINE_HISTORY; history.parent.mkdir(parents=True, exist_ok=True)
    with history.open("a", encoding="utf-8") as handle: handle.write(json.dumps(event, sort_keys=True)+"\n")
    return {**event, "accepted_manifest":ACCEPTED_MANIFEST.as_posix(), "history":BASELINE_HISTORY.as_posix()}


def reconcile(root: Path, accepted_manifest: Path | None = None, packets: Iterable[Path] = (), mode: str = "full") -> dict[str, Any]:
    root=root.resolve(); baseline_path = accepted_manifest or root / ACCEPTED_MANIFEST
    if not baseline_path.is_absolute(): baseline_path = root / baseline_path
    if not baseline_path.exists():
        return {"mode":mode,"reconciliation_outcome":"ACCEPTED_BASELINE_MISSING","classifications":["ACCEPTED_BASELINE_MISSING"],"baseline_valid":False,"impact_packets_consumed":0,"invalid_impact_packets":[],"provider_independence":"Stage 1 failed closed without an AI provider"}
    try: baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"mode":mode,"reconciliation_outcome":"ACCEPTED_BASELINE_INVALID","classifications":["ACCEPTED_BASELINE_INVALID"],"baseline_valid":False,"baseline_errors":[str(exc)],"impact_packets_consumed":0,"invalid_impact_packets":[],"provider_independence":"Stage 1 failed closed without an AI provider"}
    baseline_errors = _validate_manifest(baseline)
    if baseline_errors:
        return {"mode":mode,"reconciliation_outcome":"ACCEPTED_BASELINE_INVALID","classifications":["ACCEPTED_BASELINE_INVALID"],"baseline_valid":False,"baseline_errors":baseline_errors,"impact_packets_consumed":0,"invalid_impact_packets":[],"provider_independence":"Stage 1 failed closed without an AI provider"}
    previous={x["path"]:x for x in baseline["artifacts"]}
    current=generate_manifest(root); now={x["path"]:x for x in current["artifacts"]}
    changed=sorted(p for p in set(previous)|set(now) if previous.get(p,{}).get("content_hash") != now.get(p,{}).get("content_hash"))
    packet_data=[]; invalid_packets=[]
    for packet_path in packets:
        try: packet = json.loads(packet_path.read_text(encoding="utf-8")); errors = validate_impact_packet(packet)
        except (OSError, ValueError) as exc: packet = {}; errors = [str(exc)]
        if errors: invalid_packets.append({"path":str(packet_path),"errors":errors})
        else: packet_data.append(packet)
    covered={p for packet in packet_data for p in packet.get("changed_files",[])}
    result=build(root,manifest=current)
    repo=DiagnosticsRepository(root); affected=repo.affected(changed)
    report=repo.generated("freshness-report.json")
    classifications=[]
    if invalid_packets: classifications.append("INVALID_DIAGNOSTIC_IMPACT_PACKET")
    if set(changed)-covered: classifications.append("CHANGE_WITHOUT_DIAGNOSTIC_IMPACT_METADATA")
    report.update({"mode":mode,"accepted_baseline":str(baseline_path),"accepted_revision":baseline["repository_revision"],"baseline_valid":True,"changed_artifacts":changed,"affected_checkpoints":[x["checkpoint_id"] for x in affected],"impact_packets_consumed":len(packet_data),"invalid_impact_packets":invalid_packets,"classifications":classifications,"pending_candidate_knowledge":[p.get("change_id") for p in packet_data],"reconciliation_outcome":"IMPLEMENTATION_UNCHANGED" if not changed else "REVALIDATION_REQUIRED","canonical_knowledge_auto_modified":False})
    (root/GENERATED/"freshness-report.json").write_text(canonical_json(report),encoding="utf-8")
    return {**result,**report}
