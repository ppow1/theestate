# PL-0014 — External Worker Telemetry Adapter

## Work-package status

- Source: `operations/boards/parking_lot.md`, item `PL-0014`
- Status: Pending implementation
- Owner: Future assigned Engineering worker
- Reviewers: Alfred and Helen for supervision semantics; Security/Privacy for credential boundaries; operator for acceptance
- Implementation mode: isolated staging only
- Production activation: explicitly excluded; requires a separate install-handoff work package

## 1. Purpose

Build and prove a provider-neutral, read-only telemetry adapter that observes external AI workers (initially Codex) and truthfully reports assignment acceptance, start, progress, completion, failure, stall, timeout, and unknown states. The adapter supplies evidence to supervisors; it does not dispatch work, control a worker, approve results, merge code, or change institutional state.

This package is implementation-ready but does **not** authorize production telemetry. Implementation must occur entirely beneath the staging root defined in section 4. No shared runtime file may be edited until a separately reviewed install-handoff package identifies and authorizes each integration change.

## 2. Outcomes and non-goals

### Required outcomes

1. A provider-neutral state model and immutable observation envelope.
2. A Codex provider adapter based on documented official APIs when an adequate API exists.
3. Durable, replayable telemetry with assignment/worker correlation and provenance.
4. Read-only Alfred and Helen projections produced as staging artifacts.
5. Diagnostics, synthetic fixtures, and automated unit/integration tests.
6. An install-handoff manifest that describes—but does not perform—future production integration.

### Non-goals

- Starting, stopping, retrying, messaging, approving, or otherwise controlling workers.
- Treating telemetry as proof that output is correct, accepted, merged, deployed, or institutionally complete.
- Editing Open WebUI, Grace, Alfred, Helen, Local Compute, Evelyn, `resident-runtime`, shared CLI files, production configuration, or production data stores.
- Scraping prompts, generated source, secrets, hidden reasoning, or unrelated browser content.
- Installing a daemon, browser extension, credential, scheduled task, webhook, or network listener.
- Updating the Parking Lot item or promoting it through a governance lane.

## 3. Normative state model

The canonical normalized states are:

| State | Terminal | Meaning | Minimum evidence |
|---|---:|---|---|
| `DISCOVERED` | no | Assignment is known locally; provider receipt is not proved. | Valid assignment record. |
| `SUBMITTED` | no | Provider reports successful submission and supplies a provider assignment/run identifier. | Provider response or signed fixture. |
| `ACCEPTED` | no | Provider explicitly acknowledges or queues the assignment. | Provider event/status distinct from the local request. |
| `STARTED` | no | Provider explicitly reports execution, or the first unambiguous execution event occurs. | Provider running status or documented start-class event. |
| `IN_PROGRESS` | no | Fresh evidence shows execution after start. | Monotonic progress/event evidence. |
| `STALLED` | no | Started work has no qualifying activity for the configured stall window. | Last qualifying activity plus evaluated policy. |
| `SUCCEEDED` | yes | Provider reports successful terminal execution. | Terminal provider event/status. |
| `FAILED` | yes | Provider reports terminal failure. | Terminal status and sanitized error classification. |
| `CANCELLED` | yes | Provider reports cancellation. | Terminal provider event/status; actor only when supplied. |
| `TIMED_OUT` | yes | Assignment exceeds its explicit execution deadline without a trusted terminal event. | Deadline, current time, and policy evaluation. |
| `UNKNOWN` | no | Evidence is absent, contradictory, unmapped, stale beyond reliability, or provider access is unavailable. | Reason code and last trustworthy observation, if any. |

`STALLED` and `TIMED_OUT` are adapter-derived supervisory assessments, not invented provider claims. `UNKNOWN` is safer than guessing. Terminal states never change in place: a later contradiction or provider correction is appended as a new observation and the projection enters `UNKNOWN` with `terminal_conflict` until reviewed. A new attempt receives a new `attempt_id`; it must not reopen an old attempt.

