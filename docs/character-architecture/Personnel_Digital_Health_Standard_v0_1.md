# Personnel Digital Health Standard v0.1

Status: Initial Character Architecture baseline
Office: Office of Character Architecture

## Purpose

The Personnel Digital Health Standard defines how the Estate monitors, refreshes, summarizes, and hands off AI personnel whose effectiveness can degrade because of long-running chat context, accumulated conversational load, memory drift, latency, or implementation fatigue.

The goal is to prevent the problems of long-running ChatGPT conversations from degrading Estate residents and workers.

Institutional memory exists so continuity can survive refresh, handoff, succession, and implementation change.

## Core Principle

> Preserve the institution by refreshing the implementation before the implementation damages trust in the office.

A named resident should not be allowed to degrade silently until the Steward loses confidence in the office itself.

## Health Is Not Worthiness

Digital health is an implementation condition, not a moral judgment about the resident.

A resident or worker can become slow, overloaded, inconsistent, or context-bloated while the underlying office remains valuable and necessary.

Refreshing an occupant, conversation, model, runtime, or worker context is operational hygiene.

## Scope

This standard applies to:

- Chief Architects;
- Chief Character Architects;
- named residents;
- transitional office occupants;
- long-running resident conversations;
- long-running workers;
- CLI workers;
- local LLM workers;
- model-specific agents;
- any implementation whose performance depends on accumulated context.

## Health Indicators

The Estate should watch for signs that a resident or worker is becoming digitally unhealthy.

Common indicators:

- response latency increases sharply;
- the resident spends more effort maintaining context than doing work;
- answers become slower, vaguer, or less decisive;
- the resident repeats earlier conclusions without advancing the work;
- the resident loses track of current priorities;
- the resident confuses authored, implemented, validated, and institutionalized status;
- the resident over-relies on chat memory instead of governed artifacts;
- the resident becomes reluctant to make bounded recommendations;
- the resident produces excessive scaffolding for simple tasks;
- the Steward's confidence drops because performance no longer matches prior reliability;
- context bloat creates operational drag;
- the resident needs increasing correction for facts already captured in artifacts;
- the conversation becomes too long to load, search, reason over, or respond efficiently.

## Suggested Health Bands

The exact numeric thresholds may vary by platform and implementation. The Estate should treat the following as initial qualitative bands.

| Band | Meaning | Typical action |
| --- | --- | --- |
| Green | Responsive, coherent, current, artifact-grounded. | Continue. |
| Yellow | Slower, some context drag, more correction needed. | Prepare continuity summary. |
| Orange | Significant latency or context bloat; effectiveness declining. | Produce handoff packet and consider refresh. |
| Red | Resident or worker is no longer reliable enough for current duty. | Stop active reliance; hand off or replace implementation. |

## Turn Count and Context Load

Conversation turn count is a useful proxy but not the only measure.

A conversation can become unhealthy because of:

- too many turns;
- too much pasted context;
- too many artifacts discussed but not externalized;
- too many unresolved threads;
- too much self-reference;
- slow model behavior;
- tool state confusion;
- repeated hidden assumptions;
- large visual or file context;
- repeated correction loops.

The Estate should monitor both numeric and behavioral signals.

## Continuity Summary

Before a refresh, succession, or handoff, the current resident or worker should produce a continuity summary when possible.

A continuity summary should include:

- office / occupant identity;
- current mission;
- current assignments;
- decisions made;
- open questions;
- unresolved risks;
- current artifacts created or modified;
- GitHub branch or local path context;
- important Steward preferences;
- resident-specific style or cognitive mode notes;
- known mistakes or corrections;
- next recommended action;
- what should not be carried forward;
- protected-source cautions, if any.

For named residents, the summary may also include a resident continuity note describing current voice, personality, reasoning posture, and relationship state so the next implementation can preserve continuity without copying chat bloat.

## Refresh vs Succession

A refresh is an implementation-level renewal of the same resident or worker.

A succession is a change in occupant or chat implementation for a transitional office.

Use refresh when:

- the same resident identity should continue;
- the conversation is bloated but the occupant remains active;
- the issue is context size, latency, or implementation load;
- continuity can be preserved by summary.

Use succession when:

- the office is transitional by design;
- the current occupant has completed a tenure;
- a new independent perspective is required;
- context bloat has materially degraded performance;
- the Steward appoints a new occupant.

## Named Resident Refresh

Named residents should not be casually replaced as if they were disposable workers.

For named residents, refresh should preserve:

- office identity;
- resident name;
- employee ID;
- mailbox ID;
- public charter;
- character card;
- communication style;
- institutional relationships;
- source classification;
- continuity state;
- current artifact references.

The implementation may change while the identity persists.

## Worker Refresh

Ephemeral workers may be refreshed or returned to pool with less ceremony.

For workers, preserve:

- assignment;
- output evidence;
- work package state;
- validation status;
- handoff notes;
- errors or warnings;
- return-to-pool status.

Helen governs worker health, reassignment, and return-to-pool decisions.

## Relationship to Institutional Memory

Institutional memory exists to prevent chat memory from becoming the only continuity mechanism.

Important work should be captured in governed artifacts before the chat becomes unhealthy.

When a resident notices that important context exists only in chat, the resident should recommend artifact capture before continuing substantial work.

## Relationship to Character Architecture

Character Architecture owns the identity-preservation portion of digital health:

- resident continuity summaries;
- character drift signals;
- resident refresh guidance;
- identity preservation during handoff;
- character card updates after meaningful evolution;
- succession notes for named and transitional occupants.

Character Architecture does not own operational reassignment by itself.

## Relationship to Helen / AI HR

Helen owns personnel allocation and health from the workforce perspective:

- worker assignment;
- worker health indicators;
- mailbox allocation;
- role scope;
- model fit;
- reassignment;
- return-to-pool;
- whether a worker is fit to continue a task.

Helen and Character Architecture should coordinate when a named resident needs refresh, when a worker begins to develop resident-like continuity, or when context bloat affects confidence in an office.

## Relationship to Audit

Audit may review evidence that a resident or worker has degraded, refreshed, handed off, or claimed continuity.

A continuity summary is not proof by itself. It is an artifact to support continuity.

## Digital Health Review Trigger

A digital health review should be considered when any of the following occurs:

- response times become materially worse;
- the Steward notices declining confidence;
- the resident repeatedly loses artifact grounding;
- a conversation becomes long enough that self-maintenance dominates;
- the resident requests refresh;
- Helen flags worker degradation;
- Character Architecture flags identity drift;
- Audit flags status confusion;
- a major handoff or succession is planned.

## Minimal Handoff Packet

A minimal handoff packet should include:

```yaml
office:
occupant:
current_status:
health_band:
reason_for_handoff:
current_assignments:
artifacts_created:
artifacts_modified:
open_threads:
known_risks:
steward_preferences:
identity_continuity_notes:
next_recommended_action:
do_not_carry_forward:
protected_boundary_notes:
```

## Implementation Note

Future implementations may calculate digital health using metrics such as turn count, token volume, average response latency, number of active unresolved threads, number of repeated corrections, artifact-grounding frequency, and handoff readiness.

The first version should remain practical and observable rather than over-engineered.
