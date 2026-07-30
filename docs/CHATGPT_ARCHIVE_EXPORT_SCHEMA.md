# ChatGPT archive export schema

Each `latest.json` and immutable revision is a `Conversation` object with `schemaVersion: "1.0"`, stable conversation identity, source URL, chronological `messages`, and `exportMetadata`.

`exportMetadata` contains `exportedAt`, `exporterVersion`, `complete`, `limitations`, and `hydration`:

```json
{
  "hydrationStartedAt": "ISO-8601",
  "hydrationEndedAt": "ISO-8601",
  "hydrationDurationMs": 0,
  "hydrationPasses": 0,
  "stablePassesObserved": 0,
  "initialMessageCount": 0,
  "finalMessageCount": 0,
  "topReached": false,
  "virtualizationDetected": false,
  "incrementalAccumulationUsed": false,
  "completenessStatus": "complete",
  "completenessWarnings": [],
  "containerDescription": "main[data-archive-conversation-scroll-container=\"true\"]",
  "firstMessageHash": "..."
}
```

Allowed `completenessStatus` values are `complete`, `incomplete`, `timed-out`, `container-not-found`, `unstable`, and `extraction-failed`. `complete` is valid only after convergence; reaching the safety ceiling, reaching the top once, or extracting a non-empty DOM snapshot is insufficient. `exportMetadata.complete` must be false for every other status.

Messages use `data-message-id` when exposed. Otherwise the exporter uses role plus normalized content identity for safe incremental deduplication. Virtualized records are accumulated during upward traversal and emitted in chronological order.
