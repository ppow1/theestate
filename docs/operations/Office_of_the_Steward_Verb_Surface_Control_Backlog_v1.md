# Office of the Steward Verb Surface Control Backlog v1

## Scope and source of truth

This audit is a planning artifact for WP-0118. It inventories the implemented Office of the Steward UI from `src/estate/core/steward_command_center.py`, especially `OFFICE_TABS`, `OFFICE_NAVIGATION`, and `render_command_center_html`. It does not grant new authority, implement broad controls, or make UI buttons equivalent to permission.

## 1. Current Noun Surface Inventory

| Current tab/workspace | Implemented id | Primary panel/source | Current noun/status surface displayed |
| --- | --- | --- | --- |
| Home | `home` | Office shell summary | Local command center introduction, navigation/status/activity framing, snapshot affordance, and workspace entry points. |
| Mission Control | `mission-control` | `mission_control_workspace` | Mission Control state, ready source counts, recommended next action text, lane/source cards, capability dependency visualization, warnings. |
| Alfred | `alfred` | `alfred_resident_card`, `alfred_chat` | Alfred resident card plus chat surface; identity/status/capability-oriented resident information and bounded conversational entry. |
| Helen | `helen` | `helen_resident_card` | Helen resident card; identity/status/capability-oriented resident information. |
| Resident Conversations | `resident-conversations` | `resident_conversations_workspace` | Conversation session/message tables, session status, outcomes, authority statements, audit artifacts. |
| AI Services / Models | `ai-services-models` | `ai_services_models` | Dashboard counts, operational command-hook text, services, model inventory, preferences, assignments, approvals, audit/rediscovery state. |
| Daily Board | `daily-board` | `morning_briefing`, `daily_board_workspace` | Morning briefing artifact plus priorities, waiting, blocked, review-required, active-work and parking-lot summaries. |
| Projects | `projects` | `work_package_pipeline` | Work package pipeline focused as active projects: IDs, titles, mode, owners, dependencies, next action, completion/review. |
| Roadmap | `roadmap` | `expansion_roadmap` | Roadmap items, upcoming epics, planned inactive initiatives, future work-package candidates. |
| Parking Lot | `parking` | `daily_board_workspace` | Parking-lot items parsed from local planning artifacts. |
| Work Packages | `work-packages` | `work_package_pipeline` | Work package pipeline, pending/active/review-oriented state, dependency and next-action fields. |
| Mailboxes | `mailboxes` | `mailbox_operations_center` | Mailbox KPIs, mailbox rows, message counts, open counts, acknowledgement requirements, Steward-waiting details. |
| Recalls | `recalls` | `steward_recall_operations` | Recall rows with reasons, origin/requester, Alfred state, transport, delivery, acknowledgement, lifecycle, timestamps, source links. |
| Notifications | `notifications` | `operations_notification_center` | Aggregated notification counts, severity/source/title/message, state, local acknowledgement status, source artifact. |
| Validation | `validation` | `validation_health_dashboard`, `validation_status` | Health table by subsystem, warning/failure counts, source reports, generated validation artifact/status display. |
| Search | `search` | `search` | Global search and command palette entries, navigation commands, result metadata and availability. |
| Settings | `settings` | `settings`, `operations_center_layout` | Local UI settings, workspace/profile/layout metadata, regions, tab order, pinned views. |
| Help | `help` | `help` | Documentation links, guidance text, local-only operational help. |
| About | `about` | `about` | UI/component versions, status, artifact inventory and source paths. |

## 2. Verb Surface Philosophy

- Noun surfaces show state; verb surfaces let the Steward act on state.
- Every visible state should eventually answer: what can I do with this?
- UI actions must remain bounded by institutional authority.
- A control is not the same as permission.
- A button may draft, request, validate, queue, copy, export, or route, but must not silently authorize where authority is required.
- Office controls should be local-first, auditable, reversible where possible, and explicit about files read, files written, and command hooks.
- The Office should feel like a control room by showing safe next actions beside state, not by bypassing governance.

## 3. Action Classification

