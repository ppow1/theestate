# Office Validation, Audit, and Verdict Control Center

WP-0518 exposes real Office controls for validation, audit, and verdict operations while preserving the Estate boundary that validation evidence is not institutional acceptance.

## Controls

- `validation.refresh_center` inspects validation, audit, and verdict artifacts and supports result, package, date, owner, and attention-state filters.
- `validation.request` delegates validation and revalidation to `work_package_validation.validate_work_package` and refreshes readiness evidence when requested.
- `validation.acknowledge_failure` records local durable attention acknowledgement without changing the source failure evidence.
- `validation.automatic_validator_status` reports the existing `PostMergeAuditProcessor` status.
- `validation.open_artifact` verifies validation evidence, completion receipts, audit artifacts, and verdict artifacts are available under the Estate root.
- `validation.governed_retry` advances only the existing `PostMergeAuditProcessor` request queue.

No control creates a second validator, acceptance authority, verdict registry, or retry queue.
