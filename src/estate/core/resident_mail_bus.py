"""Governed resident mail and conversation bus over Estate mailboxes."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.collaboration_events import append_event
from estate.core.collaboration_messages import acknowledge_message, create_reply, group_threads
from estate.core.mailbox_index import generate_mailbox_index, load_functional_mailbox_registry, load_personnel_registry, resolve_destination
from estate.core.paths import ESTATE_ROOT

SCHEMA_VERSION = "estate.communication_bus.v1"
RESTRICTED_CLASSIFICATIONS = {"confidential", "restricted", "private", "personal", "undercroft"}
ARCHIVED_STATUSES = {"closed", "archived"}

def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def _write_json(path: Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)

def _slug(value: Any) -> str:
    chars=[]; prev=False
    for ch in str(value or "").strip().lower():
        if ch.isalnum(): chars.append(ch); prev=False
        elif not prev: chars.append("_"); prev=True
    return "".join(chars).strip("_") or "message"

def _body_allowed(message: dict[str, Any]) -> bool:
    c=str(message.get("classification", "")).lower()
    return not any(flag in c for flag in RESTRICTED_CLASSIFICATIONS)

def _messages_dir(root: Path) -> Path:
    return root / "collaboration" / "messages"

def _load_messages(root: Path) -> list[dict[str, Any]]:
    items=[]
    for path in sorted(_messages_dir(root).glob("*.json")):
        try: m=_read_json(path, {})
        except Exception: continue
        if isinstance(m, dict):
            m["_path"] = str(path.relative_to(root)).replace("\\", "/")
            items.append(m)
    return items

def _identity_aliases(identity: dict[str, Any]) -> set[str]:
    aliases=set()
    for key in ("employee_id", "mailbox_id"):
        if identity.get(key) is not None:
            aliases.add(str(identity[key])); aliases.add(f"{key.split('_')[0]}.{identity[key]}")
    if identity.get("mailbox_id") is not None:
        aliases.add(f"mailbox.{identity['mailbox_id']}")
    for key in ("display_name", "current_title", "current_office", "resident_id"):
        val=identity.get(key)
        if val:
            aliases.add(str(val)); aliases.add(_slug(val)); aliases.add(f"office.{_slug(val)}"); aliases.add(f"employee.{_slug(val)}"); aliases.add(f"resident.{_slug(val)}")
    return {a.lower() for a in aliases if a}

def resolve_identity(actor: str, root: str | Path | None = None) -> dict[str, Any]:
    base=_root(root); norm=str(actor or "").strip().lower()
    personnel=load_personnel_registry(base); mailboxes=load_functional_mailbox_registry(base)
    for p in personnel:
        if norm in _identity_aliases(p):
            return {"identity_type":"personnel", **p}
    for m in mailboxes:
        aliases={str(m.get("mailbox_id")), f"mailbox.{m.get('mailbox_id')}", str(m.get("display_name") or ""), str(m.get("owning_office") or ""), _slug(m.get("display_name")), f"office.{_slug(m.get('display_name'))}", f"office.{_slug(m.get('owning_office'))}", "steward" if m.get("mailbox_id")==1 else ""}
        if norm in {a.lower() for a in aliases if a}:
            return {"identity_type":"mailbox", **m}
    raise ValueError(f"identity does not resolve through personnel or mailbox registries: {actor}")

def _route_label(identity: dict[str, Any]) -> str:
    if identity.get("mailbox_id") is not None:
        return f"mailbox.{identity['mailbox_id']}"
    return identity.get("display_name") or identity.get("owning_office") or "unknown"

def _digest(sender: str, recipients: list[str], subject: str, body: str, thread_id: str | None, source_artifacts: list[str]) -> str:
    raw=json.dumps({"sender":sender,"recipients":recipients,"subject":subject,"body":body,"thread":thread_id,"artifacts":source_artifacts}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()

def send_message(sender: str, recipients: list[str] | str, subject: str, body: str, *, classification: str="Estate Internal", message_type: str="resident_mail", priority: str="normal", thread_id: str | None=None, source_artifacts: list[str] | None=None, requires_ack: bool=True, root: str | Path | None=None) -> dict[str, Any]:
    base=_root(root); source_artifacts=source_artifacts or []
    if isinstance(recipients, str): recipients=[recipients]
    src=resolve_identity(sender, base); dsts=[resolve_identity(r, base) for r in recipients]
    fingerprint=_digest(sender, recipients, subject, body, thread_id, source_artifacts)
    for existing in _load_messages(base):
        if existing.get("delivery", {}).get("dedupe_key") == fingerprint:
            return {"delivered": False, "duplicate": True, "message": existing, "path": existing.get("_path")}
    msg_id=f"msg_bus_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{fingerprint[:10]}"
    message={"id":msg_id,"schema_version":SCHEMA_VERSION,"version":1,"created_at":_now(),"created_by":sender,"source":_route_label(src),"source_identity":{"display_name":src.get("display_name"),"employee_id":src.get("employee_id"),"mailbox_id":src.get("mailbox_id"),"resident_id":src.get("resident_id"),"identity_type":src.get("identity_type")},"destination":_route_label(dsts[0]),"destination_identity":{"display_name":dsts[0].get("display_name"),"employee_id":dsts[0].get("employee_id"),"mailbox_id":dsts[0].get("mailbox_id"),"resident_id":dsts[0].get("resident_id"),"identity_type":dsts[0].get("identity_type")},"recipients":[{"label":r,"mailbox_id":d.get("mailbox_id"),"employee_id":d.get("employee_id"),"display_name":d.get("display_name") or d.get("display_name")} for r,d in zip(recipients,dsts)],"classification":classification,"message_type":message_type,"priority":priority,"status":"open","requires_ack":requires_ack,"ack_status":"pending" if requires_ack else "not_required","thread_id":thread_id or msg_id,"routing":{"supports":["resident-to-resident","resident-to-office","office-to-resident","steward-directed"],"transport":"existing collaboration/messages and collaboration/mailboxes index","authority":"delivery does not grant authority"},"delivery":{"status":"delivered","delivered_at":_now(),"dedupe_key":fingerprint,"destination_mailbox_ids":[d.get("mailbox_id") for d in dsts]},"payload":{"title":subject,"summary":body,"body":body,"artifact_refs":source_artifacts}}
    path=Path(_write_json(_messages_dir(base)/f"{msg_id}.json", message)).relative_to(base)
    generate_mailbox_index(base)
    try: append_event("communication_bus.message_delivered", sender, {"message_id":msg_id,"recipients":recipients}, subject_id=msg_id, root=base)
    except Exception: pass
    return {"delivered": True, "duplicate": False, "message": message, "path": str(path)}

def list_mailbox(actor: str, folder: str="inbox", *, include_body: bool=False, root: str | Path | None=None) -> dict[str, Any]:
    base=_root(root); ident=resolve_identity(actor, base); mailbox_id=ident.get("mailbox_id")
    rows=[]
    for m in _load_messages(base):
        dest=m.get("destination_identity",{}).get("mailbox_id") or m.get("delivery",{}).get("destination_mailbox_ids",[None])[0]
        src=m.get("source_identity",{}).get("mailbox_id")
        status=str(m.get("status","")).lower()
        if folder=="sent" and src!=mailbox_id: continue
        if folder=="archive" and not (dest==mailbox_id and status in ARCHIVED_STATUSES): continue
        if folder in {"inbox","unread","acknowledgment"} and dest!=mailbox_id: continue
        if folder=="unread" and (status in ARCHIVED_STATUSES or m.get("ack_status")=="acknowledged"): continue
        if folder=="acknowledgment" and not m.get("requires_ack"): continue
        payload=m.get("payload") if isinstance(m.get("payload"), dict) else {}
        item={"message_id":m.get("id") or m.get("message_id"),"thread_id":m.get("thread_id"),"classification":m.get("classification"),"created_at":m.get("created_at"),"source":m.get("source"),"destination":m.get("destination"),"status":m.get("status"),"ack_status":m.get("ack_status"),"title":payload.get("title"),"summary":payload.get("summary") if _body_allowed(m) else "Restricted content omitted.","path":m.get("_path")}
        if include_body and _body_allowed(m): item["body"]=payload.get("body") or payload.get("summary")
        rows.append(item)
    return {"actor": actor, "mailbox_id": mailbox_id, "folder": folder, "message_count": len(rows), "messages": rows}

def unread_count(actor: str, root: str | Path | None=None) -> int:
    return list_mailbox(actor, "unread", root=root)["message_count"]

def inspect_thread(thread_id: str, *, include_body: bool=False, root: str | Path | None=None) -> dict[str, Any]:
    base=_root(root); messages=[]
    for m in _load_messages(base):
        if (m.get("thread_id") or m.get("id")) == thread_id:
            payload=m.get("payload") if isinstance(m.get("payload"), dict) else {}
            item={"message_id":m.get("id"),"reply_to":m.get("reply_to"),"acknowledges":m.get("acknowledges"),"classification":m.get("classification"),"created_at":m.get("created_at"),"title":payload.get("title"),"summary":payload.get("summary") if _body_allowed(m) else "Restricted content omitted.","path":m.get("_path")}
            if include_body and _body_allowed(m): item["body"]=payload.get("body") or payload.get("summary")
            messages.append(item)
    return {"thread_id": thread_id, "message_count": len(messages), "messages": messages}

def notification_summary(actor: str, root: str | Path | None=None) -> dict[str, Any]:
    inbox=list_mailbox(actor, "inbox", root=root)
    return {"actor":actor,"unread_count":unread_count(actor, root),"attention":[{k:m[k] for k in ("message_id","thread_id","classification","title","summary") if k in m} for m in inbox["messages"][:10]],"privacy":"restricted bodies are omitted from summaries"}

def acknowledge_bus_message(message_id: str, actor: str="Alfred", note: str="Acknowledged.", root: str | Path | None=None) -> dict[str, Any]:
    result=acknowledge_message(message_id, actor=actor, note=note, root=_root(root)); generate_mailbox_index(_root(root)); return result

def reply_bus_message(message_id: str, actor: str="Alfred", body: str="", title: str | None=None, root: str | Path | None=None) -> dict[str, Any]:
    result=create_reply(message_id, actor=actor, body=body, title=title, root=_root(root)); generate_mailbox_index(_root(root)); return result

def office_integrations(root: str | Path | None=None) -> dict[str, Any]:
    base=_root(root)
    return {"alfred_attention": notification_summary("Alfred", base), "helen_workforce_notices": notification_summary("Helen", base), "grace_operational_directives": notification_summary("Grace", base), "office_mailbox_index": str((base/"collaboration/mailboxes/index.json").relative_to(base)), "privacy":"summaries only; message bodies follow classification gates"}
