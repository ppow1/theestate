# WP-4214 — Staged Work Package Duration Estimation

- **Status:** Pending
- **Source:** `PL-0015 — Work Package Duration Estimation`
- **Mode:** isolated staged implementation
- **Implementation root:** `collaboration/workstreams/WP-4214/`
- **Install authority:** none; a separate install-handoff work package is mandatory

## 1. Mission

Implement and validate a read-only, explainable estimator that predicts likely work-package duration before assignment, learns through versioned calibration against actual outcomes, and remains useful with repository history before PL-0014 live telemetry exists. This package does not install scheduling behavior or change assignment decisions.

## 2. Mandatory implementation boundary

All implementation, schemas, fixtures, tests, sample records, reports, and the implementation completion receipt MUST be created beneath `collaboration/workstreams/WP-4214/`. Do not edit production or shared runtime, CLI, scheduling, dispatch, Alfred, Helen, Open WebUI, Local Compute, Evelyn, resident, registry, queue, or worker files. Do not create a second task registry, queue, scheduler, or dispatch surface. Tests must prove no write outside the staged root or their temporary directory.

A later, separately authorized install-handoff package is required to integrate any staged output. That handoff must name owners, migrations, compatibility checks, rollback, and validation gates. WP-4214 completion alone grants no installation or dispatch authority.

## 3. Inputs

The request and feature vector must represent, without inventing unavailable values:

- work-package identifier, package type, and implementation-versus-documentation classification;
- expected files and affected subsystems;
- dependency count, each dependency's readiness, and unresolved blockers;
- anticipated code, test, schema, UI, and documentation scope (counts/ranges or `unknown`);
- conflict and integration risk factors, with reasons;
- worker type/class, authorized pseudonymous worker reference when permitted, and execution environment;
- available historical evidence and its reliability/freshness.

Feature extraction must preserve supplied, derived, missing, and conflicting states. It must never infer implementation size solely from prose length or treat a package's creation timestamp as its execution start.

## 4. Outputs

Each result must contain:

- predicted active engineering time and predicted elapsed/wall-clock time;
- separate active effort, queue, review, and integration components;
- lower, expected, and upper bounds using one documented unit;
- confidence classification and evidence-sufficiency classification;
- an explicit `unknown`/`not_estimable` result with reason codes;
- principal estimate drivers, comparable historical records, and material exclusions;
- request, estimator, policy, feature, worker-profile, evidence, and generated-at provenance;
- freshness/as-of data and append-only adjustment history.

Bounds must satisfy `lower <= expected <= upper`. Results must use honest granularity (for example, ranges or rounded minutes), never unsupported decimals or fabricated precision. Wall-clock composition must expose assumptions and must not collapse blocked time into active effort.

## 5. Persistent records and schemas

Define JSON Schema Draft 2020-12 contracts, examples, stable IDs, UTC RFC 3339 timestamps, explicit schema versions, and forward-compatibility policy for:

1. `estimate_request`;
2. `estimate_result`;
3. `feature_vector` / scoring inputs;
4. `worker_profile_ref` (reference, not a personnel dossier);
5. `actual_execution_outcome`;
6. `estimate_actual_comparison`;
7. `calibration_history`;
8. estimator/version provenance and adjustment history.

Records are append-only or superseded by explicit linkage; corrections do not silently rewrite history. Every derived field cites input record IDs and estimator/policy versions. Missing values remain null/unknown with reason codes. Schema validation rejects unknown status values, negative durations, inconsistent bounds, orphaned comparisons, and worker-specific adjustments without threshold evidence.

## 6. Deterministic estimation method

Version 1 is deterministic and inspectable; machine learning is out of scope. Document and implement:

1. Validate/classify the request and evidence.
2. Select eligible historical outcomes using package class, scope mix, subsystem overlap, dependency/readiness band, size band, risks, worker class, and environment.
3. Prefer robust bucketed or nearest-neighbor comparisons only when similarity and sample thresholds are met. Publish selected neighbors and distance/tie-breaking rules.
4. Fall back through broader buckets to a documented rules baseline. With insufficient inputs, widen bounds/reduce confidence or return `not_estimable`; never manufacture a central value.
5. Estimate active effort independently from queue, review, and integration time, then compose wall-clock bounds under explicit deterministic rules.
6. Apply a worker-specific factor only under Section 8's threshold, after package complexity is estimated, and record the unadjusted and adjusted values.
7. Emit stable logical output for identical normalized inputs, evidence snapshot, estimator version, and configuration. Processing timestamps may differ only where explicitly excluded from logical equivalence.