### Allowed transitions

The normal path is `DISCOVERED -> SUBMITTED -> ACCEPTED -> STARTED -> IN_PROGRESS -> SUCCEEDED|FAILED|CANCELLED`. `ACCEPTED -> SUCCEEDED|FAILED|CANCELLED` and `STARTED -> SUCCEEDED|FAILED|CANCELLED` are permitted when a provider omits intermediate events. `STARTED|IN_PROGRESS <-> STALLED` is allowed when qualifying activity stops and later resumes. Any nonterminal state may become `TIMED_OUT` after its deadline or `UNKNOWN` when trustworthy interpretation is impossible. Observed out-of-order events remain in the log but cannot regress the materialized state.

## 4. Explicit file ownership and parallel safety

The implementing worker exclusively owns only this new staging subtree:

```text
staging/external_worker_telemetry/
  README.md
  pyproject.toml
  src/external_worker_telemetry/
    __init__.py
    model.py
    correlation.py
    policy.py
    store.py
    projection.py
    diagnostics.py
    providers/base.py
    providers/codex.py
  schemas/
    assignment.v1.schema.json
    observation.v1.schema.json
    worker_identity.v1.schema.json
    snapshot.v1.schema.json
    install_handoff.v1.schema.json
  fixtures/synthetic/
  tests/unit/
  tests/integration/
  research/official_api_research.md
  research/source_inventory.json
  output/.gitkeep
  INSTALL_HANDOFF.md
  install_handoff.json
```

It may also create its completion receipt at `collaboration/work_packages/completions/PL-0014_implementation_completion_receipt.md`. All other paths are read-only. In particular, the implementation must not modify Open WebUI, Grace, Alfred, Helen, Local Compute, Evelyn, resident-runtime, shared CLI, `operations/`, existing `runtime/`, or existing shared schemas/configuration.

Parallel workers may freely change paths outside this staging subtree. The implementer must not reformat, rename, delete, or opportunistically repair unrelated files. Staging code must not import private modules from mutable shared runtimes; define provider and projection ports locally. If a required seam is unavailable, record it in `INSTALL_HANDOFF.md` rather than changing its owner’s file. Generated observations and diagnostics belong under ignored temporary test directories or `staging/external_worker_telemetry/output/`; tests must use per-test temporary directories and never shared live data.

## 5. Official integration research gate

Official API integration is the preferred and default path. Before coding a live provider client, the implementer must inventory current official provider documentation, SDKs, authentication methods, run/task endpoints, event streams or webhooks, status vocabulary, pagination/cursors, timestamps, identifiers, error/rate-limit behavior, retention, and terms relevant to monitoring. Technical research must use primary official sources only.

`research/official_api_research.md` must record for each claim: provider, document title, canonical URL, access date in UTC, relevant API/SDK version, capability, limitation, and implementation decision. `source_inventory.json` must store the same sources machine-readably with a content/version identifier when the provider publishes one. Research must explicitly map provider evidence to each normalized state and state whether acceptance is distinguishable from submission and whether start is distinguishable from progress.

The Codex client may be implemented only against a documented, supported surface. It must use a narrow interface (`list/get events or status`, no mutation methods), injectable transport, cursor handling, bounded backoff, and sanitized errors. If no official surface supplies adequate telemetry, deliver the provider-neutral core and an `official_api_gap` capability report; do not silently proceed to UI observation.

## 6. Browser/UI fallback boundary

Browser automation or UI observation is a separately gated fallback, not an equivalent transport. This package permits only a **synthetic UI observer prototype** against repository-owned HTML fixtures. Observing a real provider UI requires a later written authorization from the operator and Security/Privacy, plus evidence that official API and export/event options are inadequate.

