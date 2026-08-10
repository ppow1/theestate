# WP-4214 — Steward Attention Annunciator v1

Status: Open
Priority: Normal
Classification: Estate Internal
Assigned To: Resident Runtime Implementation Stream
Depends On: WP-4018

## Mission

Extend the canonical Steward attention aggregate with a durable local presentation
boundary for newly actionable items. v1 provides a Windows-local sound/TTS adapter
and a durable, platform-neutral visual annunciator artifact.

## Scope

- Detect newly actionable `urgent`, `decision_required`, and `attention_soon` items
  from the existing Steward attention aggregate.
- Persist presentation fingerprints across polls and restarts.
- Write a durable visual annunciator state for Office of the Steward / Operations
  Center consumers.
- Use the host default audio endpoint through local Windows APIs only.
- Preserve a presenter protocol that can later be implemented by Linux KAMRUI or a
  phone consumer without moving attention authority out of Estate Python.
- Add deterministic tests, a safe local demo, documentation, validation report, and
  completion receipt.

## Do Not Touch

- No second event bus, attention authority, notification router, task queue, resident,
  cloud/API dependency, Bluetooth-distance logic, or phone fallback.
- Do not change the semantics or authority of existing attention actions.
- Do not make a Windows presenter the architectural authority.

## Required Reading

- `collaboration/work_packages/pending/WP-4018_Steward_Attention_Management_and_Executive_Briefing.md`
- `src/estate/core/steward_attention.py`
- `operations/validation/reports/WP-4018_steward_attention_management.md`
- `collaboration/handoffs/2026-08-09_ESTATE_NEAR_TERM_CAPABILITY_PUNCH_LIST_AND_WORKSTATION_DIRECTION.md` (if present in the active handoff checkout)

## Deliverables

- `src/estate/core/steward_annunciator.py`
- CLI presentation command and local demo path
- deterministic annunciator tests with mocked audio/TTS
- validation report and completion receipt

## Acceptance Criteria

- New actionable items alert once; unchanged items do not repeat after polling or restart.
- Severity is explicit and not color-only; acknowledgement/resolution/dismissal clears state.
- Presenter failure is recorded without losing the active visual state or falsely marking an item presented.
- Tests and a safe demo pass without producing real sound.
- No external cloud or paid AI service is used.

## Completion Notes

Filled in by worker.
