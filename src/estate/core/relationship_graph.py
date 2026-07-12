"""Privacy-filtered resident relationship graph runtime."""
from __future__ import annotations
import json, hashlib
from pathlib import Path
from estate.core.paths import ESTATE_ROOT
from estate.core.resident_registry_snapshot import build_resident_registry_snapshot

def _root(root=None): return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())
def _key(v): return str(v or "").lower().replace(" ","-").strip("-")
PUBLIC = {
    ("alfred","helen"): "executive coordination and workforce-development partner",
    ("alfred","grace"): "attention-gate and operations sequencing collaborator",
    ("helen","grace"): "workforce fit and operations coordination collaborator",
    ("ingrid","alfred"): "privacy/classification boundary advisor to Chief-of-Staff coordination",
    ("ingrid","evelyn"): "privacy guard for Steward Relationship Layer boundaries",
}
PRIVATE = {("evelyn","steward"): "protected intimate Steward-confidant continuity"}

def load_relationship_context(resident, *, surface_id="resident", root=None):
    snap=build_resident_registry_snapshot(root); key=_key(resident); edges=[]; redactions=[]
    active={_key(r.get("name")) for r in snap.get("active_residents",[])}
    for (a,b),desc in PUBLIC.items():
        if key in {a,b} and a in active and b in active:
            edges.append({"from":a,"to":b,"relationship_type":"professional","scope":"public","description":desc,"source":"data/registry/residents.json"})
    for (a,b),desc in PRIVATE.items():
        if key in {a,b} and not surface_id.startswith(("conference","room")):
            edges.append({"from":a,"to":b,"relationship_type":"personal","scope":"restricted","description":desc,"source":"docs/residents/evelyn/Evelyn_Relationship_Map_v0_1.md"})
        elif key in {a,b}:
            redactions.append({"edge":[a,b],"reason":"restricted relationship edge excluded from shared surface"})
    payload={"schema_version":"resident_relationship_graph.v1","resident_key":key,"edges":edges,"redactions":redactions,"change_policy":"conversation cannot silently promote durable relationship state","diagnostics":snap.get("conflicts",[])}
    payload["graph_hash"]=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()[:16]
    return payload