Any later real-UI proposal must be read-only; use a dedicated profile and least-privilege session; observe only allow-listed assignment/status elements; redact content at capture time; store no screenshots or DOM dumps by default; obey provider terms; rate-limit access; expose a kill switch; and stop on selector drift, authentication challenge, CAPTCHA, consent dialog, unexpected origin, or ambiguous identity. It must never click submit/approve/cancel/retry, inject scripts into unrelated origins, intercept credentials/tokens, defeat access controls, use computer vision as sole terminal-state evidence, or infer status from color, spinner presence, window title, notification text, elapsed time, or model prose alone.

## 7. Assignment acceptance and start detection

- **Submission** requires a successful provider response containing a durable provider identifier; a local button click or HTTP request attempt is insufficient.
- **Acceptance** requires an explicit provider `accepted`/`queued` equivalent or an official event documented as acknowledgement. If the provider conflates submission and acceptance, report `SUBMITTED` with `acceptance_not_observable`; do not synthesize `ACCEPTED`.
- **Start** requires an explicit running/start event or first documented execution-class event carrying the same provider assignment/run ID. Queue position changes and mere passage of time do not prove start.
- Duplicate evidence with the same provider event ID is idempotent. Conflicting identifiers or an event predating submission produce `UNKNOWN` and a diagnostic.
- Every retry is a distinct `attempt_id`, correlated to the stable Estate `assignment_id`.

## 8. Progress, terminal, stall, and timeout reporting

Progress is an ordered series of provider events, not an invented percentage. The normalized progress payload permits `phase`, provider-supplied `percent`, completed/total units, a sanitized status code, and `last_activity_at`; absent values remain null. Never estimate percentage from elapsed time or token/output volume. Qualifying activity is a new provider event, a monotonic provider update timestamp, or documented counter advancement—not a successful poll with unchanged content.

Completion and failure require authoritative terminal provider evidence. Preserve a sanitized error `category`, provider error `code`, retryability when officially defined, and a reference/hash rather than sensitive error bodies. `SUCCEEDED` means execution ended successfully, not that deliverables passed validation.

Policy defaults in fixtures are: poll active attempts every 15 seconds with deterministic ±20% jitter; accepted/queued attempts every 30 seconds; terminal attempts are not polled; stall warning after 10 minutes without qualifying activity; timeout only at an assignment-specific `deadline_at` (synthetic default 60 minutes). These are defaults, not hard-coded provider limits. Honor official rate-limit headers, use exponential backoff capped at 5 minutes, and perform at most one concurrent request per provider assignment. Event streams are preferred: persist event checkpoints immediately, emit a heartbeat at most every 60 seconds, and run a reconciliation poll every 5 minutes. After restart, resume from the last committed cursor and overlap one page/window, relying on event-ID deduplication.

Clock calculations use UTC and a monotonic clock within a process. If wall-clock skew exceeds 60 seconds, deadlines cannot be evaluated reliably: report `UNKNOWN/clock_skew` rather than timing out. After three consecutive transport/auth/rate-limit failures, open a circuit for the provider-configured interval, preserve last-known state as stale metadata, and project `UNKNOWN/provider_unavailable`; never convert observer failure into worker `FAILED`.

## 9. Persistent records and schemas

Schemas use JSON Schema Draft 2020-12, reject unknown fields where practical, and version names and payloads independently. UTC timestamps use RFC 3339 with `Z`; IDs are opaque bounded strings; all records have a `schema_version` and `recorded_at`.

### Assignment record (`assignment.v1`)

Required: `assignment_id`, `attempt_id`, `provider`, `provider_assignment_id`, optional `provider_run_id`, `worker_identity_id`, `submitted_at`, optional `deadline_at`, `correlation_version`, and `scope_hash`. It must not contain prompt text, source code, credentials, or human-readable secrets.

### Worker identity (`worker_identity.v1`)

