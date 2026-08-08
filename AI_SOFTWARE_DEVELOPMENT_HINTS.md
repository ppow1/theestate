# AI_SOFTWARE_DEVELOPMENT_HINTS.md

Status: Canonical minimum engineering contract for Estate software work.

## 1. Purpose

If you are creating, modifying, repairing, integrating, testing, deploying, or promoting software for The Estate, read this document completely before writing code.

You may already know how to write software. This document defines how software must be engineered for The Estate.

A work package may impose stricter or additional requirements. It does not silently remove these minimum requirements.

The contract is provider-neutral. It applies to cloud Codex, ChatGPT, local AI workers, future providers, automation, and human developers.

## 2. First Principle: Understand Before Adding

Before creating a new subsystem, registry, scheduler, database, service, daemon, protocol, or institutional mechanism:

1. inspect the existing architecture;
2. determine whether an existing subsystem already owns the responsibility;
3. extend the existing owner when practical;
4. introduce a new mechanism only when the existing Estate cannot responsibly absorb the requirement.

Do not redesign the Estate because context is incomplete. Do not create parallel infrastructure merely because it is easier to understand in isolation.

## 3. Environment Identity and Development Boundary

Before implementation begins, establish which environment is being changed or tested. Do not infer environment identity from memory or an incidental path.

The intended Estate development doctrine is described in `collaboration/workstreams/WIP_Estate_Development_Architecture.md`: the Live Estate is the institutional runtime, not the normal experimental workspace; development and acceptance prepare candidates for explicit promotion.

### Normal lifecycle

The target engineering lifecycle is:

```text
Blue / Development Candidate
        |
        v
Green / Acceptance Candidate
        |
        v
Authorized Promotion
        |
        v
Live Estate
        |
        v
Archive / Rollback Provenance
```

Names may differ for a subsystem, but the responsibilities must remain explicit: candidate development, acceptance, promotion, Live operation, and preservation of superseded state.

### Current transitional exception

The Estate is undergoing active stabilization and some presently authorized work is occurring directly against Live or other non-ideal boundaries to obtain necessary operational results. Do not mistake this temporary practice for the desired permanent engineering doctrine.

A direct-Live change must be treated as an exception. Record why the normal candidate/acceptance path was not used, minimize the mutation, preserve rollback/provenance information, and validate the resulting Live state. Do not expand a direct-Live repair into unrelated development.

Do not stop an explicitly authorized urgent task merely to retrofit the entire Blue/Green/Live architecture. Improve adoption incrementally as systems are naturally touched.

## 4. Blue, Green, Live, and Archive Responsibilities

### Blue / Development

Use Blue or the designated Development environment for implementation, experimentation, repair development, and destructive/adversarial testing where practical. It must not silently share mutable Live state.

### Green / Acceptance

Green or the designated Acceptance environment exists to answer whether the exact candidate is fit to promote. Acceptance must exercise the real integration boundary required by the capability, not merely unit-test an approximation.

### Live

Live is the institutional runtime. Normal engineering work reaches Live only through explicit promotion. After promotion, validate the actual Live behavior; candidate success is not proof of Live success.

### Archive / rollback provenance

Preserve enough information to identify what Live state was replaced, what exact candidate was promoted, the evidence supporting promotion, and how the prior state can be recovered when rollback is required. Archive is historical/provenance material, not another writable source of truth.

## 5. Revision and Implementation Provenance

Every governed source/configuration/documentation artifact created or modified by software work must participate in the Estate's implementation provenance system.

Do not invent semantic versions merely to satisfy a version field. The universal revision identity is the canonical repository path plus immutable content identity and Git/repository context. Semantic versions are appropriate only where they communicate genuine compatibility or interface meaning.

Dirty and untracked working revisions must remain distinguishable from committed repository revisions. Repository provenance must not be misrepresented as installed/running provenance.

Where Living Diagnostics is available, its implementation manifest and accepted-baseline lifecycle are the governing mechanisms for deterministic revision/staleness assessment.

## 6. Diagnostics Are a Development Deliverable

The worker who writes a change is responsible for producing the first diagnostic description of that change while its intent is still known.

The author does not automatically own final canonical troubleshooting truth. The author owns high-quality candidate diagnostic metadata.

For a material code change, record at minimum:

