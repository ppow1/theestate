# WP-0625 - Governed Automatic Admission and Bounded Audit Execution

Status: Proposed  
Priority: Critical  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-10

## Mission

Move the automatic validation loop from discovery into real controlled execution.

WP-0623 and WP-0624 now discover, correlate, consolidate, and quarantine canonical work-package candidates. WP-0625 must automatically admit eligible candidates and process them through the existing post-merge audit pipeline without requiring the Steward to name each work package manually.

Required flow:

```text
new canonical candidate
  -> eligibility evaluation
  -> automatic admission when pre-approved conditions are satisfied
  -> bounded audit processing
  -> deterministic validation
  -> Ring 2 prompt/review preparation
  -> verdict publication
  -> Office status update
```

This is implementation, not a new governance layer.

## Provider Assignment Guidance

Recommended provider: `codex_cloud_web`  
Local runtime required: false for implementation; true for live demonstration  
Do not use Codex CLI for normal implementation.

## Automatic Admission Rules

A canonical candidate is automatically admissible when all are true:

```text
canonical target resolves and validation binding is ready
candidate has completion-receipt evidence
work_package_id is unambiguous
candidate is not superseded, blocked, retired, or already finally audited
completion receipt parses
provider_execution_performed and dispatch_execution_performed are present
candidate falls within configured recency and queue limits
no explicit hold exists
```

Missing receipt metadata may allow admission into validation because receipt failure is itself audit evidence, but malformed identity or ambiguous work-package correlation must remain blocked.

Default behavior for newly discovered current work should be `auto_admit`.
Historical backfill should remain quarantined unless explicitly released.

## Candidate Classification

Classify candidates as:

```text
current
historical_backfill
manual_hold
ambiguous
already_audited
superseded
```

Current candidates use cursor time and configured recency windows. Historical candidates remain quarantined.

## Bounded Runtime Consumption

Add a real audit-processing limit to Operations Runtime.

Support a command equivalent to:

```powershell
python -m estate.cli.main operations-runtime run-once --discover-merges --auto-admit --process-audits --max-audit-requests 5 --json
```

The runtime must never process more than the configured maximum in one cycle.

Required counters:

```text
candidates_evaluated
candidates_auto_admitted
candidates_held
historical_candidates_quarantined
audits_started
audits_completed
audits_failed
audits_ring2_required
audits_verdicts_published
queue_limit_reached
```

## Existing Backlog Handling

Do not drain the old queue blindly.

Before processing:

```text
ignore superseded requests
ignore quarantined historical requests
prefer canonical admitted requests
skip requests already covered by a final verdict
respect explicit holds
```

Add reconciliation support so legacy requests inherit the canonical candidate state where correlation is available.

## Ring 2 Behavior

For each completed deterministic audit:

- write the Ring 2 prompt to the external validation root,
- publish `ring2_required` when no local model run is enabled,
- optionally run the configured local Ollama reviewer when explicitly enabled,
- never treat Ring 2 evidence as final institutional acceptance.

## CLI Requirements

Add commands equivalent to:

```powershell
python -m estate.cli.main merge-discovery admission-status --target estate-main --json
python -m estate.cli.main merge-discovery auto-admit --target estate-main --json
python -m estate.cli.main merge-discovery hold --target estate-main --work-package WP-XXXX --json
python -m estate.cli.main merge-discovery release --target estate-main --work-package WP-XXXX --json
python -m estate.cli.main operations-runtime run-once --discover-merges --auto-admit --process-audits --max-audit-requests 5 --json
```

Follow existing CLI conventions if names differ.

## Office Visibility

Expose:

```text
auto_admission_enabled
current_candidates
historical_candidates
admitted_candidates
held_candidates
active_audit_limit
audits_processed_last_cycle
latest_admitted_work_package
latest_audit_verdict
```

## Expected Artifacts

Expected files:

```text
src/estate/core/merge_discovery_admission.py
tests/test_merge_discovery_admission.py
docs/integration/governed_automatic_admission_and_bounded_audit_execution.md
```

Expected integration touchpoints:

```text
src/estate/core/merge_discovery.py
src/estate/core/merge_discovery_consolidation.py
src/estate/core/merge_discovery_runtime.py
src/estate/core/operations_runtime.py
src/estate/core/operations_runtime_service.py
src/estate/core/post_merge_audit_processor.py
src/estate/core/steward_command_center.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

## Test Requirements

Tests must prove:

- current receipt-backed candidates auto-admit,
- historical backfill remains quarantined,
- ambiguous and superseded candidates never admit,
- explicit hold and release work,
- final-verdict duplicates are skipped,
- runtime processes no more than the configured maximum,
- canonical admitted requests are preferred over legacy requests,
- deterministic validation runs,
- Ring 2 prompts are generated,
- verdicts are published,
- Office status updates,
- provider and dispatch execution remain false.

## Validation

```powershell
Clear-Host
cd A:\theestate
python -m py_compile src\estate\core\merge_discovery_admission.py
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_merge_discovery.py tests/test_merge_discovery_consolidation.py tests/test_merge_discovery_admission.py tests/test_operations_runtime.py tests/test_post_merge_audit_processor.py --basetemp Temp/pytest-auto-admission
python -m estate.cli.main validate-work-package --id WP-0625 --json
```

## Live Demonstration

After merge:

```powershell
Clear-Host
cd A:\theestate
git pull --ff-only origin main
$env:PYTHONPATH = "src"
python -m estate.cli.main merge-discovery scan --target estate-main --json
python -m estate.cli.main merge-discovery auto-admit --target estate-main --json
python -m estate.cli.main operations-runtime run-once --discover-merges --auto-admit --process-audits --max-audit-requests 5 --json
python -m estate.cli.main post-merge-audit status --json
python -m estate.cli.main operations-runtime status --json
```

Expected result:

```text
recent eligible work is found without naming work packages
eligible candidates are admitted automatically
no more than five audits run
historical backlog remains quarantined
validation and Ring 2 preparation complete
verdicts are published
no provider or dispatch execution occurs
```

## Completion Receipt

Create:

```text
collaboration/work_packages/completions/WP-0625_codex_done.json
```

Report candidates evaluated/admitted/held, historical candidates quarantined, audits processed, queue limit behavior, verdicts, Ring 2 artifacts, and false provider/dispatch execution values.

## Promotion Criteria

Ready when newly merged eligible work moves automatically from discovery through deterministic validation and verdict publication, bounded by a real per-cycle limit, while historical backlog remains controlled and authority boundaries remain intact.
