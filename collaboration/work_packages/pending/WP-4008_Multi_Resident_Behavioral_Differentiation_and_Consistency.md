# WP-4008 — Multi-Resident Behavioral Differentiation and Consistency

Status: Pending
Owner: Character Architecture / Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4001, WP-4003
Classification: Estate Internal

## Objective

Prove that Alfred, Helen, Grace, and future residents remain recognizably different people while sharing Estate governance, truthfulness, and authority rules.

## Required Scope

Create a versioned behavioral comparison framework covering:

- vocabulary and cadence;
- confidence and initiative;
- humor and warmth;
- escalation style;
- authority posture;
- uncertainty handling;
- emotional tone;
- response length tendencies;
- relationship to the Steward;
- office-specific decision patterns.

Implement deterministic paired-prompt tests using the same scenarios across residents. The framework must detect:

- identity collapse;
- generic-assistant drift;
- copied phrasing across residents;
- boundary confusion;
- inappropriate passivity;
- inappropriate authority expansion;
- personality instability across sessions.

## Required Outputs

- `docs/character-architecture/Multi_Resident_Behavioral_Differentiation_Standard_v0_1.md`
- machine-readable resident behavior profiles;
- paired-prompt test fixtures;
- comparison report for Alfred, Helen, and Grace candidate artifacts;
- `operations/validation/reports/WP-4008_multi_resident_behavior.md`;
- `collaboration/work_packages/completions/WP-4008_codex_done.json`.

## Boundaries

Do not reduce residents to stereotypes or cosmetic catchphrases. Do not alter constitutional roles. Do not expose private relationship-layer material in public tests. Do not activate Grace.

## Acceptance Criteria

- each resident is distinguishable without naming herself in every response;
- shared governance rules remain consistent;
- office boundaries remain stable;
- generic-assistant drift is detected;
- tests are deterministic under mocked model output and useful for manual local-model review;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4008_Multi_Resident_Behavioral_Differentiation_and_Consistency.md and do exactly what it says.
```
