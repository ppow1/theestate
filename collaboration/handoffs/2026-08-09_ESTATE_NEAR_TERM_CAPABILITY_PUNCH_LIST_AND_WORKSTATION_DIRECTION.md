# Estate Near-Term Capability Punch List and Workstation Direction

Date: 2026-08-09
Status: Steward conversation checkpoint
Classification: Estate Internal
Purpose: Durable recovery point before workstation cold reboot / possible conversation loss.

## Steward intent

The Estate is close to becoming operational in several areas. Near-term work should favor small, bounded capability increments that make the Estate visibly and practically useful rather than opening new institutional branches. Where a job is a straightforward 15-minute-to-bounded engineering task, dispatching directly to Codex CLI is preferable to spending hours proving Grace can dispatch it. Grace can be tested progressively after underlying capabilities are trustworthy.

## Workstation / display operating model

The Steward currently works with four 55-inch 4K displays in a 2x2 arrangement, commonly with multiple windows visible per display and Stream Deck controls used to move active windows onto the primary lower monitors. The upper displays are often used for status/monitoring.

A small KAMRUI Linux PC is intended to become the daily-driver/browser/HMI workstation and can feed approximately three displays through the HDMI matrix. The Windows development machine is increasingly being treated as a compute/GPU and specialist-application host (4090 plus P100-class accelerator; Windows remains needed for applications such as Bambu Studio). The development machine may later move to Linux, but not yet.

Therefore Estate human-facing interfaces MUST NOT assume they execute on the Windows development host. Office of the Steward / Operations Center, Open WebUI/resident interaction, SCADA/activity displays, and attention presentation must be usable from the KAMRUI Linux workstation over the Estate network. Backend work may originate on other Estate machines.

A likely display arrangement reserves all or part of one wall display as an always-visible Estate operational surface, with Open WebUI/resident interaction, Office of the Steward/Operations Center, and status/SCADA information sharing that display as useful.

## Priority capability stack

### 1. Estate Attention / Notification Path v1

Goal: Stop requiring the Steward to babysit Codex terminals and other long-running processes.

Use the existing completion/attention monitoring direction and standardized Estate attention events. A real attention-required event should be presented through multiple channels rather than being tied to one machine or one headset.

Initial presenters:
- audible ding plus local text-to-speech, e.g. "The Estate needs your input on Project 5";
- a lightweight visual annunciator on the Estate operational display, such as a thin pulsing edge/corner indicator that does not steal focus;
- persistent attention state until acknowledged;
- acknowledgement from an Estate UI or Stream Deck should clear the same underlying event.

Visual severity should be distinguishable without relying solely on color. Routine activity belongs in SCADA; the annunciator means the Steward is actually needed.

Bluetooth proximity should not be estimated by distance. If a suitable audio endpoint is connected, use it. Phone fallback is a follow-on capability so an alert can reach the Steward when away from the workstation/headset. The event source must be Estate-level, not tied specifically to the Windows dev machine, because the KAMRUI is expected to become the primary human-facing workstation.

### 2. Codex Multi-Seat Fuel Gauge v1

There are three independent ChatGPT Business/Codex seats/logins with independent usage pools. They do not reliably reset according to a predictable schedule; observed remaining capacity is authoritative, while any advertised reset time is informational.

Known acquisition lead: interactive Codex CLI `/status` exposes usage/fuel information. Characterize how `/status` obtains/renders this information and determine the narrowest reliable automation path (underlying state/session data if available, otherwise controlled status interrogation). Do not begin with broad browser scraping unless necessary.

Normalize per-seat state including seat/profile identity, observed remaining capacity, observed timestamp, freshness/confidence, advertised reset if available, and previous observation. Detect replenishment jumps, low thresholds, exhaustion, stale/unknown state, and collector failure.

Grace should eventually consume this as resource state when deciding whether to use Codex CLI, Codex Cloud, local AI, or defer nonurgent work. Stream Deck and Operations Center should display it. Capacity changes should emit normal Estate events and significant changes can emit attention events.

### 3. Estate Operations Center Live SCADA / Activity Stream v1

Make the existing Operations Center/UI principles operational rather than placeholder-heavy. The Estate needs a persistent rolling operational heartbeat similar to an HMI/SCADA console.

Use real Estate runtime events only. No fake/demo events to create the appearance of activity.

Examples: work dispatched, worker progress changes, validation passed/failed, provider state changes, Codex capacity changes, mailbox communication events, Git state changes, attention required, and later fabrication events.

Support useful severity and source information and the already-intended verbosity concept: Quiet / Normal / Detailed / Diagnostic. Normal should be concise. Detailed/Diagnostic may expose provenance, IDs, timestamps, adapter detail, etc. Clicking/drilling into an event should reveal detail rather than stuffing all detail into the ticker.

Office of the Steward must contain action verbs, not only passive readouts. Important panels should answer both "what is happening?" and "what can I do about it?"

### 4. Stream Deck Git Truth Repair

Git/repository status controls currently create friction and low confidence. Existing issue #525 records the problem: persistent DIRTY state and ambiguous DIRTY/SYNC/CLEAN controls.

