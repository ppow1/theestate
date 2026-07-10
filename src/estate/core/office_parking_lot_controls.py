"""Canonical planning control adapter for Office Parking Lot and Roadmap surfaces."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.operations_control_runtime import OperationsControlRuntime
from estate.core.operations_manager import OperationsDecision

PARKING_LOT = Path("operations/boards/parking_lot.md")
ROADMAP = Path("operations/boards/roadmap.md")
UNDO = Path("runtime/steward/planning_control_surface_last_change.json")
AUDIT = Path("runtime/steward/planning_control_surface_events.jsonl")

PARKING_COLUMNS = ["ID", "Idea", "Category", "Priority", "Originator", "Date Captured", "Status", "Target Milestone", "Promotion Condition"]
ROADMAP_COLUMNS = ["Capability", "Current Milestone", "Status", "Key Dependency", "Future Initiative"]
PRIORITIES = {"Low", "Normal", "High", "Strategic"}
STATUSES = {"Captured", "Clarify Later", "Reconsider", "Promoted", "Closed", "Archived"}

@dataclass
class PlanningResult:
    outcome: str
    message: str
    artifacts_read: list[str]
    artifacts_written: list[str]
    runtime_state_changed: list[str]
    data: dict[str, Any]

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _root(root: str | Path | None) -> Path:
    return Path(root) if root is not None else Path.cwd()

def _rel(path: Path) -> str:
    return str(path).replace("\\", "/")

def _split_table(text: str, heading: str) -> tuple[str, list[str], str]:
    lines = text.splitlines()
    h = next((i for i,l in enumerate(lines) if l.strip().lower() == f"## {heading}".lower()), None)
    if h is None: raise ValueError(f"Missing heading: {heading}")
    start = next((i for i in range(h+1, len(lines)) if lines[i].strip().startswith("|")), None)
    if start is None or start + 1 >= len(lines): raise ValueError(f"Missing table under {heading}")
    end = start
    while end < len(lines) and lines[end].strip().startswith("|"):
        end += 1
    return "\n".join(lines[:start]), lines[start:end], "\n".join(lines[end:])

def _parse_row(line: str) -> list[str]:
    return [c.strip().replace("\\|", "|") for c in line.strip().strip("|").split("|")]

def _escape(v: Any) -> str:
    return str(v or "").replace("|", "\\|").replace("\n", " ").strip()

def _load_table(root: Path, rel: Path, heading: str) -> tuple[str, list[str], list[dict[str, str]], str, str]:
    path = root / rel
    text = path.read_text(encoding="utf-8")
    before, table, after = _split_table(text, heading)
    columns = _parse_row(table[0])
    rows = [dict(zip(columns, _parse_row(line))) for line in table[2:]]
    return text, columns, rows, before, after

def _write_table(root: Path, rel: Path, heading: str, columns: list[str], rows: list[dict[str, str]], before: str, after: str) -> None:
    path = root / rel
    sep = "|" + "|".join("---" for _ in columns) + "|"
    lines = ["| " + " | ".join(columns) + " |", sep]
    lines += ["| " + " | ".join(_escape(row.get(c, "")) for c in columns) + " |" for row in rows]
    content = before.rstrip() + "\n" + "\n".join(lines) + "\n" + after.lstrip("\n")
    path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")

def _save_undo(root: Path, surface: str, rel: Path, before: str, after: str, item_id: str | None, action: str) -> None:
    p = root / UNDO; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"surface":surface,"path":_rel(rel),"before":before,"after":after,"item_id":item_id,"action":action,"created_at":_now()}, indent=2, sort_keys=True)+"\n", encoding="utf-8")

def _audit(root: Path, payload: dict[str, Any]) -> None:
    p = root / AUDIT; p.parent.mkdir(parents=True, exist_ok=True)
    p.open("a", encoding="utf-8").write(json.dumps({"timestamp":_now(), **payload}, sort_keys=True)+"\n")

def _next_pl(rows: list[dict[str,str]]) -> str:
    nums = [int(m.group(1)) for r in rows if (m:=re.fullmatch(r"PL-(\d+)", r.get("ID", "")))]
    return f"PL-{(max(nums) if nums else 0)+1:04d}"

def _find(rows, item_id):
    for i,r in enumerate(rows):
        if r.get("ID") == item_id or r.get("Capability") == item_id:
            return i,r
    raise ValueError(f"Unknown item: {item_id}")

def parking_action(root=None, action: str = "", item_id: str | None = None, **params: Any) -> PlanningResult:
    base = _root(root); rel = PARKING_LOT; before, cols, rows, prefix, suffix = _load_table(base, rel, "Parking Lot Items")
    old = before; msg = "updated"; changed = True
    if action == "create":
        iid = params.get("item_id") or _next_pl(rows); rows.append({"ID":iid,"Idea":params.get("idea","Untitled idea"),"Category":params.get("category","Uncategorized"),"Priority":params.get("priority","Normal"),"Originator":params.get("owner") or params.get("originator","Steward"),"Date Captured":params.get("date_captured") or _now()[:10],"Status":"Captured","Target Milestone":params.get("target_milestone", ""),"Promotion Condition":params.get("notes") or params.get("promotion_condition","")}); item_id=iid; msg=f"Created {iid}"
    elif action == "edit":
        i,row=_find(rows,item_id); mapping={"idea":"Idea","category":"Category","priority":"Priority","owner":"Originator","originator":"Originator","status":"Status","target_milestone":"Target Milestone","notes":"Promotion Condition","promotion_condition":"Promotion Condition"}; [row.__setitem__(col, str(params[k])) for k,col in mapping.items() if k in params and params[k] is not None]; msg=f"Edited {item_id}"
    elif action in {"move_up","move_down"}:
        i,_=_find(rows,item_id); j=i-1 if action=="move_up" else i+1
        if j < 0 or j >= len(rows): return PlanningResult("blocked", "Item is already at that boundary.", [_rel(rel)], [], [], {"item_id":item_id})
        rows[i],rows[j]=rows[j],rows[i]; msg=f"Moved {item_id}"
    elif action == "reorder":
        order = params.get("order") or []
        if isinstance(order, str): order = [x.strip() for x in order.split(",") if x.strip()]
        known = {r["ID"]: r for r in rows}
        if set(order) != set(known): return PlanningResult("blocked", "Reorder must include every current Parking Lot ID exactly once.", [_rel(rel)], [], [], {})
        rows = [known[x] for x in order]; msg="Reordered Parking Lot"
    elif action == "set_priority":
        i,row=_find(rows,item_id); priority=str(params.get("priority") or "");
        if priority not in PRIORITIES: return PlanningResult("blocked", f"Invalid priority: {priority}", [_rel(rel)], [], [], {})
        row["Priority"]=priority; msg=f"Priority changed for {item_id}"
    elif action in {"accept","archive","reject","restore"}:
        i,row=_find(rows,item_id); row["Status"]={"accept":"Promoted","archive":"Archived","reject":"Closed","restore":"Captured"}[action]; msg=f"Status changed for {item_id}"
    elif action == "promote":
        i,row=_find(rows,item_id); dest=params.get("destination")
        if dest not in {"operations_control", "work_package_review"}: return PlanningResult("blocked", "Promotion destination must be an existing governed destination.", [_rel(rel)], [], [], {"destination":dest})
        decision = OperationsDecision.create(decided_by=params.get("decided_by") or "Steward", decision_type="reprioritize", target_type="work_package", target_id=item_id, priority=("high" if str(row.get("Priority") or "normal").lower() == "strategic" else str(row.get("Priority") or "normal").lower()), reason=f"Promote Parking Lot item through governed pathway: {row.get('Idea')}", assignment_label=params.get("assignment_label") or "Existing governed planning destination", requires_steward_attention=True, metadata={"destination":dest})
        paths = OperationsControlRuntime(base).record_decision(decision); row["Status"]="Promoted"; msg=f"Promoted {item_id} through operations control"; params["promotion_paths"]=[_rel(Path(v)) for v in paths.values()]
    else:
        return PlanningResult("blocked", f"Unsupported Parking Lot action: {action}", [_rel(rel)], [], [], {})
    _write_table(base, rel, "Parking Lot Items", cols, rows, prefix, suffix); after=(base/rel).read_text(encoding="utf-8"); _save_undo(base,"parking",rel,old,after,item_id,action); _audit(base,{"surface":"parking","action":action,"item_id":item_id})
    written=[_rel(rel), _rel(UNDO), _rel(AUDIT)] + params.get("promotion_paths", [])
    return PlanningResult("completed", msg, [_rel(rel)], written, ["planning artifact updated", "office targeted refresh requested"], {"item_id":item_id,"rows":rows})

def roadmap_action(root=None, action: str = "", item_id: str | None = None, **params: Any) -> PlanningResult:
    base=_root(root); rel=ROADMAP; before, cols, rows, prefix, suffix = _load_table(base, rel, "Roadmap"); old=before
    key="Capability"
    if action == "create": rows.append({"Capability":params.get("capability") or item_id or "New Capability","Current Milestone":params.get("milestone", "Planned"),"Status":params.get("status","Planned"),"Key Dependency":params.get("dependency", ""),"Future Initiative":params.get("future_initiative") or params.get("notes", "")}); item_id=rows[-1][key]
    elif action == "edit": i,row=_find(rows,item_id); mapping={"capability":"Capability","milestone":"Current Milestone","status":"Status","dependency":"Key Dependency","future_initiative":"Future Initiative","notes":"Future Initiative"}; [row.__setitem__(col, str(params[k])) for k,col in mapping.items() if k in params and params[k] is not None]
    elif action in {"move_up","move_down"}: i,_=_find(rows,item_id); j=i-1 if action=="move_up" else i+1; 
    else: j=None
    if action in {"move_up","move_down"}:
        if j < 0 or j >= len(rows): return PlanningResult("blocked", "Item is already at that boundary.", [_rel(rel)], [], [], {})
        rows[i],rows[j]=rows[j],rows[i]
    elif action == "reorder":
        order=params.get("order") or []
        if isinstance(order,str): order=[x.strip() for x in order.split(",") if x.strip()]
        known={r[key]:r for r in rows}
        if set(order)!=set(known): return PlanningResult("blocked", "Reorder must include every roadmap capability exactly once.", [_rel(rel)], [], [], {})
        rows=[known[x] for x in order]
    elif action == "set_priority":
        i,row=_find(rows,item_id); row["Status"] = params.get("priority") or params.get("status") or row.get("Status")
    elif action not in {"create","edit"}:
        return PlanningResult("blocked", f"Unsupported Roadmap action: {action}", [_rel(rel)], [], [], {})
    _write_table(base, rel, "Roadmap", cols, rows, prefix, suffix); after=(base/rel).read_text(encoding="utf-8"); _save_undo(base,"roadmap",rel,old,after,item_id,action); _audit(base,{"surface":"roadmap","action":action,"item_id":item_id})
    return PlanningResult("completed", f"Roadmap {action} completed", [_rel(rel)], [_rel(rel), _rel(UNDO), _rel(AUDIT)], ["planning artifact updated", "office targeted refresh requested"], {"item_id":item_id,"rows":rows})

def planning_undo(root=None) -> PlanningResult:
    base=_root(root); p=base/UNDO
    if not p.exists(): return PlanningResult("blocked", "No safe local planning change is available to undo.", [_rel(UNDO)], [], [], {})
    data=json.loads(p.read_text(encoding="utf-8")); rel=Path(data["path"]); (base/rel).write_text(data["before"], encoding="utf-8"); _audit(base,{"surface":data.get("surface"),"action":"undo","item_id":data.get("item_id")})
    return PlanningResult("completed", f"Undid {data.get('action')} for {data.get('item_id')}", [_rel(UNDO), _rel(rel)], [_rel(rel), _rel(AUDIT)], ["planning artifact restored", "office targeted refresh requested"], data)

def filter_items(root=None, surface="parking", query="", status="", priority="", owner="") -> PlanningResult:
    base=_root(root); rel=PARKING_LOT if surface=="parking" else ROADMAP; heading="Parking Lot Items" if surface=="parking" else "Roadmap"; _,_,rows,_,_=_load_table(base,rel,heading)
    def ok(r):
        blob=" ".join(r.values()).lower(); return (not query or str(query).lower() in blob) and (not status or r.get("Status","")==status) and (not priority or r.get("Priority","")==priority) and (not owner or owner.lower() in (r.get("Originator","").lower()))
    visible=[r for r in rows if ok(r)]
    return PlanningResult("completed", f"{len(visible)} visible item(s)", [_rel(rel)], [], ["browser filter state changed"], {"visible_items":visible})
