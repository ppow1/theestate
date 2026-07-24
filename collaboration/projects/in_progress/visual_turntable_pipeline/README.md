# Visual Turntable Pipeline

**Status:** In progress  
**Established:** 2026-07-24  
**Purpose:** Preserve the working knowledge, workflows, evidence, and next actions for generating an eight-view resident turnaround and converting selected outputs to transparent PNGs.

## Current result

The experiment established that one ComfyUI workflow can generate a candidate pool containing usable views for the full eight-angle sequence:

- 000 front
- 045 front-right three-quarter
- 090 right profile
- 135 rear-right three-quarter
- 180 rear
- 225 rear-left three-quarter
- 270 left profile
- 315 front-left three-quarter

The most reliable approach was parallel absolute-angle generation with multiple stochastic candidates per angle. Three candidates per target angle produced a useful 24-image pool. Sequential relative rotation was less reliable and frequently collapsed into duplicate profile or front/rear views.

BiRefNet background removal successfully converted a selected opaque-background output into a true RGBA PNG with transparency. Checkerboard verification confirmed the alpha channel.

## Scope boundary

The current character is a **temporary visual-canon test fixture**, not final Evelyn and not canonical resident identity. It may be used to validate the Estate visual-canon pipeline without canonizing the character appearance.

## Repository package layout

- `workflows/` — ComfyUI workflow exports used during the experiment
- `samples/source_archives/` — candidate pools and source experiment archives
- `samples/contact_sheets/` — review sheets for candidate pools
- `samples/transparency_tests/` — background-removal verification evidence
- `canon_validation/` — reserved for the next canon-validation run
- `METHOD.md` — repeatable operating method
- `DECISIONS.md` — decisions reached during testing
- `LESSONS_LEARNED.md` — failures and findings worth preserving
- `STATUS.md` — exact current stopping point
- `NEXT_STEPS.md` — immediate continuation sequence

## Canonical warning

Do not rename the temporary fixture to Evelyn or place it in an authoritative resident visual-bible path until the canon-validation step has been completed and the Steward explicitly accepts the result.
