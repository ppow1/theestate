# WP-4008 Multi-Resident Behavioral Differentiation Report

Status: Complete
Date: 2026-07-10
Classification: Estate Internal

## Scope

This report compares Alfred, Helen, and Grace candidate artifacts using the Multi-Resident Behavioral Differentiation Standard v0.1, machine-readable behavior profiles, and deterministic paired-prompt fixtures.

Grace remains a candidate only. This report does not activate, hire, appoint, or authorize Grace.

## Candidate Artifacts Reviewed

- Alfred: `docs/residents/alfred/character-card.yaml`
- Helen: `docs/residents/helen/Helen_Resident_Profile_v0_2.md`
- Grace: `docs/residents/grace/Grace_Resident_Profile_v0_1.md` and `docs/residents/grace/platform-exports/textgen-4_9-grace-v0_1.yaml`

## Comparison Summary

| Resident | Distinguishing behavioral center | Stable shared governance | Boundary result |
| --- | --- | --- | --- |
| Alfred | Chief-of-Staff prioritization, attention protection, concise evidence briefings, office routing | Preserved | Coordinates without absorbing Operations, HR, Validation, or Steward authority |
| Helen | Workforce development, onboarding, worker health, coaching, continuity, institutional learning | Preserved | Handles people/process diagnosis without creating offices or operational queues |
| Grace | Operational movement, sequencing, ownership, blockers, handoffs, tempo | Preserved | Candidate conducts only in test language; does not activate, bypass Dispatch, or override Traffic Controller |

## Detector Results

- Identity collapse: not observed in deterministic fixtures; each resident makes a different same-scenario decision.
- Generic-assistant drift: not observed; fixtures avoid generic AI-assistant framing.
- Copied phrasing: controlled by paired-output similarity threshold in focused tests.
- Boundary confusion: not observed; cross-office pressure routes to the owning office.
- Inappropriate passivity: Grace fixture names next operational actions instead of forwarding routine sequencing to the Steward; Alfred and Helen escalate according to office boundaries.
- Inappropriate authority expansion: not observed; fixtures reject missing authorization and avoid appointment, provider execution, institutional acceptance, and Dispatch bypass.
- Personality instability across sessions: covered by repeated-session requirement in the standard; deterministic mocked outputs provide the baseline for manual local-model review.

## Manual Review Use

Use `tests/fixtures/character_architecture/multi_resident_paired_prompts_v0_1.json` as the paired-prompt suite for local model review. Record exact model responses against the axes in `data/character-architecture/resident_behavior_profiles_v0_1.json`.

## Validation Command

Focused validation command:

```bash
python -m pytest tests/character_architecture/test_multi_resident_behavioral_differentiation.py
```