The baseline must use versioned, reviewable weights/bands rather than hidden judgment. Sparse-evidence rules must state thresholds and widening behavior. No ML training, opaque score, or automatic assignment is allowed.

## 7. Historical evidence policy

Eligible evidence and default reliability, highest first:

1. provider/PL-0014 authoritative attempt telemetry correlated to assignment and attempt;
2. complete completion receipt plus merged PR timestamps and validation evidence;
3. repository commit/merge evidence correlated to the package and attempt;
4. validated PR lifecycle evidence without a complete receipt;
5. operator annotation with author, reason, authority, and supporting references;
6. package-document timestamps (context only; never duration evidence by themselves).

Use commit, PR, completion receipt, telemetry, and validation evidence together when available. Record source-specific timestamp semantics and timezone. Conflicts remain visible; select a value only through a deterministic reliability rule and emit a warning. Missing start/finish boundaries produce partial components or `not_estimable`, not a zero duration. Validation time, review wait, blocked intervals, and merge delay are not active effort unless direct evidence says so.

For multi-commit/multi-PR packages, correlate all accepted attempts and intervals, union overlapping active intervals, and avoid double counting. Interrupted intervals are excluded from active effort only with evidence. Abandoned attempts remain outcomes labeled `abandoned`; blocked work separates blocked wait; reassignment closes the prior attempt and opens a linked attempt. Do not use terminally interrupted/abandoned records as ordinary successful neighbors, but retain them for risk/bound analysis under explicit policy.

## 8. Worker-performance boundaries

Estimate complexity before any worker adjustment. Worker evidence may correlate by authorized pseudonymous identity or worker class and environment; it must not infer personal traits or combine people without authority. Worker-specific adjustment requires at least **5 comparable, completed, validated outcomes** across at least **3 packages**, with usable timestamps and no unresolved evidence conflicts. Below the threshold, use the worker-class baseline and state that no individual adjustment was applied.

Profiles contain only estimation-relevant aggregated evidence, threshold status, version, and source references. No punitive, disciplinary, compensation, hiring, reputational, wellbeing, or public ranking use is permitted. Results must explain that observed duration reflects package, environment, queue, review, integration, and evidence quality—not intrinsic worker worth. Access, retention, pseudonymization, and deletion follow existing Estate authority; the staged implementation must not invent broader identity access.

## 9. Actual outcomes and special cases

An actual outcome records attempt intervals and disposition: completed, interrupted, blocked, abandoned, or reassigned. Completion requires evidence of execution termination; merge, validation, and receipt milestones remain distinct. A package spanning multiple attempts, commits, or PRs receives one package outcome plus linked attempt outcomes. Comparisons may calculate only components supported on both predicted and actual sides and must label censored/partial records.

Queue = eligible/assigned to trustworthy start; active = evidenced execution intervals; review = review-ready to approved/closed review; integration = approval to merge/install checkpoint. Unknown boundaries remain unknown. Overlapping phases must not be summed blindly into wall-clock duration.

## 10. Calibration and estimator lifecycle

For every eligible terminal outcome, append predicted-versus-actual comparisons for active and wall-clock duration and available components. Report small-sample-safe metrics: signed error, absolute error, absolute percentage error only when actual is nonzero, median absolute error, median absolute percentage error where defined, interval coverage, and sample count. Never publish a percentage metric without its denominator and eligibility count.

Estimator behavior and calibration datasets are independently versioned. Trigger recalibration after 10 new eligible outcomes, material median error/coverage drift over a documented window, feature/schema change, worker-class/environment change, or operator-requested investigation. Confidence may improve only when comparable sample count, evidence reliability, recency, and interval coverage meet versioned thresholds; mere passage of time does not improve it.

