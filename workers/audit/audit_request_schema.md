# Audit Request Schema v1

Status: Schema
Adapter: audit
Classification: Estate Internal

## Purpose

Audit requests allow GitHub-mediated workers to request authoritative local Estate validation without requiring Pat to copy and paste terminal output.

## Required Fields

- request_id
- requested_by
- work_package_id
- target_commit
- reason
- requested_at
- classification
- expected_checks
- promotion_context

## Example

    {
      "request_id": "audit_YYYYMMDD_HHMMSS_slug",
      "adapter": "audit",
      "requested_by": "Chief Architect #2",
      "work_package_id": "WP-EXAMPLE-001",
      "target_commit": "main",
      "reason": "Validate current branch after worker output.",
      "requested_at": "YYYY-MM-DDTHH:MM:SS",
      "classification": "Estate Internal",
      "expected_checks": ["estate audit"],
      "promotion_context": "Result may be committed to collaboration/audit/results if it contains no Local Only material."
    }

## Placement

Pending requests belong in:

    collaboration/audit/pending/

## Boundary Rule

Do not include private prompts, generated media, local-only artifact details, or confidential material in the request.