Required: stable Estate `worker_identity_id`, provider, provider-native subject/account/workspace identifiers as salted hashes, declared worker type/model when supplied, identity source, first/last observed timestamps, and verification state (`verified`, `unverified`, `conflicted`, `unknown`). Display names are labels, never correlation keys.

### Observation envelope (`observation.v1`)

Required fields:

```json
{
  "schema_version": "1.0.0",
  "observation_id": "uuid",
  "assignment_id": "estate-id",
  "attempt_id": "estate-attempt-id",
  "worker_identity_id": "estate-worker-id",
  "provider": "codex",
  "provider_assignment_id": "opaque-id",
  "provider_event_id": "opaque-id-or-null",
  "observed_at": "RFC3339 UTC",
  "recorded_at": "RFC3339 UTC",
  "normalized_state": "IN_PROGRESS",
  "provider_state": "bounded-sanitized-value",
  "reason_code": "provider_event",
  "progress": {"phase": null, "percent": null, "completed": null, "total": null},
  "source": {"transport": "official_api", "endpoint_class": "events", "api_version": "value", "cursor_hash": "sha256"},
  "provenance": {"raw_payload_sha256": "sha256", "adapter_version": "semver", "mapping_version": "semver", "fixture": false},
  "integrity": {"previous_record_sha256": "sha256-or-null", "record_sha256": "sha256"}
}
```

The store is append-only JSON Lines for staging, one stream per assignment attempt plus an atomic materialized snapshot. Writes use temporary-file + fsync + atomic rename where applicable; a process lock prevents concurrent writers. Hashes cover canonicalized records excluding `integrity.record_sha256`. On load, schema, hash chain, duplicate IDs, ordering, and correlation are validated. Corruption quarantines the affected stream and yields `UNKNOWN/telemetry_integrity_failure`; it is never auto-repaired or truncated.

Retention and deletion are policy inputs recorded in the handoff, not invented here. Synthetic fixtures contain no real identifiers. Raw provider bodies are not persisted; only their hashes and allow-listed normalized fields are retained.

## 10. Identity and correlation rules

The correlation tuple is `(provider, provider workspace/tenant hash, provider_assignment_id, provider_run_id when present)` mapped to `(assignment_id, attempt_id, worker_identity_id)`. Correlation is established from the submission receipt or a pre-registered synthetic assignment; timestamps, titles, prompt text, branch names, display names, and “most recent run” heuristics may corroborate but must never establish identity.

One provider run maps to exactly one attempt. Reuse, absence, or collision of a provider ID causes `UNKNOWN/correlation_conflict`, quarantines the event from all projections, and raises an operator diagnostic. Account/workspace mismatch is handled identically. Mapping changes are append-only records with actor, reason, time, prior/new IDs, and evidence; historical observations are not rewritten.

## 11. Provenance and audit

Every observation must identify transport, official API/version or synthetic fixture, provider event ID, observation and ingestion times, mapping and adapter versions, sanitized raw-payload hash, cursor hash, assignment/attempt/worker IDs, prior/new projected state, reason code, and record hash-chain linkage. Derived events (`STALLED`, `TIMED_OUT`, `UNKNOWN`) additionally record policy version, thresholds, clock basis, and source observation IDs.

Audit logs are append-only and deterministic under replay. Secrets, bearer tokens, cookies, prompt/output bodies, hidden reasoning, source code, and unnecessary personal data are forbidden. Redaction happens before logging and hashing of any retained normalized body. Diagnostics may reference observation IDs and hashes, not sensitive payloads. A replay of the same ordered evidence and policy version must produce byte-equivalent logical snapshots (excluding explicitly documented processing timestamps).

## 12. Alfred and Helen read-only supervision surfaces

The adapter writes two local staging projections; it does not edit either resident’s files or call their runtime:

