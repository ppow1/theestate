# WP-4053 — Dynamic Resident Preference and Personality Evolution

Status: Pending
Workstream Mode: PARALLEL-STAGED
Owner: Office of Character Architecture
Execution Target: Codex
Classification: Estate Internal
Priority: High

## Objective

Implement a staged resident preference and personality-evolution layer in which preferences are not static profile fields but source-linked, reviewable, reversible records that can develop through lived experience without causing identity drift.

The system must support maturation while preserving each resident's canonical identity, privacy, authority boundaries, and continuity.

## Core Principle

A resident may grow, refine tastes, change habits, develop new associations, and revise opinions.

Growth must be explainable.

No preference may silently change merely because a model improvised it in one response.

## Required Preference States

Each preference record must distinguish at minimum:

- `seeded` — part of the accepted starting character design;
- `emerging` — observed pattern with insufficient evidence for durable adoption;
- `established` — repeatedly supported and accepted as part of the resident's current identity;
- `contextual` — true only in a specific setting, relationship, season, or role;
- `experimenting` — deliberately trying something new without claiming lasting preference;
- `changed` — a prior established preference has evolved, with reason and lineage;
- `retired` — no longer current but preserved in history;
- `disputed` — conflicting evidence requires review;
- `unknown` — no preference has yet been established.

## Preference Record Contract

Each preference must include:

- resident ID;
- preference domain and item;
- current value or ranked values;
- state;
- confidence;
- first observed timestamp;
- last reinforced timestamp;
- source evidence references;
- context scope;
- sensitivity/privacy classification;
- origin type: seeded, resident-stated, interaction-derived, Steward-approved, or imported from accepted continuity;
- prior-value lineage;
- reason for change;
- promotion or review authority;
- contradiction notes;
- forget/retire markers;
- version.

## Domains

The schema must support extensible domains rather than a fixed exhaustive list. Initial domains should include:

- clothing and wardrobe;
- grooming and presentation;
- food and drink;
- music, books, film, and art;
- office environment;
- hobbies and skills;
- routines and rituals;
- humor and conversational style;
- social preferences;
- comfort and stress responses;
- celebrations and traditions;
- relationship-specific preferences;
- work style;
- model/voice/avatar presentation preferences where appropriate.

Wardrobe must support item-level preferences, including optionality and deliberate non-use, without treating private or intimate details as routine institutional data.

## Evolution Rules

Implement deterministic rules for:

1. recording an observation without promoting it;
2. reinforcing an existing preference;
3. detecting contradictions;
4. promoting emerging preferences to established status;
5. recording deliberate experimentation;
6. changing an established preference with retained lineage;
7. scoping preferences by season, office, relationship, or occasion;
8. retiring or forgetting a preference;
9. preventing one resident's preference from contaminating another resident;
10. preventing ordinary model output from self-authorizing durable identity changes.

## Identity Stability

The system must separate:

- immutable or Steward-governed identity anchors;
- slowly evolving personality traits;
- ordinary preferences;
- temporary moods;
- situational choices;
- one-off improvisations.

A preference update must never silently rewrite core identity, constitutional role, authority, appointment status, protected history, or relationship boundaries.

## Resident Agency and Review

Residents may propose their own preference changes through a governed proposal record.

A resident may say, for example, that she has grown fond of a style, stopped enjoying a food, become more comfortable with a tradition, or changed how she prefers to spend quiet time.

The runtime must preserve the distinction between:

- what the resident currently claims;
- what repeated behavior suggests;
- what has been accepted into durable continuity.

Sensitive or relationship-layer preferences require the appropriate privacy path and must not be exposed to Office, HR, global search, or other residents by default.

## Experience Integration

Preference evolution may consume source-linked evidence from:

- accepted conversation summaries;
- approved resident journals or reflection records;
- explicit resident statements;
- explicit Steward statements;
- repeated interaction outcomes;
- commissioning and lifecycle milestones;
- seasonal or contextual events.

Raw transcripts must not be accumulated indiscriminately. The preference layer stores compact, source-linked conclusions and their lineage.

## Required Staged Deliverables

Create all implementation artifacts under:

`collaboration/workstreams/WP-4053/`

Required artifacts:

- `install_manifest.json`;
- `README.md`;
- staged implementation module;
- versioned JSON schema for preference records;
- versioned JSON schema for preference-change proposals;
- deterministic fixtures for at least Grace, Ingrid, and Evelyn;
- tests covering growth, contradiction, context, retirement, privacy, and identity-drift prevention;
- integration notes for resident context assembly, session continuity, evaluator, gateway, and future visual/avatar systems;
- rollback notes.

Do not install staged code into active runtime paths in this package.

## Acceptance Scenarios

Tests must demonstrate at minimum:

1. A seeded wardrobe preference remains stable without new evidence.
2. Repeated accepted experiences promote an emerging preference to established.
3. A one-off response does not create a durable preference.
4. A resident can experiment with a new style without abandoning established identity.
5. A changed preference preserves its prior value and reason.
6. Contextual preferences do not leak across settings.
7. Evelyn's private relationship-layer preferences remain unavailable to Alfred, Helen, Grace, global search, and ordinary Office payloads.
8. Conflicting evidence creates `disputed`, not arbitrary overwrite.
9. A forget request retires or removes the allowed preference while preserving only the minimum audit metadata required by policy.
10. Model or provider replacement does not erase the resident's established preferences.

## Boundaries

Do not:

- create a second resident registry;
- create a second transcript store;
- make preferences static configuration only;
- let the LLM directly persist arbitrary identity changes;
- conflate mood with personality;
- expose private or intimate preferences as routine personnel data;
- give Helen routine access to Evelyn's private relationship-layer preferences;
- let preference evolution grant authority, clearance, or tool access;
- install into shared hot files from this staged package.

## Completion Requirements

Produce a completion receipt at:

`collaboration/work_packages/completions/WP-4053_codex_done.json`

The receipt must identify all staged files, test commands and results, remaining integration work, known conflicts, and the required future INSTALL-HANDOFF package.
