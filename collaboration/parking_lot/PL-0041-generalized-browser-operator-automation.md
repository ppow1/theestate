# PL-0041 — Generalized Browser Operator Automation

Status: Captured
Priority: Strategic
Category: Developer Experience / Browser Automation / Acceptance Engineering
Originator: Pat / Steward
Date Captured: 2026-08-08
Target Milestone: After the current Grace/Open WebUI Playwright acceptance proves the browser-operator pattern in live use

## Idea

Generalize the browser automation capabilities proven during Grace/Open WebUI acceptance into a reusable Estate browser-operator capability that can be driven by ChatGPT, Codex command-line/cloud work, or local AI without requiring the Steward to act as the manual copy/paste and screenshot relay between an AI worker and a browser UI.

The goal is not to create one giant site-specific automation script. The goal is to preserve and reuse the browser/session/evidence machinery while allowing a target-specific layer to define the shell being exercised.

The present Open WebUI/ChatGPT work is the proving ground. A future second target should demonstrate that the abstraction is genuinely reusable; the Office of the Steward is a strong candidate because it will require substantial dashboard/UI modernization and direct browser integration testing against authoritative SQLite-backed operational state.

## Why This Matters

Historically, browser-facing Estate validation has required the Steward to manually:

- paste prompts into Grace or another resident surface;
- repeat the same prompts against alternate resident/gateway surfaces;
- copy responses back to ChatGPT/Codex;
- capture screenshots so the AI worker can see visible UI state;
- paste the underlying text separately because screenshots do not preserve enough context;
- repeat this cycle across several prompts while the worker diagnoses and repairs defects.

Existing Office Snapshot/export tooling improves static inspection by packaging HTML, CSS, JavaScript, JSON and related page artifacts, but static snapshots are not equivalent to a worker actually clicking a control, observing the resulting state transition, following navigation, waiting for asynchronous behavior, or proving that a real browser user path works.

A reusable browser operator could remove most of that repetitive human relay while preserving final Steward acceptance.

## Intended Architecture Direction

When intentionally promoted, first inspect and reuse the existing Open WebUI/ChatGPT Playwright/operator automation. Extract only the parts that are genuinely target-independent.

Candidate reusable responsibilities include:

- browser and page lifecycle;
- persistent profile/session handling;
- explicit authentication boundaries and human handoff when genuinely required;
- headed and unattended modes;
- deterministic waits and readiness classification;
- screenshots;
- Playwright traces;
- console capture;
- network evidence;
- scenario execution;
- failure classification;
- machine-readable evidence manifests;
- process-safe detached execution through the Estate's existing isolation tooling where required;
- bounded interaction/extraction operations;
- clean shutdown and orphan-process detection.

Target-specific packages should own only what is actually specific to the shell, such as:

- URLs/navigation;
- selectors;
- model/resident pickers;
- composer behavior;
- dashboard controls;
- target-specific readiness criteria;
- extraction rules;
- expected UI state transitions.

Conceptually:

```text
Estate Browser Operator
    |
    +-- browser/session lifecycle
    +-- persistent profiles
    +-- authentication boundary
    +-- screenshots / traces
    +-- console / network evidence
    +-- deterministic waits
    +-- scenario runner
    +-- evidence package
    |
    +---- Open WebUI target
    +---- ChatGPT Work target
    +---- Office of the Steward target
    +---- future approved browser target
```

The scenario/payload should vary. The core browser machinery should not need to be rewritten for every target.

## Office of the Steward Opportunity

The Office of the Steward has fallen behind current Estate reality and is expected to require renewed dashboard and visualization work as durable SQLite-backed operational state expands.

A generalized browser operator could become the integration-test surface for that modernization by proving, through a real browser, that:

- controls are clickable and have the expected effect;
- dashboard views reflect authoritative current state;
- navigation works;
- live/update behavior works where intended;
- charts, queues, resident activity, CME state, resources and other operational visualizations render correctly;
- asynchronous actions complete or fail visibly and truthfully;
- screenshots/traces/text evidence are automatically captured for engineering review.

This should complement, not replace, the existing Office Snapshot/export concept. Snapshot/export answers "what files/state did the page contain?" Browser automation answers "what did the UI actually do when operated?"

## Provider Neutrality

Do not hard-code this capability to Codex.

The operator should be callable by whichever Estate reasoning/execution provider is authorized and capable, including:

- ChatGPT;
- Codex;
- local AI;
- future Estate execution/reasoning providers.

Provider selection is outside the browser operator's responsibility.

## Safety / Governance Boundary

Generic browser capability must not imply unrestricted automation authority over arbitrary external services.

Each target remains subject to:

- Estate authorization;
- service terms and policies;
- authentication boundaries;
- privacy/security rules;
- destructive-action authority;
- target-specific rate and interaction limits.

The reusable core should provide mechanics and evidence, not silently grant permission to automate a site.

## Why It Is Parked

The current Grace multi-lane/Open WebUI acceptance must finish first. That work is actively proving whether the browser-operator approach actually saves Steward time and produces trustworthy live evidence.

Generalizing the implementation before the first target is proven would risk extracting the wrong abstraction and creating unnecessary framework work.

## Promotion Condition

Promote this item when:

1. the current Open WebUI/Grace Playwright acceptance has completed successfully enough to demonstrate real operational value;
2. a second materially different browser surface is ready for integration testing, preferably the Office of the Steward modernization effort;
3. the existing browser tooling can be inspected to identify a small reusable core rather than a new monolithic framework;
4. the Steward intentionally authorizes the extraction/generalization effort.

A successful promotion should prove the reusable layer against at least two materially different targets before treating it as an Estate-wide standard.

## Explicit Non-Action

Do not interrupt the current Grace parallel acceptance to generalize the browser tooling.

Do not create a new department, scheduler, database, browser service, or broad architectural layer merely because this idea is captured.

Do not rewrite the working Open WebUI harness before its current acceptance objective is complete.

Do not assume generic browser mechanics authorize automation of every external website.

When promoted, first ask which existing Playwright/operator code can be extracted with small targeted edits and which behavior must remain target-specific.

## Related Evidence

- Existing Open WebUI operator/Playwright acceptance work and its live Grace acceptance evidence.
- Existing detached process-sensitive harness: `tools/cme_owner_isolation.py`.
- Existing Office Snapshot/export concept: PL-0017 / WP-0117.
- Existing Live Office State Updates concept: PL-0018 / WP-4216.
- Office of the Steward modernization need as current operational state increasingly moves into durable SQLite-backed sources.
- Canonical Parking Lot process: `AI_COMMUNICATION_HINTS.md`.
