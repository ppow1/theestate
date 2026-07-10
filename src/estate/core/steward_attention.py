"""Steward attention management and executive briefing service.

Alfred owns this gatekeeping surface, but this module only reads existing Estate
artifacts and persists local attention actions. It is not an event bus, task
queue, router, or authority source.
"""
from __future__ import annotations

import hashlib, json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_task_visibility import build_resident_task_board

ATTENTION_SCHEMA_VERSION = "steward_attention_item.v1"
BRIEFING_SCHEMA_VERSION = "steward_attention_briefing.v1"
ACTIONS_PATH = Path("runtime/office/steward_attention_actions.json")
ITEMS_PATH = Path("runtime/office/steward_attention_items.json")
BRIEFING_PATH = Path("runtime/office/steward_attention_briefing.json")
REPORT_PATH = Path("operations/briefings/steward_attention_briefing.md")
PRIVATE_KEYS = {"private_journal", "detailed_workforce_assessment", "health_notes", "confidential_notes", "worker_record", "personnel_private"}
CLASS_ORDER = {"urgent": 0, "decision_required": 1, "attention_soon": 2, "watch": 3, "routine": 4, "informational": 5}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default

def _write_json(root: Path, rel: Path, payload: Any) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def _rel(root: Path, path: Path) -> str:
    try: return str(path.relative_to(root)).replace("\\", "/")
    except ValueError: return str(path)

def _digest(parts: list[Any]) -> str:
    return hashlib.sha256("|".join(str(p or "") for p in parts).encode()).hexdigest()[:16]

def _parse_dt(value: Any) -> datetime | None:
    if not value: return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None

def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items() if k not in PRIVATE_KEYS}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    return value

def _item(source: str, key: str, title: str, summary: str, classification: str, owner: str, action: str, *, deadline: str | None = None, timestamp: str | None = None, source_links: list[str] | None = None, should_know: bool = True, must_decide: bool = False, details: dict[str, Any] | None = None) -> dict[str, Any]:
    item_id = "attn_" + _digest([source, key, classification, owner, action])
    return {"schema_version": ATTENTION_SCHEMA_VERSION, "id": item_id, "dedupe_key": f"{source}:{key}", "title": title, "summary": summary, "classification": classification, "owner": owner, "requested_steward_action": action, "deadline": deadline, "timestamp": timestamp or _now(), "source_links": source_links or [], "should_know": should_know, "must_decide": must_decide, "details": _sanitize(details or {}), "status": "open"}

def _class_for_resident(row: dict[str, Any]) -> str:
    if row.get("waiting_on") in {"steward", "Steward"} or row.get("escalation_state") == "attention_needed": return "decision_required" if row.get("waiting_on") else "attention_soon"
    if row.get("status") == "blocked": return "attention_soon"
    if row.get("stale_status"): return "watch"
    if row.get("unread_message_count"): return "routine"
    return "informational"

def _resident_items(root: Path) -> list[dict[str, Any]]:
    board = build_resident_task_board(root)
    out=[]
    for row in board.get("participants", []):
        cls = _class_for_resident(row)
        if cls == "informational": continue
        must = cls == "decision_required"
        out.append(_item("resident_task_status", row.get("resident_id") or row.get("resident_name"), f"{row.get('resident_name')} needs attention", row.get("blocker") or row.get("current_task") or "Resident status update", cls, row.get("task_owner") or row.get("resident_name") or "Alfred", "decide" if must else "review", deadline=row.get("next_checkpoint"), timestamp=row.get("source_last_updated"), source_links=row.get("source_links") or [], must_decide=must, details=row))
    return out

def _work_package_items(root: Path) -> list[dict[str, Any]]:
    out=[]
    for state, cls, action in [("pending", "decision_required", "approve, defer, or assign"), ("open", "attention_soon", "review blocked work")]:
        d=root/"collaboration"/"work_packages"/state
        if d.exists():
            for p in sorted(d.glob("WP-*.md"))[:50]:
                wp=p.stem.split("_")[0]
                out.append(_item("work_package", wp, f"{wp} {state}", p.stem, cls, "Alfred", action, source_links=[_rel(root,p)], must_decide=state=="pending"))
    return out

def _validation_items(root: Path) -> list[dict[str, Any]]:
    data=_read_json(root/"runtime/validation/local_operational_validation_latest.json", {}) or _read_json(root/"runtime/validation/local_operational_validation_run.json", {})
    summary=data.get("summary", {}) if isinstance(data, dict) else {}
    failures=int(summary.get("failure_count") or summary.get("error_count") or 0)
    if not failures: return []
    return [_item("validation", "local_operational_validation", "Local validation has failures", f"{failures} validation failures/errors reported", "urgent", "Operations", "review failures before approving related work", timestamp=data.get("generated_at"), source_links=["runtime/validation/local_operational_validation_latest.json", "runtime/validation/local_operational_validation_run.json"], details={"summary": summary})]

