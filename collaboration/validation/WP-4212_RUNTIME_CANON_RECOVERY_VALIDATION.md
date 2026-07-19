# WP-4212 Runtime-Canon Recovery Validation

## Result

The implementation was validated on 2026-07-19 as deterministic,
pending-definition matched, assignment-independent, and non-promoting.

## Commands

```text
PYTHONPATH=src pytest -q tests/test_runtime_canon_recovery.py
PYTHONPATH=src pytest -q tests/test_conversation_archive_ingestion.py tests/test_conversation_specification_extraction.py tests/test_conversation_scope_validation.py tests/test_runtime_canon_recovery.py
PYTHONPATH=src pytest -q
PYTHONPATH=src python -m estate.core.runtime_canon_recovery tests/fixtures/conversations/wp_4107_4116_wrong_canons.txt --output-root /tmp/wp4212-validation --machine-readable
```

## Inputs and availability

Repository search found the two existing plain-text WP-4211 fixtures:

- `tests/fixtures/conversations/wp_4107_4116_wrong_canons.txt`
- `tests/fixtures/conversations/wp_4117_correction_refusal.txt`

None of the four requested real MHTML archives were available anywhere under the
repository workspace, so no result is claimed for them:

- `127-130 #1.mhtml`
- `127-130 #1(1).mhtml`
- `Estate work-package continuation2.mhtml`
- `Chief Architect Renewal Verification.mhtml`

## Regression observations

The available wrong-canon fixture contains short `WP-0026` and `WP-0027` output.
Both decisions remain visible, but fail the substantive structure threshold rather
than being represented as complete supporting documents. The detector does not
derive expected authority from historical or assignment references.

The integration fixture in `tests/test_runtime_canon_recovery.py` deliberately
assigns `WP-9999` and then supplies a complete `WP-4212` candidate. The candidate
still resolves uniquely to the `WP-4212` pending definition, is assessed, and is
staged with complete provenance. Two identical runs resolve to the same run path
and byte-identical deterministic JSON and Markdown artifacts.

The repository's pending directory currently contains legacy malformed and
duplicate identifier conditions. The production index reports these explicitly as
fatal diagnostics; it does not invent an authoritative match. Targeted integration
tests use an isolated valid pending directory to exercise the full preservation
path.

The focused predecessor and WP-4212 suite passed **40 tests**. The repository-wide
suite passed **1,581 tests** and reported four unrelated pre-existing failures in
OpenWebUI campaign-02 placeholder/voice expectations and the historical reflection
handoff's final-line expectation. WP-4212 tests had no failures.

## Safety findings

- Candidate detection, resolution, assessment, reconciliation, and staging do not
  consume assignment scope as a gate.
- The renderer targets only its derived run staging directory.
- The pending definition is read-only and is checked unchanged by tests.
- Every manifest sets `automatic_promotion_permitted` to false.
- Competing complete candidates remain review-blocked and are never synthesized.

Repository commit at execution start: `f5008be0ff58cc272540b9d48d876ce276c26fe6`.
The committed implementation SHA is recorded by the pull request and by artifacts
generated from the committed tree.