| Action class | Examples | Authority/safety class | Default behavior |
| --- | --- | --- | --- |
| Read / inspect | Open detail drawer, inspect source JSON/Markdown, show latest validation report | Safe read-only | No confirmation; no mutation. |
| Refresh / regenerate local artifact | Regenerate command center, refresh Mission Control payload, rebuild local index | Safe local generated-artifact update | Show output paths before running; report generated files. |
| Export / snapshot | Office Snapshot ZIP, copy JSON panel payload, export current table | Safe read-only unless artifact is written | If writing, identify output path and sensitivity warning. |
| Open source artifact | Open source path in browser/editor/file link | Safe read-only | Link to local artifact; never mark state reviewed by opening. |
| Copy command | Copy CLI command for Steward to run | Safe read-only | Make command visible; no execution. |
| Create draft | Draft work package, draft reply, draft acknowledgement, draft review request | Steward-confirmed local mutation | Preview full draft and target path before write. |
| Queue request | Queue Alfred request, queue CA review request, queue validation request | Steward-confirmed local mutation or authority-gated institutional action | Confirm route, actor, artifact, and authority boundary. |
| Acknowledge / mark reviewed | Local notification acknowledgement, local mailbox read marker | Steward-confirmed local mutation | Must distinguish local UI acknowledgement from authoritative source closure. |
| Validate | Run validation recipe, inspect validation health, produce report | Safe local generated-artifact update when recipe exists; authority-gated to declare acceptance | UI may run/report validation but must not declare institutional acceptance alone. |
| Start local service | Start approved local AI service | Authority-gated institutional action | Requires manifest, policy gates, visible command, approval evidence where required. |
| Stop local service | Stop approved local AI service | Authority-gated institutional action | Requires manifest, target identity, and confirmation. |
| Run safe local command | Run registered local-only CLI command | Safe local generated-artifact update or Steward-confirmed local mutation | Only registered allowlist commands; show command and effects. |
| Promote parking-lot item | Convert parking-lot item to proposed work package draft | Steward-confirmed local mutation | Draft only unless existing governance permits promotion. |
| Submit sequential batch manifest | Submit batch for review/execution | Authority-gated institutional action | Requires batch manifest validation and correct authority route. |
| Request Chief Architect review | Create or queue CA review request | Authority-gated institutional action | Request review; do not mark CA verified. |
| Destructive action | Delete artifact, purge history, cancel job, stop service with impact | Prohibited until future governance/tooling exists unless explicit design exists | Require explicit confirmation, authority, audit, and recovery story. |

Authority/safety classes used in this backlog:

1. **Safe read-only** — inspects, opens, filters, copies, or exports without changing Estate state.
2. **Safe local generated-artifact update** — regenerates local derived artifacts without changing source authority.
3. **Steward-confirmed local mutation** — writes local UI/runtime/draft state after preview and confirmation.
4. **Authority-gated institutional action** — routes through existing Steward, Chief Architect, resident, validation, or governance authority.
5. **Prohibited until future governance/tooling exists** — unsafe or undefined controls that must remain absent.

## 4. Per-Tab Verb Matrix