def _mail_items(root: Path) -> list[dict[str, Any]]:
    items=[]
    for p in sorted((root/"collaboration/messages").glob("*.json"))[:200]:
        msg=_read_json(p,{})
        if msg.get("status","open") in {"closed","archived"} or msg.get("ack_status") == "acknowledged": continue
        pr = msg.get("priority", "normal")
        cls = "attention_soon" if pr in {"high","urgent"} else "routine"
        payload=msg.get("payload", {}) if isinstance(msg.get("payload"), dict) else {}
        items.append(_item("mail", msg.get("id") or p.stem, payload.get("title") or msg.get("message_type") or "Open message", payload.get("summary") or "Open Estate message", cls, msg.get("destination") or "Alfred", "acknowledge or delegate", timestamp=msg.get("created_at"), source_links=[_rel(root,p)], details=msg))
    return items

def _load_actions(root: Path) -> dict[str, Any]:
    return _read_json(root/ACTIONS_PATH, {"schema_version":"steward_attention_actions.v1","actions":[]})

def _apply_actions(root: Path, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions=_load_actions(root).get("actions", [])
    latest={a.get("item_id"): a for a in actions if isinstance(a,dict)}
    now=datetime.now(timezone.utc)
    out=[]
    for item in items:
        act=latest.get(item["id"])
        if act:
            item["last_action"] = act
            if act.get("action") in {"acknowledge","dismiss","resolve","delegate"}: item["status"] = act.get("action") + "d"
            if act.get("action") == "snooze":
                until=_parse_dt(act.get("until"))
                item["status"] = "snoozed" if until and until > now else "open"
        if item["status"] not in {"dismissed", "resolved"}: out.append(item)
    return out

def aggregate_attention(root: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    base=_root(root)
    raw=_resident_items(base)+_work_package_items(base)+_validation_items(base)+_mail_items(base)
    merged={}
    for item in raw:
        key=item["dedupe_key"]
        if key in merged:
            merged[key]["source_links"] = sorted(set(merged[key]["source_links"] + item["source_links"]))
            merged[key].setdefault("related_updates", []).append(item["id"])
            if CLASS_ORDER[item["classification"]] < CLASS_ORDER[merged[key]["classification"]]: merged[key].update({k:item[k] for k in ["classification","requested_steward_action","must_decide"]})
        else: merged[key]=item
    items=sorted(_apply_actions(base, list(merged.values())), key=lambda x:(CLASS_ORDER[x["classification"]], x.get("deadline") or "9999", x["title"]))
    payload={"schema_version":"steward_attention_aggregate.v1","generated_at":_now(),"owner":"Alfred","non_authoritative":True,"items":items,"summary":{"total":len(items),"must_decide":sum(1 for i in items if i["must_decide"]),"should_know":sum(1 for i in items if i["should_know"] and not i["must_decide"]),"by_classification":{c:sum(1 for i in items if i["classification"]==c) for c in CLASS_ORDER}}}
    if write: _write_json(base, ITEMS_PATH, payload)
    return payload

def create_briefing(kind: str = "on_demand", root: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    agg=aggregate_attention(root, write=write); base=_root(root)
    items=agg["items"]
    if kind == "morning": selected=[i for i in items if i["classification"] != "informational"][:20]
    elif kind == "exception": selected=[i for i in items if i["classification"] in {"urgent","decision_required"}]
    else: selected=items[:50]
    briefing={"schema_version":BRIEFING_SCHEMA_VERSION,"briefing_type":kind,"generated_at":_now(),"owner":"Alfred","gatekeeping_boundary":"Alfred batches attention; source systems remain authoritative.","steward_must_decide":[i for i in selected if i["must_decide"]],"steward_should_know":[i for i in selected if not i["must_decide"]],"routine_batch":[i for i in items if i["classification"]=="routine"][:10],"summary":agg["summary"]}
    if write:
        _write_json(base, BRIEFING_PATH, briefing)
        (base/REPORT_PATH).parent.mkdir(parents=True, exist_ok=True); (base/REPORT_PATH).write_text(format_briefing(briefing), encoding="utf-8")
    return briefing

def record_action(item_id: str, action: str, actor: str = "steward", root: str | Path | None = None, *, until: str | None = None, delegate_to: str | None = None, note: str | None = None) -> dict[str, Any]:
    if action not in {"snooze","acknowledge","delegate","dismiss","resolve"}: raise ValueError("unsupported attention action")
    base=_root(root); payload=_load_actions(base)
    rec={"action_id":"attact_"+_digest([item_id, action, actor, _now()]),"item_id":item_id,"action":action,"actor":actor,"recorded_at":_now(),"until":until,"delegate_to":delegate_to,"note":note,"transport":"Office action transport"}
    payload.setdefault("actions", []).append(rec); _write_json(base, ACTIONS_PATH, payload); aggregate_attention(base, write=True)
    return rec

def format_briefing(briefing: dict[str, Any]) -> str:
    lines=["# Steward Attention Briefing", "", f"Generated at: {briefing.get('generated_at')}", f"Type: {briefing.get('briefing_type')}", "", briefing.get("gatekeeping_boundary",""), "", "## Steward must decide"]
    for i in briefing.get("steward_must_decide",[]): lines.append(f"- **{i['classification']}** {i['title']} — {i['requested_steward_action']} ({', '.join(i.get('source_links') or [])})")
    lines += ["", "## Steward should know"]
    for i in briefing.get("steward_should_know",[]): lines.append(f"- **{i['classification']}** {i['title']} — {i['summary']}")
    lines += ["", "## Routine batch", f"- {len(briefing.get('routine_batch', []))} routine items batched.", ""]
    return "\n".join(lines)
