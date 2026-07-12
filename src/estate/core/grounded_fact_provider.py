"""Read-only grounded Estate fact provider."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from estate.core.resident_registry_snapshot import build_resident_registry_snapshot
from estate.core.resident_mail_bus import list_mailbox

def get_grounded_facts(resident, *, surface_id="resident", root=None, domains=None):
    domains=set(domains or ["registry","mailbox","work_packages"]); facts=[]; diagnostics=[]
    if "registry" in domains:
        snap=build_resident_registry_snapshot(root); facts.append({"key":"registry.active_residents","value":[r["name"] for r in snap["active_residents"]],"source":"data/registry/residents.json","verification_state":"verified","disclosure_scope":"directory"}); diagnostics += snap.get("conflicts",[])
    if "mailbox" in domains and not surface_id.startswith(("conference","room")):
        try: mb=list_mailbox(resident, root=root); facts.append({"key":"mailbox.summary","value":{"message_count":mb["message_count"]},"source":"collaboration/messages","verification_state":"verified","disclosure_scope":"resident"})
        except Exception as exc: facts.append({"key":"mailbox.summary","value":"unknown","verification_state":"unknown","source":"collaboration/messages","diagnostic":str(exc)})
    if "work_packages" in domains:
        base=Path(root) if root else Path.cwd(); pending=base/"collaboration/work_packages/pending"; facts.append({"key":"work_packages.pending_count","value":len(list(pending.glob("WP-*.md"))) if pending.exists() else "unknown","source":"collaboration/work_packages/pending","verification_state":"derived"})
    return {"schema_version":"grounded_estate_facts.v1","facts":facts,"diagnostics":diagnostics,"failed_closed":bool(diagnostics)}
