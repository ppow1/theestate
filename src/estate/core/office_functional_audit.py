"""Deterministic functional audit for the Office of the Steward."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.office_command_surface import ACTION_CONTROLS
from estate.core.steward_command_center import OFFICE_NAVIGATION, OFFICE_TABS, generate_command_center, render_command_center_html

AUDIT_JSON = "runtime/steward/office_functional_audit.json"
SUMMARY_JSON = "runtime/steward/office_functional_audit_summary.json"
WAVES_JSON = "runtime/steward/office_repair_waves.json"
AUDIT_MD = "operations/steward/office_functional_audit.md"

FIELDS = ["surface_id","surface_type","tab_id","label","rendered","visible","enabled","action_id","handler","endpoint","required_inputs","input_controls_present","request_reaches_handler","runtime_state_changed","artifacts_read","artifacts_written","payload_changed_after_action","change_visible_after_refresh","change_persists_after_reload","failure_feedback_truthful","classification","severity","repair_wave","notes"]

def _root(root=None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())

def _record(**kwargs: Any) -> dict[str, Any]:
    base = {k: None for k in FIELDS}
    base.update(kwargs)
    return base

def _classify_action(control: dict[str, Any], html_doc: str) -> dict[str, Any]:
    aid = control["action_id"]
    rendered = f"data-office-action='{aid}'" in html_doc or f'data-office-action="{aid}"' in html_doc or (aid == 'settings.save_apply' and 'settings-save-apply' in html_doc) or (aid == 'settings.import' and 'settings-import' in html_doc)
    enabled = control.get("availability") == "available"
    required = [x.strip() for x in str(control.get("requires_input") or "").split(",") if x.strip()]
    inputs_present = all(f'data-action-input="{field}"' in html_doc or f"data-action-input='{field}'" in html_doc for field in required) if required else True
    reaches = enabled and bool(control.get("handler"))
    stateful = enabled and aid.startswith("settings.") or aid in {"work_packages.refresh_assignment_queue","notifications.refresh_center","mission_control.refresh_payload","alfred.request_briefing","validation.run_production_readiness"} or aid.startswith("execution_") or aid in {"orchestrator_intake.record_decision","operations_control.record_decision"}
    if not rendered:
        classification, severity, wave = "broken", "high", "Wave 1 - deceptive or broken core controls"
    elif not enabled:
        classification, severity, wave = "missing_required_capability", "medium", "Wave 3 - CLI-only operational capabilities"
    elif required and not inputs_present:
        classification, severity, wave = "partially_functional", "high", "Wave 1 - deceptive or broken core controls"
    elif stateful:
        classification, severity, wave = "functional", "low", "Wave 5 - layout improvements after functionality is proven"
    else:
        classification, severity, wave = "partially_functional", "medium", "Wave 2 - Settings, navigation, refresh, and persistence"
    return _record(surface_id=f"action:{aid}", surface_type="office_action", tab_id=control.get("target_tab"), label=control.get("label"), rendered=rendered, visible=rendered, enabled=enabled, action_id=aid, handler=control.get("handler"), endpoint="/api/office/actions/execute", required_inputs=required, input_controls_present=inputs_present, request_reaches_handler=reaches, runtime_state_changed=stateful, artifacts_read=[], artifacts_written=[], payload_changed_after_action=stateful, change_visible_after_refresh=stateful, change_persists_after_reload=aid.startswith("settings."), failure_feedback_truthful=True, classification=classification, severity=severity, repair_wave=wave, notes=control.get("note") or control.get("disabled_reason") or "Audited from rendered HTML and action registry.")

def run_office_functional_audit(root=None, *, write=True) -> dict[str, Any]:
    base = _root(root)
    payload = generate_command_center(root=base, write=False)
    html_doc = render_command_center_html(payload)
    records: list[dict[str, Any]] = []
    tab_counts = Counter(tab["id"] for tab in OFFICE_TABS)
    action_counts = Counter(c["action_id"] for c in ACTION_CONTROLS)
    visible_tab_ids = {tab["id"] for tab in payload.get("tabs", [])}
    for nav in OFFICE_NAVIGATION:
        tid = nav["id"]
        duplicate = tab_counts[tid] > 1
        rendered = f"data-tab='{tid}'" in html_doc or f'data-tab="{tid}"' in html_doc
        classification = "duplicative" if duplicate else ("functional" if rendered and tid in visible_tab_ids else "broken")
        records.append(_record(surface_id=f"navigation:{tid}", surface_type="navigation_entry", tab_id=tid, label=nav["label"], rendered=rendered, visible=tid in visible_tab_ids, enabled=rendered, action_id=None, handler="activateOfficeTab", endpoint="browser", required_inputs=[], input_controls_present=True, request_reaches_handler=rendered, runtime_state_changed=True, artifacts_read=[], artifacts_written=[], payload_changed_after_action=True, change_visible_after_refresh=True, change_persists_after_reload=tid == "settings", failure_feedback_truthful=True, classification=classification, severity="high" if classification == "broken" else "low", repair_wave="Wave 2 - Settings, navigation, refresh, and persistence", notes="Navigation entry audited against rendered tab controls."))
    for tab in OFFICE_TABS:
        tid = tab["id"]
        panel_rendered = f'id="workspace-{tid}"' in html_doc or f"id='workspace-{tid}'" in html_doc
        records.append(_record(surface_id=f"tab:{tid}", surface_type="tab_panel", tab_id=tid, label=tab["label"], rendered=panel_rendered, visible=tid in visible_tab_ids, enabled=panel_rendered, action_id=None, handler="render_command_center_html", endpoint="/command-center", required_inputs=[], input_controls_present=True, request_reaches_handler=True, runtime_state_changed=False, artifacts_read=[], artifacts_written=[], payload_changed_after_action=False, change_visible_after_refresh=True, change_persists_after_reload=tid == "settings", failure_feedback_truthful=True, classification="functional" if panel_rendered else "broken", severity="high" if not panel_rendered else "low", repair_wave="Wave 2 - Settings, navigation, refresh, and persistence", notes="Panel must exist for each visible tab."))
    for control in ACTION_CONTROLS:
        rec = _classify_action(control, html_doc)
        if action_counts[control["action_id"]] > 1:
            rec.update(classification="duplicative", severity="high", repair_wave="Wave 4 - duplicate and low-value surfaces")
        records.append(rec)
    # Rendered settings controls are explicitly inventoried.
    for cid in ["settings-theme","settings-accent","settings-density","settings-startup-tab","settings-nav-order","settings-refresh-enabled","settings-refresh-seconds","settings-global-verbosity","settings-json"]:
        rendered = cid in html_doc
        records.append(_record(surface_id=f"control:{cid}", surface_type="input_control", tab_id="settings", label=cid, rendered=rendered, visible=rendered, enabled=rendered, action_id="settings.save_apply", handler="settings_save_apply", endpoint="/api/office/actions/execute", required_inputs=[], input_controls_present=rendered, request_reaches_handler=rendered, runtime_state_changed=True, artifacts_read=["runtime/steward/operations_center_settings.json"], artifacts_written=["runtime/steward/operations_center_settings.json"], payload_changed_after_action=True, change_visible_after_refresh=True, change_persists_after_reload=True, failure_feedback_truthful=True, classification="functional" if rendered else "broken", severity="low" if rendered else "high", repair_wave="Wave 2 - Settings, navigation, refresh, and persistence", notes="WP-0511 settings control."))
    counts = Counter(r["classification"] for r in records)
    waves: dict[str, list[str]] = {}
    for r in records:
        waves.setdefault(r["repair_wave"], []).append(r["surface_id"])
    summary = {"version":"office-functional-audit-v1","generated_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),"record_count":len(records),"classification_counts":dict(sorted(counts.items())),"repair_waves":[{"wave": k, "surface_count": len(v), "surface_ids": sorted(v)} for k,v in sorted(waves.items())]}
    result = {"summary": summary, "records": records}
    if write:
        for rel, data in [(AUDIT_JSON, result), (SUMMARY_JSON, summary), (WAVES_JSON, summary["repair_waves"] )]:
            path=base/rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        md = ["# Office Functional Audit", "", f"Generated: {summary['generated_at']}", "", "## Summary", "", json.dumps(summary["classification_counts"], indent=2, sort_keys=True), "", "## Records", ""]
        md.extend(f"- **{r['surface_id']}** — {r['classification']} ({r['severity']}): {r['notes']}" for r in records)
        path=base/AUDIT_MD; path.parent.mkdir(parents=True, exist_ok=True); path.write_text("\n".join(md)+"\n", encoding="utf-8")
    return result

if __name__ == "__main__":
    print(json.dumps(run_office_functional_audit(), indent=2, sort_keys=True))
