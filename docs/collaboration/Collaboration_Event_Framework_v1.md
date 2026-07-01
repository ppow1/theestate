# Collaboration Event Framework v1

Status: Implemented
Classification: Estate Internal
Owner: Alfred / Chief of Staff
Boundary Authority: Privacy and Boundary Office

## Purpose

The Collaboration Event Framework records a local-first operational event trail for existing Collaboration Layer tooling. It supports routing, inbox watching, the Operations Board, audit summaries, and future local automation without redesigning the Communication Bus.

This framework is not a transport adapter, not GitHub integration, and not a new governance system.

## Event Format

Events are appended as JSON Lines records. Each record uses this shape:

```json
{
  "id": "evt_YYYYMMDD_HHMMSS_ab12cd34",
  "version": 1,
  "type": "message.routed",
  "created_at": "2026-07-01T00:00:00",
  "source": "collaboration.routing_engine",
  "subject_id": "msg_example",
  "classification": "Estate Internal",
  "payload": {}
}
```

Required fields are `id`, `version`, `type`, `created_at`, `source`, `classification`, and `payload`. `subject_id` may be null when an event does not refer to one message, work item, review, promotion, or audit artifact.

## Event Types

Supported event types are:

- `message.routed`
- `inbox.updated`
- `work.claimed`
- `work.completed`
- `work.blocked`
- `review.requested`
- `promotion.requested`
- `audit.result.created`

Unsupported event types are rejected by the event module so the trail remains predictable and does not introduce new lifecycle states.

## Generated Files

The framework generates:

- `runtime/collaboration/events/events.jsonl` — append-only local event trail.
- `runtime/collaboration/events/latest.json` — latest valid event record.
- `collaboration/status/event_summary.json` — repository-visible operational summary of event counts, recent events, malformed record count, and read errors.

The runtime event log is local operational state. The status summary is intended for local dashboards and repository-visible status checks.

## CLI Usage

Summarize events in human-readable form:

```bash
python -m estate.cli.main collaboration-events
```

Summarize events as JSON:

```bash
python -m estate.cli.main collaboration-events --json
```

The command tolerates a missing event log and writes `collaboration/status/event_summary.json` with zero events when no log exists.

## Existing Tooling Integration

The Alfred routing engine emits `message.routed` events for routing decisions where practical. The worker inbox watcher emits `inbox.updated` after writing inbox summaries.

## Limitations

- The framework is local-first and does not require network access.
- It does not replace the Communication Bus.
- It does not make GitHub the event bus.
- It does not directly edit the ledger or development devlog.
- Malformed JSONL lines and invalid event records are reported in summaries instead of crashing readers.
- Partial or missing runtime state is treated as an empty event trail.
