# Estate Feature Activation Ledger

Status: Authoritative activation ledger  
Created: 2026-07-11  
Source package: WP-0647

This ledger is the single operational activation record for implemented Estate capabilities reviewed by WP-0647. It records whether each capability is live, installed-but-newly-connected, staged-only, planning-only, or blocked/incomplete. It is not a second registry, scheduler, queue, authority system, Office, resident gateway, model-control plane, or validation engine.

## Activation states

- **Live**: imported or called by an existing runtime surface and covered by active tests.
- **Connected by WP-0647**: installed active source that had no Office/runtime caller and is now reached through an existing surface.
- **Installed active source**: present in `src/estate` and validated, but no additional WP-0647 caller was needed or safe.
- **Staged only**: validated workstream files remain outside active runtime paths.
- **Blocked/incomplete**: activation would require creating or replacing a prohibited system.

## Ledger

| Capability | State | Runtime reachability evidence | WP-0647 action |
| --- | --- | --- | --- |
| Office command surface controls | Live | `estate.core.office_command_surface.execute_office_action` dispatches registered actions through existing handlers. | Reused as the activation surface; no duplicate Office created. |
| WP-0522 executive workspace | Connected by WP-0647 | `office_intelligence.refresh_executive_workspace` is registered in the existing Office command surface and calls `estate.core.office_executive_workspace.build_executive_workspace`. | Connected advisory refresh to Mission Control tab outputs. |
| WP-0523 guided actions | Installed active source | `src/estate/core/office_guided_actions.py` and active tests exist. | No extra caller added; avoid inventing a second action authority. |
| WP-0524 actionable notifications | Live | Existing notification controls in the Office command surface call `estate.core.office_actionable_notifications`. | Left on canonical notification surface. |
| WP-0525 resident presence | Live | Resident presence has active source and Office resident tests. | Left on canonical resident surfaces. |
| WP-0526 workspace personalization | Installed active source | Active source and tests exist for deterministic settings/personalization behavior. | No extra caller added beyond existing settings surface. |
| WP-0527 unified search | Installed active source | Active source and tests exist for query contract/search behavior. | No broad global caller added without product surface requirements. |
| WP-0528 operational timeline | Installed active source | Active source and tests exist for timeline construction. | No duplicate activity stream created. |
| WP-0529 decision support | Installed active source | Active source and tests exist for advisory decision support. | No autonomous authority added. |
| WP-0530 operational workflows | Installed active source | Active source and tests exist for workflow sessions. | No scheduler/queue created. |
| WP-4024 resident context assembler | Installed active source | Active tests import `estate.core.resident_context_assembler`. | No new gateway created. |
| WP-4025 resident session manager | Installed active source | Active tests import `estate.core.resident_session_manager`. | No new resident gateway created. |
| WP-4026 local model assignment | Installed active source | Active tests cover `estate.model_control.resident_model_assignment`. | No second model-control plane created. |
| WP-4027 resident evaluator | Installed active source | Active tests import `estate.core.resident_evaluator`. | No validation engine replacement created. |
| WP-4028 local AI service supervision | Live | AI service controls route through `estate.ai_services` and active supervision source. | Left on canonical AI services control plane. |
| WP-4029 resident attachment exchange | Installed active source | Active tests import `estate.core.resident_attachment_exchange`. | No new resident gateway created. |
| WP-4030 estate backup/restore | Staged only | Workstream source remains under `collaboration/workstreams/WP-4030/src`. | Not activated; operational authority and restore policy are not established. |

## Safety conclusion

WP-0647 activated only an eligible orphan by adding an Office command-surface route for the installed executive workspace. Other implemented capabilities remain truthfully classified without fabricating new orchestration, validation, model-control, resident-gateway, or authority systems.
| WP-0651 | Live evidence pending Chief Architect acceptance | `runtime/operational_readiness/cases/orc-76a26b52c11c00b9.json` and `runtime/operational_readiness/evidence/orc-76a26b52c11c00b9/events.jsonl` | Activation evidence is work-package specific; institutional acceptance remains separate. |