- `output/alfred_assignment_snapshot.json`: assignment, attempt, normalized state, state confidence (`authoritative`, `derived`, `unknown`), last trustworthy activity, age, deadline/stall assessment, terminal evidence reference, and concise diagnostic flags.
- `output/helen_worker_snapshot.json`: pseudonymous worker identity, correlated active/terminal attempt counts, availability as `observed_active|no_active_assignment|unknown`, last observed time, provider health, and identity/correlation warnings.

Both schemas must be documented and deny control fields. Alfred’s view cannot claim work quality or institutional completion. Helen’s view cannot infer performance, capability, employment status, wellbeing, discipline, or availability beyond observed assignment telemetry. Unknown/stale data is conspicuous and includes `as_of`, `stale_after`, and reason. Any future consumption by Alfred or Helen is an install-handoff task owned by those systems’ maintainers.

## 13. Operator diagnostics

Provide a staging-only diagnostic command/module that reads a supplied staging directory and emits structured JSON plus a redacted human summary. It must report adapter/schema/mapping versions; provider and circuit health; last successful observation; lag; cursor age; rate-limit/backoff state; active attempt counts; unknown/stalled/timed-out counts; correlation conflicts; schema/hash-chain/quarantine failures; clock skew; and next eligible poll time. Exit codes: `0` healthy, `2` degraded/unknown, `3` integrity or configuration failure. It must have `--offline` fixture/replay support and no mutation/control commands. Diagnostic output must pass secret-pattern tests.

## 14. Privacy and credential boundaries

- Credentials enter only through an injected secret provider or environment variable named in local documentation; never CLI arguments, repository files, fixtures, output, exception text, URLs, or hashes intended for comparison.
- Request only read scopes required for task/run status. A scope audit is a release gate; a token with mutation/admin scopes is rejected unless a later Security-approved handoff explicitly permits it.
- Never log headers, cookies, query tokens, full provider payloads, prompts, responses, generated code, hidden reasoning, email addresses, or unrelated account activity.
- Hash provider account/workspace IDs with an installation-specific salt stored outside the repository. Do not claim anonymization; the records remain restricted operational metadata.
- Apply bounded field lengths, allow-list provider fields, redact before persistence, use restrictive file permissions, and document retention/deletion controls for the future installer.
- Authentication failure yields provider-unavailable telemetry; never retry credentials aggressively, open a login UI, or weaken verification.

## 15. Safe failure and unknown handling

Fail closed to `UNKNOWN` on unmapped provider states, missing/colliding identifiers, invalid schema, corrupted chains, impossible transitions, stale evidence, authentication loss, cursor gaps, clock skew, or provider contract drift. Preserve the last trustworthy state only as `last_known_state`; do not present it as current. Continue collecting non-conflicting evidence when safe, but quarantine ambiguous evidence. Never mutate provider or Estate state as recovery. Backoff is bounded and jittered; retries are idempotent. An explicit operator-visible diagnostic is required for every unknown reason code. New provider states must first receive a mapping-version update, tests, and review.

## 16. Required synthetic fixtures

Create deterministic, invented fixtures for:

1. normal submitted-to-success event stream;
2. acceptance not observable;
3. immediate terminal failure;
4. cancellation;
5. progress with provider percentage and progress without percentage;
6. stall then resume;
7. hard deadline timeout;
8. delayed and out-of-order events;
9. duplicate event/page overlap;
10. unmapped provider state;
11. authentication and rate-limit failures with recovery;
12. provider outage/circuit opening;
13. clock skew;
14. worker/account mismatch and provider-ID collision;
15. terminal-state conflict;
16. malformed record and broken hash chain;
17. cursor restart/replay;
18. selector drift and unexpected-origin HTML for the synthetic UI fallback.

Each fixture includes expected observations, snapshot, diagnostics, and a manifest proving all people, accounts, tokens, assignments, and payloads are fictional.

## 17. Unit tests

