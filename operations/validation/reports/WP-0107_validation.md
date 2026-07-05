# Work Package Validation Report — WP-0107

- Timestamp: 2026-07-05T00:01:28+00:00
- Work package ID: WP-0107
- Local branch: work
- Git commit: 51e0b5912c9ca6293eea2f0f767531bc8b660fdb
- Validation status: failed
- Recipe used: wp-0107-alfred-online-duty-runner
- Recipe title: WP-0107 — Alfred Online Duty Runner

## Commands Run
- `python -m estate.cli.main alfred-duty --json` — passed (exit 0, 0.396s)
- `python -m estate.cli.main resident-duty --resident Alfred --json` — passed (exit 0, 0.408s)
- `python -m estate.cli.main resident-presence --resident Alfred --json` — passed (exit 0, 0.399s)
- `python -m pytest tests/test_alfred_duty.py tests/test_resident_presence.py tests/test_resident_cards.py` — failed (exit 1, 0.928s)

## Findings
- None.

## Warnings
- None.

## Failures
- Command failed: python -m pytest tests/test_alfred_duty.py tests/test_resident_presence.py tests/test_resident_cards.py (exit 1)

## Receipt Validation
- Receipt status: incomplete
- Completion artifact: collaboration/work_packages/completions/WP-0107_codex_done.json
- Receipt gaps: pull_request_url_or_not_applicable_reason, codex_status_done

## Production Readiness
- Production ready: False
- Execution status: failed
- Receipt status: incomplete
- Blocking reasons: Completion artifact is missing required metadata: pull_request_url_or_not_applicable_reason, codex_status_done; Execution status blocks readiness: failed.
- Non-blocking findings: None

## Generated Artifacts
- `operations/validation/reports/WP-0107_validation.md`
- `runtime/validation/work_packages/WP-0107_validation.json`
- `runtime/validation/work_packages/latest.json`

## Reviewer Recommendation
Chief Architect should review failures before approval.
