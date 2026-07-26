# Conversation specification reconciliation (WP-4210)

WP-4210 reviews one or more WP-4209 staging bundles together. Inputs, pending
definitions, and proposed destinations are read-only. Every output is non-canonical,
review-required evidence; the command cannot approve or promote a candidate.

From the repository root:

```bash
PYTHONPATH=src python -m estate.core.conversation_specification_reconciliation \
  staging/conversation_specifications/<run-one> \
  staging/conversation_specifications/<run-two> \
  --expected "WP-4127 through WP-4130" \
  --generate-compatible-drafts
```

Use `--pending-root` only to select an alternate read-only pending-definition tree
and `--output-root` to select the derived bundle root. The default output is
`staging/conversation_reconciliation/<reconciliation-run-id>/`.

The bundle contains `reconciliation_manifest.json`, `coverage_report.json`,
`candidate_assessments.jsonl`, `duplicate_comparisons.json`,
`reconciliation_report.md`, `promotion_plan.json`, `diagnostics.json`, and optional
files below `reconciled_candidates/`. Compatible drafts include section source
hashes and remain review-only. Material conflicts never produce a draft.

Exit status `0` means the evidence is ready for human review, not accepted. Exit
status `2` means missing, unexpected, invalid, conflicting, tampered, incomplete,
or otherwise review-blocking evidence was found. Input/contract errors raise a
fatal command error. Inspect the Markdown report first, then the machine-readable
assessments and promotion plan. The promotion plan describes possible human actions
only and writes nothing to any proposed destination.