| Tab/workspace | Current noun/status surface | Proposed verbs/actions | Authority class | Complexity | Prerequisites | Recommended work package | Notes/risks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Home | Shell status, navigation, activity framing, snapshot affordance | Refresh Office; export Office Snapshot; open active alerts; copy local serve command | Safe read-only; safe local generated-artifact update | Low | Existing snapshot/export and generate hooks | WP-0118-F1 Office action framework | Avoid making Home a hidden executor. |
| Mission Control | State, source counts, lanes, warnings, dependencies | Refresh workspace; inspect source lane; open source artifact; create follow-up draft from warning; request CA review | Safe read-only; safe generated update; authority-gated for review request | Medium | Action registry, source-link resolver, draft queue | WP-0118-F8 Mission Control and Projects controls | Mission Control must remain summary, not source of truth. |
| Alfred | Resident card and Alfred chat | Start conversation; inspect resident surface; copy duty/status commands; queue Alfred request; inspect job; cancel/retry only through policy | Safe read-only; Steward-confirmed local mutation; authority-gated | Medium/High | Resident interaction framework, Alfred request/job policy | WP-0118-F6 Resident conversation controls | Do not grant Alfred work-package execution authority. |
| Helen | Resident card | Inspect resident surface; copy HR authority checks; start conversation when Helen chat exists; draft HR/onboarding request | Safe read-only; Steward-confirmed draft; authority-gated HR actions | Medium | Helen chat surface, HR authority routes | WP-0118-F6 Resident conversation controls | HR mutations require explicit authority evidence. |
| Resident Conversations | Sessions/messages/outcomes/audit artifacts | Start session; open transcript; export transcript; redact/forget with audit; draft promotion of outcome | Safe read-only; Steward-confirmed local mutation; authority-gated promotion | Medium | Resident API standard, redaction workflow | WP-0118-F6 Resident conversation controls | Conversation outcomes are not institutional decisions until promoted. |
| AI Services / Models | Services, models, preferences, assignments, approvals, command hooks | Rediscover; inspect manifest; copy start/stop/load commands; request approval; start/stop/load via gated adapter later | Safe read-only; safe generated update; authority-gated service actions | High | Service allowlist, approval workflow, process adapter | WP-0118-F7 AI services/model controls | Starting services can affect host resources; keep explicit. |
| Daily Board | Briefing, priorities, waiting, blocked, review-needed | Refresh board; open source item; mark locally reviewed; draft daily note; promote blocked/review item to request | Safe read-only; Steward-confirmed local mutation; authority-gated request | Medium | Local acknowledgement store, draft queue | WP-0118-F5 Daily Board and Parking Lot controls | Local reviewed state must not close underlying work. |
| Projects | Work package pipeline as active projects | Inspect package; open source; copy validation command; request review; create blocker note; assign only through governance | Safe read-only; Steward-confirmed note; authority-gated assignment | Medium | Work package registry/state machine | WP-0118-F8 Mission Control and Projects controls | Avoid conflicting with Work Packages tab ownership. |
| Roadmap | Roadmap items, epics, planned initiatives, candidates | Inspect evidence; draft work-package proposal; export roadmap snapshot; request prioritization review | Safe read-only; Steward-confirmed draft; authority-gated prioritization | Medium | Proposal template, prioritization workflow | WP-0118-F8 Mission Control and Projects controls | Roadmap candidate is not approval. |
| Parking Lot | Parking-lot rows | Inspect item; promote to proposed work-package draft; archive local duplicate; request review | Safe read-only; Steward-confirmed draft/mutation; authority-gated review | Medium | Draft work-package generator, duplicate detection | WP-0118-F5 Daily Board and Parking Lot controls | Promotion creates draft/proposal, not execution authority. |
| Work Packages | Pipeline rows, dependencies, next action, completion/review | Inspect package; validate package; open pending/completion; copy commands; request CA review; submit batch manifest | Safe read-only; safe generated update; authority-gated review/batch | Medium/High | Validation framework, batch manifest rules | WP-0118-F2 Work Packages tab controls | Buttons must not execute pending packages. |
| Mailboxes | Mailbox KPIs, rows, ack/waiting state | Open mailbox; inspect message; draft reply; local acknowledge; route to resident; export mailbox snapshot | Safe read-only; Steward-confirmed local mutation; authority-gated routing | Medium | Message action API, local ack store | WP-0118-F4 Mailboxes and notifications controls | Local ack is not source deletion/closure. |
| Recalls | Recall lifecycle, delivery, acknowledgement | Inspect recall; copy delivery command; local acknowledge; request Steward decision; export recall audit bundle | Safe read-only; Steward-confirmed local mutation; authority-gated decision | Medium | Recall lifecycle API, decision queue | WP-0118-F4 Mailboxes and notifications controls | Recall acknowledgement semantics must be precise. |
| Notifications | Aggregated notification rows and local ack status | Filter; inspect source; local acknowledge; bulk local acknowledge low-severity; create follow-up draft | Safe read-only; Steward-confirmed local mutation | Medium | Notification ack store, bulk confirmation UX | WP-0118-F4 Mailboxes and notifications controls | Bulk controls must be reversible or auditable. |
| Validation | Health table, validation status artifacts | Run recipe; run production readiness; open report; copy failing command; create validation observation | Safe generated update; Steward-confirmed draft; authority-gated acceptance | Medium | Validation command registry, observation template | WP-0118-F3 Validation tab controls | UI pass state is evidence, not institutional acceptance. |
| Search | Command palette entries and results | Navigate; inspect result; copy command; open artifact; save search locally | Safe read-only; Steward-confirmed local preference mutation | Low/Medium | Command palette metadata, saved-search store | WP-0118-F1 Office action framework | Search must not expose unregistered commands. |
| Settings | UI settings, layout, profiles, tab order | Change theme/profile; save active tab; reset local preferences; export/import local settings | Steward-confirmed local mutation; safe read-only export | Low/Medium | Settings manager, schema validation | WP-0118-F9 Settings/help/about utility controls | Do not store secrets. |
| Help | Document links and guidance | Open docs; copy support bundle command; export help index; create documentation feedback draft | Safe read-only; Steward-confirmed draft | Low | Document registry, feedback draft template | WP-0118-F9 Settings/help/about utility controls | Help can explain authority but not override it. |
| About | Component versions, artifact inventory | Copy version manifest; export diagnostics; open component source; compare generated/runtime versions | Safe read-only; safe generated update if diagnostics written | Low | About payload, diagnostics writer | WP-0118-F9 Settings/help/about utility controls | Diagnostics may include internal paths. |