- files/artifacts changed;
- subsystem/component ownership;
- important dependencies consumed or changed;
- intended behavior and invariants;
- expected inputs and outputs where meaningful;
- known or plausible failure seams discovered during implementation;
- the narrowest useful probes/tests;
- evidence locations and acceptance results;
- restart/reload/reconciliation boundaries where relevant;
- existing troubleshooting checkpoints affected;
- proposed new checkpoint/failure knowledge where an existing entry cannot absorb the change.

Use the canonical Diagnostic Impact Packet contract when available. Do not silently change implementation and leave Living Diagnostics to reverse-engineer intent later.

Candidate diagnostic knowledge is not automatically canonical knowledge. Reconciliation, validation, and acceptance decide promotion into the Troubleshooting Cookbook.

## 7. The Development-to-Diagnostics Loop

Estate software development should increasingly follow this loop:

```text
Requirement / Work Package
        |
        v
Implementation
        |
        v
First-pass diagnostic metadata
        |
        v
Focused tests and evidence
        |
        v
Candidate / acceptance / promotion
        |
        v
Living Diagnostics reconciliation
        |
        v
Local-AI bounded interpretation where useful
        |
        v
Validated canonical troubleshooting knowledge
        |
        +-------------------------------> future development
```

This prevents the Troubleshooting Cookbook from becoming detached prose that slowly diverges from the implementation.

## 8. Local AI Is the Preferred Bulk Interpretation Resource

Do not default large repository-wide diagnostic interpretation or cookbook population work to scarce cloud-provider quota.

Deterministic Stage 1 work must remain provider-independent wherever practical: manifesting, hashing, Git/revision comparison, dependency/change detection, schema validation, checkpoint applicability, staleness classification, and candidate packet ingestion.

Large-volume review of changed artifacts, candidate diagnostic packets, test evidence, and existing cookbook coverage is a strong candidate for Estate-controlled local AI, including unattended/off-hours execution when authorized.

Local AI may propose, classify, summarize, or identify gaps. It does not silently promote candidate knowledge to canonical truth, alter accepted baselines, or authorize remediation merely because it has processed the repository.

Escalate only the bounded cases that genuinely require stronger reasoning, external capability, Steward judgment, or another authorized provider.

## 9. Observer Effect and Process-Sensitive Testing

Testing can change the thing being tested. The Estate has demonstrated process-sensitive observer effects around ownership, PIDs, locks, leases, workers, browser processes, provider processes, and lifecycle/concurrency behavior.

Before declaring a process-sensitive test authoritative, ask:

> Can the observer, test runner, shell, parent process, inspection method, or cleanup path alter the ownership/lifecycle state being measured?

If yes or uncertain, use the established detached/isolation boundary or an equivalent validated mechanism. Persist evidence outside the observed process and reconcile ownership afterward.

A failure caused by the observer is not proof that the subject failed. A passing in-process test is not sufficient proof when the production behavior depends on process boundaries.

Process-sensitive acceptance should, as applicable, prove:

- controller/worker ownership is correctly distinguished;
- locks and leases have the intended owner;
- duplicate activation is inert or rejected as designed;
- stale/crashed ownership is recovered without clearing unrelated work;
- child processes terminate or remain alive exactly as intended;
- final locks, leases, reservations, processes, and worktrees reconcile;
- evidence survives the process boundary required to diagnose failure.

## 10. Testing Must Match the Real Boundary

Use unit and synthetic tests for fast deterministic coverage, but do not substitute them for integration acceptance when the behavior depends on a real boundary.

Examples include browser UI behavior, persistent authentication, provider invocation, database/runtime selection, process ownership, concurrency, filesystem/worktree isolation, and promotion into Live.

Compile/static checks prove syntax and structure. Unit tests prove bounded behavior. Detached/process tests prove lifecycle behavior. Browser tests prove actual operator-visible UI behavior. Live acceptance proves Live behavior. Do not claim one from evidence belonging only to another layer.

## 11. Browser-Integrated Testing: Incoming Capability

The Estate is actively proving browser-operated acceptance through Playwright-style automation. A generalized browser operator is a future/incoming engineering capability, not yet universal infrastructure.

Until it is formally accepted, do not assume every task can invoke it. Where a validated subsystem-specific browser harness already exists, use it when the work package requires that real UI boundary.