Unit tests must cover schema acceptance/rejection; every allowed and forbidden state transition; provider-to-normalized mapping; acceptance/start evidence gates; progress nullability and monotonicity; stall/timeout boundaries; UTC/monotonic-clock and skew behavior; exponential backoff/jitter bounds; rate-limit handling; circuit breaker; event deduplication; cursor overlap; identity/correlation collision; redaction and bounded fields; canonical hashing/hash-chain verification; atomic store recovery; terminal immutability; unknown reason codes; snapshot projection; Alfred/Helen semantic restrictions; deterministic replay; diagnostic exit codes; and synthetic UI selector/origin fail-closed behavior.

Network, clocks, UUIDs, jitter, transports, secret sources, and filesystem locations must be injected. Unit tests make no network calls and use only temporary directories.

## 18. Integration tests

Using a local fake HTTP/SSE server and synthetic credentials, test:

1. submission receipt registration through successful official-event replay;
2. polling pagination, event-stream disconnect, cursor resume, and overlap deduplication;
3. restart from durable cursor without state regression or duplicate observations;
4. rate limiting, transport failures, circuit open/half-open/recovery;
5. stall, resume, deadline timeout, and late terminal conflict;
6. concurrent observations for multiple workers/assignments without cross-correlation;
7. malformed/hostile bounded payloads and credential/redaction non-disclosure;
8. corrupted persistence quarantine and unaffected-stream continuity;
9. generation of read-only Alfred/Helen snapshots and diagnostics;
10. full offline synthetic UI fixture path, proving no real browser/provider is contacted.

Integration tests must bind only loopback, perform no live provider calls, and assert that no file outside the test temporary directory changes.

## 19. Validation scenarios

| Scenario | Expected result |
|---|---|
| Provider acknowledges but never starts | `ACCEPTED`, then stale/unknown or timeout per explicit policy; never `STARTED`. |
| First evidence is an official running event | Intermediate omission noted; state becomes `STARTED`. |
| Progress goes quiet, then resumes | Derived `STALLED`, append resume evidence, return to `IN_PROGRESS`; history remains. |
| Adapter loses authentication | Worker is not failed; projection is `UNKNOWN/provider_unavailable`, redacted diagnostic emitted. |
| Deadline passes during outage | `UNKNOWN/provider_unavailable`, not `TIMED_OUT`, until trustworthy clock/evidence evaluation is possible. |
| Success arrives after derived timeout | Preserve both; projection becomes `UNKNOWN/terminal_conflict` for review. |
| Two Estate assignments claim one provider run | Both are quarantined from current projections with correlation-conflict diagnostics. |
| New provider state appears | Store allow-listed evidence, report `UNKNOWN/unmapped_provider_state`, require reviewed mapping update. |
| Record is altered on disk | Hash validation fails; affected stream quarantined, other streams remain readable. |
| Alfred/Helen consume snapshot fixtures | They receive status and provenance only, with no command or institutional decision authority. |
| Synthetic UI changes selector/origin | Observer stops without interaction and reports `UNKNOWN/ui_contract_drift`. |

## 20. Anti-patterns (must be rejected in review)

- Equating a local request with provider acceptance or elapsed time with start/progress.
- Inventing progress percentages, converting observer outages to worker failures, or treating `SUCCEEDED` as validated/merged work.
- Polling in a tight loop, ignoring rate limits, retry storms, or polling terminal assignments forever.
- Correlating by prompt/title/time/display name, or attaching “latest run” without a durable ID.
- Mutable single-row status without append-only evidence, rewriting history, silent corruption repair, or unversioned mappings.
- Logging raw payloads, tokens, cookies, prompts, responses, source code, hidden reasoning, or personal identifiers.
- Real UI scraping without the separate gate; brittle selectors that guess; CAPTCHA bypass; mutation clicks; screenshots/DOM archives by default.
- Writing directly into Alfred/Helen/runtime files, importing private shared-runtime internals, adding shared CLI commands, or installing production services from staging.
- Defaulting unknown to queued/running/failed, suppressing conflicts, or allowing stale last-known state to appear current.