Repair the state model so it truthfully distinguishes at least working-tree modifications/untracked files, clean state, ahead/behind/diverged remote state, stash presence/count, sync-in-progress/failure, and unknown/error. Do not manufacture CLEAN by automatically hiding work in stashes. Stashes should be visible operational debt. Controls must make their action and current state unambiguous.

### 5. Codex Cloud Provider / Adapter

Codex Cloud can be more capacity-efficient for bounded jobs that do not need repeated access to the Steward's local disks. Investigate the authenticated Business-seat Codex Cloud command surface first (submit/status/diff/result) and place successful behavior behind the Estate's existing provider/execution adapter boundary.

Hard constraint: do not silently fall back to paid OpenAI API execution. ChatGPT Business-seat/Codex entitlement is the desired budget source. If the Business-seat Cloud path cannot perform the job, stop or select another Estate provider rather than incurring API charges.

Grace should eventually be able to select among local AI, Codex CLI/local-repository execution, and Codex Cloud based on capability, data locality, fuel/capacity, and cost source.

### 6. Resident / Character / Governance Reintegration

Recover and reconcile the two senior architect identities/roles and the senior character-design role from canonical Estate records rather than creating replacements. Historically the architects could work independently/adjacently, challenge one another, and communicate through Estate mailboxes. Preserve the personnel/authority model while allowing the underlying reasoning substrate to move toward local resident models.

For now, do NOT give every resident an independent external high-reasoning integration. Residents should be able to identify a bounded need for higher-level reasoning and submit that request through Grace. Grace brokers the existing higher-reasoning path and returns the result. This centralizes capacity/cost/routing/audit behavior and gives one place for future boundary enforcement.

Restart the character-development program after canonical reconciliation. Substantial prior character/canon work exists and should be preserved rather than recreated.

Ingrid is the Security/Boundary resident and appears to have identity/onboarding artifacts but requires operational reintegration. Existing boundary-policy hooks should be characterized and wired into real ingress/egress choke points, particularly Grace-mediated external reasoning and externally hosted execution, before sensitive engineering data routinely leaves the Estate.

A legal-review resident believed to be named Judy should be reconciled from canonical records before relying on the name/role. Intended relationship: Ingrid owns security/boundary decisions and can consult legal-review expertise for law/licensing/contracts/privacy/export/compliance questions.

## Communications visibility

The Estate already has mailbox/message concepts. Inter-resident communication should be observable without dumping full conversations into the normal SCADA ticker.

Normal SCADA may show concise communication events such as "Chief Architect 1 -> Chief Architect 2: review request sent." A dedicated Communications view should provide thread/message content, sender/recipient, timestamps, unread state, related work package/project, and provenance. Detailed/Diagnostic SCADA modes can expose more transport/sync information.

This becomes particularly useful when architects or other residents collaborate autonomously: the Steward can see that useful communication is occurring and inspect it when desired without being forced into every exchange.

## Fabrication / Bambu capability (next behind the immediate six)

Investigate AI-accessible fabrication tooling: Bambu printer-control integrations/MCP-style interfaces plus AI-accessible slicer control. Treat the printer as an Estate execution resource managed through existing Operations/Grace concepts rather than creating a new institution.

Desired eventual flow: idea -> engineering/CAD homework -> validated printable artifact -> slicing/profile review -> governed dispatch -> printer monitoring -> completion/failure/attention -> capacity available again.

Grace should see printer capacity and fabrication queue state. Physical print initiation should initially retain an explicit readiness/approval gate. Prefer local/stable integration surfaces and characterize exact printer/firmware capabilities before depending on undocumented behavior.

## Recommended execution approach

Direct Codex CLI packages first for:
1. Attention Notification Path v1 (durable event + local audio + visual annunciator; phone later).
2. Codex Multi-Seat Fuel Gauge v1.
3. Operations Center SCADA/Event Stream v1.
4. Stream Deck Git Truth Repair (#525).

These are bounded capability/repair jobs and should not be delayed merely to prove Grace can dispatch them.

Then characterize/implement Codex Cloud provider behavior. Once the underlying provider works, use an appropriately bounded job as a Grace scheduling/dispatch test.

Resident/governance work should begin with reconciliation rather than implementation so existing employee identities, mailboxes, authority, and character canon are not duplicated or overwritten.

## Architectural direction

Prefer one normalized operational/event fabric with multiple consumers:
- Operations Center / SCADA for visibility;
- Stream Deck for compact high-value state/actions;
- attention presenters for visual/audio/phone alerts;
- Grace for scheduling/resource decisions;
- communications UI for mailbox/message inspection.

Do not let each subsystem invent its own independent status/notification mechanism.

The Estate's human-facing operational surfaces must be network-accessible and usable from the Linux KAMRUI daily-driver. Compute, Codex, GPU work, Bambu Studio, or other specialist processes may remain on the Windows dev machine or other Estate hosts, but status/control must not require sitting at that host.

## Recovery note

This document was intentionally committed before a planned cold reboot prompted by another apparent P100 loss. It is a conversation checkpoint so the near-term capability planning can be recovered even if the active ChatGPT conversation/session is disrupted.