## 5. Immediate Implementation Breakdown

| Follow-up package | Draft title | Draft mission |
| --- | --- | --- |
| WP-0118-F1 | Office Action Framework / Command Dispatch Foundation | Define an Office action registry, action metadata schema, allowlisted local command hooks, common confirmation model, output-path reporting, and test fixtures without implementing high-risk controls. |
| WP-0118-F2 | Work Packages Tab Controls | Add inspect/open/copy-validation/request-review affordances to Work Packages while preventing execution of pending work packages and routing CA review through existing authority. |
| WP-0118-F3 | Validation Tab Controls | Add run/copy/open validation controls that generate validation artifacts, show command output, and distinguish evidence from acceptance. |
| WP-0118-F4 | Mailboxes, Recalls, and Notifications Controls | Add inspect, local acknowledge, draft reply, export snapshot, and route/request controls with clear local-vs-authoritative state labels. |
| WP-0118-F5 | Daily Board and Parking Lot Controls | Add refresh/open/draft/promote-to-proposal controls for board and parking-lot items, with proposal-only semantics. |
| WP-0118-F6 | Resident Conversation Controls | Add session start/open/export/redaction request/draft-promotion controls for Alfred, Helen, and resident conversation surfaces under the resident action authority boundary. |
| WP-0118-F7 | AI Services / Model Controls | Add manifest inspection, rediscovery refresh, copy command, and approval-request surfaces before any direct process-control adapters. |
| WP-0118-F8 | Mission Control, Projects, and Roadmap Controls | Add source inspection, refresh, warning-to-draft, and prioritization/review request controls without making summaries authoritative. |
| WP-0118-F9 | Settings, Help, About Utility Controls | Add local preference reset/export, documentation feedback draft, version manifest export, and diagnostics snapshot controls. |

## 6. Control Safety Rules

1. Every mutating control must show what it will change before it changes it.
2. Every authority-gated action must route through the correct authority path.
3. Every generated artifact update must identify output paths.
4. Every command-running action must be local-first and visible to the Steward.
5. Destructive actions require explicit confirmation, audit trail, and recovery story.
6. Buttons must not silently execute pending work packages.
7. Resident controls must respect the Resident Action Authority Boundary: residents may converse, draft, summarize, inspect, or request within their authority, but may not silently validate, merge, hire/fire, mutate governance, or execute work packages.
8. Validation controls must not declare success by UI state alone; they may run recipes and present evidence.
9. Copy-command controls are safer than execute-command controls and should be preferred until action dispatch is reviewed.
10. Local acknowledgements must be visibly labeled as local UI/runtime state unless the authoritative source is actually updated through a designed authority route.
11. Bulk actions must summarize all affected items and require a second confirmation.
12. Prohibited actions stay absent rather than disabled-but-tempting until governance/tooling exists.

## 7. Validation Recipe for WP-0118

The WP-0118 validation recipe is registered in `src/estate/core/work_package_validation.py` and checks that:

- this backlog document exists;
- the action-surface work package template exists;
- the implemented Office tabs/workspaces are inventoried;
- noun/status surfaces are distinguished from verbs/actions;
- the action classification model is present;
- the per-tab verb matrix is present;
- follow-up work package recommendations are present;
- the template requires authority classification and validation behavior;
- the WP-0118 completion receipt is complete.

Required validation commands:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0118 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```
