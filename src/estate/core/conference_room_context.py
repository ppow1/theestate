"""Governed conference-room context assembly and disclosure metadata."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from estate.core.resident_registry_snapshot import build_resident_registry_snapshot
from estate.core.relationship_graph import load_relationship_context

def _now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def assemble_conference_room_context(participants, *, room_id="conference-room", session_id=None, root=None, room_history=None, disclosure_scope="Estate Internal", current_moderator=None, backup_moderator=None):
    snap=build_resident_registry_snapshot(root); active={str(r.get('name')).lower():r for r in snap.get('active_residents',[])}
    canonical=[]; diagnostics=list(snap.get('conflicts',[])); redactions=[]
    for p in participants:
        rec=active.get(str(p).lower())
        if not rec: diagnostics.append({"type":"unknown_or_inactive_participant","participant":p}); continue
        canonical.append({"resident_id":rec.get('id'),"name":rec.get('name'),"office":rec.get('office')})
        rel=load_relationship_context(rec.get('name'), surface_id='conference-room', root=root); redactions += rel.get('redactions',[])
    canonical_ids={str(item["name"]).lower() for item in canonical}
    for role, holder in (("current_moderator",current_moderator),("backup_moderator",backup_moderator)):
        if holder and str(holder).lower() not in canonical_ids:
            diagnostics.append({"type":"role_holder_not_active","role":role,"resident":holder})
    return {"schema_version":"conference_room_context.v1","room_id":room_id,"session_id":session_id or str(uuid.uuid4()),"assembled_at":_now(),"participants":canonical,"conference_roles":{"current_moderator":current_moderator,"backup_moderator":backup_moderator},"disclosure_scope":disclosure_scope,"room_history":list(room_history or [])[-20:],"private_history_imported":False,"relationship_context":"public_relationship_edges_only","disclosure_decisions":{"redactions":redactions},"diagnostics":diagnostics,"failed_closed":bool(diagnostics)}
