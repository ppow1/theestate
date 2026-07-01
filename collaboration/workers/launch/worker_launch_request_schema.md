# Worker Launch Request Schema v1

Status: Version 1 Schema
Classification: Estate Internal

## Purpose

This schema defines the structured request used to launch a local Estate worker through the Local Worker Launch Adapter.

## Required Fields

```json
{
  "request_id": "launch_0001",
  "worker_id": "local_builder_001",
  "requested_by": "Chief Architect #2",
  "model": "qwen2.5-coder:7b",
  "role": "builder",
  "work_package_id": "WP-LEAP-001",
  "work_package_path": "collaboration/work_packages/open/WP-LEAP-001_Audit_Worker_v1_Local_Ollama.md",
  "classification": "Estate Internal",
  "mode": "manual_one_shot",
  "requested_at": "2026-06-30T00:00:00",
  "notes": "Launch a local builder worker for the assigned work package."
}
```

## Field Definitions

- `request_id`: Unique launch request identifier.
- `worker_id`: Intended worker identity for this launch.
- `requested_by`: Person, office, or worker requesting the launch.
- `model`: Ollama model name to run.
- `role`: Worker role such as builder, reviewer, architect, auditor, or researcher.
- `work_package_id`: Assigned work package identifier.
- `work_package_path`: Local repository path to the assigned work package.
- `classification`: Privacy and boundary classification.
- `mode`: Launch mode. Version 1 supports `manual_one_shot`.
- `requested_at`: Request timestamp.
- `notes`: Optional launch notes.

## Validation Rules

- `model` must appear in `ollama list`.
- `work_package_path` must exist locally.
- `classification` must not violate Privacy and Boundary rules.
- `mode` must be `manual_one_shot` for v1.
- The request must not contain secrets, tokens, or credential material.