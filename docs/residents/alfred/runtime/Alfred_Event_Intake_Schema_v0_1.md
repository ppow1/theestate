# Alfred Event Intake Schema v0.1

## Event Types

Allowed event types are:

- `work_package_completed`
- `validation_failed`
- `validation_passed`
- `pull_request_merged`
- `local_runtime_error`
- `provider_unavailable`
- `queue_blocked`
- `resident_health_observation`
- `manual_steward_note`

## Required Fields

Each event must include:

- `event_id`: stable event identifier.
- `event_type`: one allowed event type.
- `source`: emitting adapter, office, command, or manual source.
- `timestamp`: ISO-8601 timestamp.
- `severity`: `info`, `notice`, `warning`, `error`, or `critical`.
- `recommended_verbosity`: `brief`, `standard`, `mid`, `detailed`, or `forensic`.
- `source_artifacts`: list of repository-visible evidence paths or external references.
- `required_action`: briefing/routing action requested; execution is not authorized.
- `authority_boundary`: boundary statement for Alfred's role and limitations.
- `payload`: event-specific JSON object.
- `steward_attention_required`: boolean.

## Authority Boundary Requirement

Every event must preserve that Alfred may brief, summarize, route, or recommend escalation only. Event intake must not authorize Alfred to approve, merge, validate, spend, hire, modify governance, inspect private local characters, or bypass boundary offices.

## Adapter Classification

Sources such as TextGen, Open WebUI, SillyTavern, and Ollama are interface/provider adapters. They are not Alfred's home and do not create live Estate access by themselves.