## 21. Implementation sequence and gates

1. **Research gate:** complete official-source inventory and state-capability matrix.
2. **Contract gate:** implement schemas, normalized transitions, ports, correlation, and policy with unit tests.
3. **Persistence gate:** append-only store, integrity, replay, quarantine, and deterministic projections.
4. **Provider gate:** implement only supported read-only official API behavior with fake-transport tests; otherwise document `official_api_gap`.
5. **Supervision gate:** generate staging-only Alfred/Helen fixtures and operator diagnostics.
6. **Fallback gate:** synthetic HTML observer only; document authorization prerequisites for any live UI work.
7. **Validation gate:** run all tests/scenarios, privacy scan, staging-boundary check, and package receipt.
8. **Handoff gate:** create `INSTALL_HANDOFF.md` and `install_handoff.json` listing proposed production-owned paths, owners, configuration, credentials/scopes, retention, rollback, compatibility, and validation—without touching or installing them.

## 22. Required validation commands

The later implementer must run from repository root (adjust only the Python launcher if unavailable) and record exact output in the implementation receipt:

```bash
python -m pytest staging/external_worker_telemetry/tests/unit -q
python -m pytest staging/external_worker_telemetry/tests/integration -q
python -m pytest staging/external_worker_telemetry/tests -q
python -m json.tool staging/external_worker_telemetry/install_handoff.json >/dev/null
find staging/external_worker_telemetry/schemas staging/external_worker_telemetry/fixtures -type f -name '*.json' -print0 | xargs -0 -n1 python -m json.tool >/dev/null
git diff --check
git status --short
```

Add a boundary check that compares the implementation commit to its parent and fails if any changed path is outside `staging/external_worker_telemetry/` and the one authorized completion receipt. Add a secret scan over the staging subtree and fixture manifest verification. Live-provider tests are explicitly not a completion requirement and must not run in this package.

## 23. Completion criteria

PL-0014 implementation is complete for **staging review only** when:

- all state definitions and transitions above are implemented without optimistic inference;
- acceptance and start detection are independently evidenced where the provider permits;
- progress, completion, failure, cancellation, stall, timeout, stale, and unknown behavior are durable and tested;
- official primary-source research and a versioned capability map justify the provider path;
- no real browser/UI observation exists and the synthetic fallback fails closed;
- versioned schemas validate all persistent records and snapshots;
- identity/correlation uses durable provider identifiers and detects conflicts;
- provenance, audit, replay, hash-chain, quarantine, and redaction tests pass;
- cadence, rate limiting, cursor recovery, circuit breaking, and clock behavior pass;
- Alfred and Helen staging projections are read-only, stale-aware, privacy-bounded, and contain no control authority;
- operator diagnostics are useful, structured, redacted, and correctly exit nonzero for degraded/integrity states;
- all required unit, integration, fixture, and validation scenarios pass offline;
- no forbidden/shared path changed and no production service, credential, live call, or telemetry was installed;
- the completion receipt identifies commit, changed paths, research sources, exact commands/results, known gaps, and rollback (`delete staging subtree`);
- install-handoff artifacts enumerate proposed integration work but clearly remain unexecuted;
- reviewers approve staging evidence and a separate package is authored before any shared-runtime or production change.

Passing this package does not promote the Parking Lot item, activate telemetry, authorize a provider credential, or approve an install. Those remain separate governed decisions.

## 24. Deliverables

- The complete `staging/external_worker_telemetry/` tree listed in section 4.
- Official API research and provider capability decision.
- Versioned schemas, provider-neutral core, official adapter if supportable, persistence, projections, and diagnostics.
- Synthetic fixtures and passing unit/integration evidence.
- Unexecuted install-handoff plan and manifest.
- `collaboration/work_packages/completions/PL-0014_implementation_completion_receipt.md`.