The intended future capability is a reusable browser operator with environment/payload-specific overlays so authorized workers can navigate real interfaces, click controls, enter natural-language interactions, observe asynchronous state, correlate UI actions with Estate roots/evidence, and capture sanitized screenshots/traces/console/network evidence.

Likely uses include Open WebUI/Grace acceptance and the Office of the Steward. Future availability must not be interpreted as permission to automate third-party services contrary to their rules or without authorization.

When this capability becomes canonical, move it from "incoming" guidance into the normal testing contract rather than maintaining two conflicting standards.

## 12. Git, History, and Publication

Treat repairs as new Estate changes. Preserve history; do not rewrite accepted institutional history merely to make the current state look cleaner.

Before modification, identify the branch/worktree and unrelated dirty state. Do not discard unrelated work. Use isolated worktrees when concurrent repository mutation or acceptance requires them.

For cloud task environments, a local commit is not durable Estate publication. When the task is expected to produce repository work, publish through the supported GitHub/Codex mechanism and verify the remote state before dependent work assumes the commit exists. Do not leave valuable accepted implementation stranded in an ephemeral task environment.

Do not force-push, squash away required accepted history, create a competing PR, or merge unless the work package/Steward authorization permits it.

## 13. Generated Output, Runtime State, Databases, and Secrets

Know what category each artifact belongs to before committing it.

Do not commit credentials, tokens, cookies, private keys, authentication profiles, secret-bearing traces, or runtime databases unless an explicit governed design requires a safe non-secret fixture.

Generated artifacts should be reproducible from canonical source where practical and should not become an accidental second source of truth.

Runtime evidence belongs in the established evidence/runtime locations and should be sanitized where required. Development and acceptance must not silently point at Live databases, caches, credentials, or mutable runtime state.

## 14. Minimum Completion Deliverables

Unless a work package explicitly establishes a stricter standard, a software-changing task should close with:

1. implementation scoped to the authorized responsibility;
2. exact changed-file/revision provenance;
3. focused tests appropriate to the change;
4. real-boundary acceptance where the behavior requires it;
5. first-pass diagnostic impact metadata;
6. affected/new Troubleshooting Cookbook candidate knowledge where applicable;
7. documentation/runbook updates required to operate the change;
8. evidence of failures as well as successes when those failures materially informed the repair;
9. explicit environment/promotion state: Development/Blue, Acceptance/Green, Live, or authorized exception;
10. final process/lock/lease/worktree reconciliation when process-sensitive behavior was exercised;
11. preserved unrelated repository state;
12. remote publication status when repository publication is part of the task;
13. truthful blockers and unproven boundaries rather than an unsupported readiness token.

## 15. Work-Package Inheritance

Future Estate software work packages should normally contain a short required-reading instruction rather than restating this contract:

> Read `AI_HINTS.md` and `AI_SOFTWARE_DEVELOPMENT_HINTS.md` completely before implementation. Their software-development requirements are inherited by this work package unless this package explicitly imposes a stricter requirement.

A work package may then focus on the unique requirements, acceptance criteria, and authorization boundaries of its subsystem.

## 16. Relationship to the Troubleshooting Cookbook

The Troubleshooting Cookbook is a living operational knowledge system, not a substitute for engineering evidence and not an excuse to freeze implementation.

Code changes can invalidate diagnostic knowledge. Missing or invalid diagnostic impact metadata should fail conservatively toward revalidation rather than preserving false certainty.

The desired responsibility split is:

- developer/implementing worker: first-pass diagnostic intent and evidence;
- deterministic Living Diagnostics: revision/change/staleness truth;
- local AI or other capability-routed interpretation: bounded candidate analysis;
- validation/acceptance: evidence that the guidance still applies;
- canonical cookbook: accepted operational knowledge;
- Grace/other residents: consumers of that knowledge according to their authority.

## 17. Final Engineering Principle

Build the smallest correct change inside the existing Estate architecture. Know exactly which revision and environment you changed. Leave evidence that another worker can verify. Teach Living Diagnostics what changed while you still understand it. Test through the boundary that actually matters. Promote deliberately when the Estate's candidate/acceptance path is available, document authorized exceptions when it is not, and preserve enough provenance to recover safely.
