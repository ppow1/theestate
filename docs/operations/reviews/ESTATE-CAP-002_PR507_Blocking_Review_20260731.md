# ESTATE-CAP-002 PR #507 Blocking Review

Date: 2026-07-31

## Review result

Starting PR head: `628101a82d7b4b3b76b348826709070c054f4cd8`  
Base reviewed: `ff3aae80a1eeacc88ac1ab452e79ca4f4bc61aeb`

The review found two correctable in-scope blockers. The resident manifest was
closed but did not sufficiently bind authority, evidence freshness, current
status evidence, or safe source references. The onboarding lint accepted
section marker words without requiring structural labels and could accept
unresolved placeholders in a non-template package.

## Corrections

The manifest schema remains versioned and closed, compatible with rather than
replacing the provider catalog. It now requires:

- strict capability IDs and semantic versions;
- maturity, current availability, and dispatchability as separate fields;
- provider/resident-tool/service/connector/human-worker binding with provider
  and adapter identity;
- enumerated classification ceiling;
- closed authority object with required authorization and prohibited actions;
- unique accepted inputs and outputs;
- closed evidence objects with kind, safe source reference, state, observation
  time, optional expiry, and lowercase SHA-256 digest;
- no absolute, drive-qualified, or traversing source reference;
- no open metadata or hidden authority-bearing properties.

The existing work-package validator now exposes the bounded
`validate-capability-onboarding` lint path. It checks structural labels for
owner, identity, maturity, provider/tool disposition, authority, scopes,
evidence, tests, acceptance, rollback/deprecation, and Steward-stop behavior.
The canonical template is intentionally allowed to retain fill-in
placeholders; non-template packages with unresolved placeholders fail with
actionable diagnostics. Ordinary work-package recipes remain unchanged.

The runbook was corrected to distinguish an existing provider configuration
from a catalog entry and to assign Grace, Helen, Engineering, the resident
owner, and Steward/Chief Architect responsibilities at each lifecycle phase.

## Paper exercises

1. Whisper transcription request: Grace asks Helen; Helen reports the existing
   capability/provider maturity separately from current dispatchability,
   requires owner authorization and media scope, and records the next inquiry
   and assessment. No repository implementation authority is implied.
2. Whisper model installed but no governed adapter: Helen reports provider
   available at most Level 2, current dispatchability not_dispatchable, and
   returns a capability-gap/enabling-project proposal. Grace may resume only
   after registration, fresh evidence, and re-evaluation.
3. Qwen Coder repository implementation: Grace receives provider availability
   but distinguishes it from dispatchability. Helen supplies qualification,
   health, capacity, and authorization evidence; PTM/Engineering/Operations/
   Dispatch and final handoff are required before execution.
4. Historian archival search with conflicting sources: the resident wrapper is
   read-only, records source IDs/retrieval dates/citations/conflicts and
   uncertainty, and stops for owner review; inference cannot replace evidence.
5. Legal jurisdiction-bound tool with stale authority: the request is held as
   unavailable/not dispatchable, the jurisdiction/effective-date boundary is
   preserved, and stale authority is refreshed before any new result.
6. Worker lacks bootstrap capability: Helen records a second capability gap
   and returns a bounded enabling-project proposal; no recursive self-claim or
   invented bootstrap is allowed.

Each exercise identifies an owner, maturity, availability, required authority,
next record, safe stop, and whether Grace can resume. None implies live
provider execution or institutional acceptance.

## Validation

- Onboarding, schema, validator, provider, Grace/Helen, PTM, Dispatch, handoff,
  and work-package matrix: **92 passed**.
- Draft 2020-12 schema validation with `FormatChecker`: passed.
- Positive and negative manifest tests: passed, including extra authority,
  absolute/traversing reference, malformed binding, and missing contract data.
- Template lint: passed.
- Incomplete package and non-template placeholder lint: passed as failures with
  actionable diagnostics.
- Python compilation and `git diff --check`: passed.

The two inherited temporary-root CLI failures reproduce identically on both
base and head:

- `test_capability_lifecycle_cli_registration`: fixture expects 1, runtime
  discovers 6.
- `test_cli_writes_visualization_outputs`: fixture expects 1, runtime discovers
  6.

They arise because the subprocess root-discovery behavior resolves the
checkout rather than the temporary fixture root. They predate this PR, are
outside onboarding/schema/lint behavior, and remain documented rather than
expanded into this bounded correction.

## Final disposition

No worked-example provider was implemented or invoked. No second registry,
Dispatch path, PTM system, personnel system, or receipt authority was added.
No unresolved architecture decision blocks this PR. The remaining temporary
root failures are inherited and non-blocking for this package.

After commit and push, PR #507 remains draft and unmerged. Next Steward action:
review the corrected draft PR and explicitly authorize merge if accepted.