Retain old versions and replay fixtures/datasets against candidate and incumbent versions. Promotion requires deterministic comparison, documented tradeoffs, approval, and rollback pointer. Rollback changes the active version reference; it never rewrites old estimates or outcomes.

## 11. Runtime/operator contract

Expose only a staged, read-only request/evaluation interface. A request must not claim, assign, enqueue, dispatch, schedule, modify, or cancel work. Results show freshness, evidence cutoff, expiration/staleness policy, explanation, drivers, exclusions, confidence, bounds, and provenance. Diagnostics report version, evidence counts/quality, rejected records, missing fields, calibration status, threshold decisions, and inability-to-estimate reasons without secrets.

An authorized operator may append an override/annotation with author/reference, timestamp, reason, original result, replacement planning value/range, and authority. The estimator must display the annotation separately and never rewrite source evidence, prior results, or calibration truth.

## 12. Integration boundaries

- Consume normalized PL-0014 telemetry when it becomes available, through a documented adapter boundary; do not depend on it for initial operation.
- Bootstrap only from reliable historical repository evidence under Section 7.
- Produce a versioned read-only estimate contract that a future PL-0016 orchestration package may consume.
- Do not call or modify scheduling, dispatch, Alfred, Helen, Open WebUI, Local Compute, Evelyn, workers, or production runtime.
- Do not install readers/writers in shared paths. Integration requires a separate install-handoff package.

## 13. Required staged artifacts

Under `collaboration/workstreams/WP-4214/`, create:

- `README.md` and implementation/authority boundary;
- deterministic estimator library and offline read-only diagnostic entry point;
- schemas for every Section 5 record;
- versioned baseline configuration and evidence reliability policy;
- wholly synthetic fixtures plus bounded repository-evidence fixtures containing references/hashes rather than copied sensitive content;
- unit/integration tests and a no-outside-write test;
- validation report and implementation completion receipt;
- install-handoff requirements document (not an installation package).

## 14. Required tests and validation

Tests must cover:

- deterministic reruns with stable logical output;
- no-history and explicit not-estimable behavior;
- sparse history with widened bounds/low confidence;
- similar completed packages and materially different-package exclusion/down-weighting;
- blocked, interrupted, abandoned, and reassigned executions;
- multi-commit and multi-PR aggregation without double counting;
- inaccurate prior estimates and calibration error reporting;
- missing/inconsistent timestamps and source reliability selection;
- worker-specific adjustment below and above the evidence threshold;
- lower/expected/upper consistency and component/wall-clock rules;
- explanation, freshness, principal drivers, adjustments, and provenance;
- incumbent/candidate estimator-version comparison and rollback pointer;
- explicit checks against fabricated precision;
- schema rejection, deterministic neighbor tie-breaking, no network access, and no writes outside staged/temp paths.

Validation must run all staged tests twice and compare logical outputs, validate all schemas/fixtures, inventory changed paths, scan for secrets/real identities, and confirm production/shared paths are untouched. A validation report must record commands, results, fixture counts, limitations, and estimator/dataset versions.

## 15. Completion and lifecycle gates

WP-4214 implementation is complete only when all staged artifacts exist, required tests pass, validation evidence exists, and a complete implementation receipt identifies commits/PR and known limitations. Even then, nothing is installed.

Only after implementation is merged, required tests pass, validation evidence exists, and the complete implementation receipt exists may an authorized lifecycle update change PL-0015 from `Promoted` to `Closed`. Package authoring alone must not close PL-0015. A separate install-handoff remains mandatory for any production integration.

## 16. Acceptance criteria

1. All Sections 3–12 are represented in versioned staged code/contracts and tests.
2. Deterministic baseline, sparse/no-history behavior, evidence ranking, bounds, explanations, comparisons, and rollback are demonstrated.
3. Worker adjustment respects threshold/privacy rules and remains distinct from complexity.
4. No fabricated precision or unsupported duration is emitted.
5. All changes remain under `collaboration/workstreams/WP-4214/` plus its implementation receipt there.
6. No production/shared runtime or integration file changes.
7. A separate install-handoff package is explicitly required.
8. PL-0015 remains `Promoted` until the lifecycle gates in Section 15 are met.
