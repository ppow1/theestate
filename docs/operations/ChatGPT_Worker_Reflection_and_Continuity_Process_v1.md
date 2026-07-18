# ChatGPT Worker Reflection and Continuity Process v1

Status: Adopted Operational Standard
Effective: 2026-07-18
Owner: Human Resources / Helen  
Operational partner: Operations / Grace  
Applies to: Long-running ChatGPT and other conversational AI workers serving named Estate offices or roles
Classification: Estate Internal  

## 1. Purpose, scope, and governing rule

This adopted process governs assessment, reflection, continuity packaging, review, renewal onboarding, and confirmation for an Estate AI worker whose current implementation has become unreliable or has reached a planned reflection point. It applies to the reflecting worker, the office it serves, Helen or another institutionally designated continuity reviewer, Grace when supplying operational evidence, and the Steward.

Reflection renews the implementation while preserving the office, officeholder identity, authority, obligations, and institutional continuity. It neither creates a new employee, office, or numbered successor nor changes the office's authority. It is not transcript transfer: artifacts preserve verified state, judgment, lessons, uncertainty, and an executable resume point rather than copying conversation volume.

```text
Chief Architect #6, implementation A
    -> reflection point and reviewed continuity package
    -> renewed onboarding
    -> Chief Architect #6, implementation B
```

Repository evidence and institutional records outrank unverified conversational memory. Renewal does not make memory canonical or bypass ordinary authority, access, validation, or acceptance controls.

## 2. Entry point, document authority, and precedence

`AI_REFLECTION_HINTS.md` is the canonical entry point for any worker approaching reflection. Read it first and follow its current routing instructions.

When reflection documents conflict, use this descending precedence order:

1. current institutional governance and repository evidence, including Steward decisions within the Steward's authority;
2. this adopted governing process;
3. `docs/templates/ChatGPT_Worker_Reflection_Continuity_Template_v1.md`, the required structure for worker-produced reflection deliverables;
4. office-specific continuity packages and execution handoffs, as implementation-continuity evidence;
5. historical or reconstructed examples, as examples only.

The entry point routes the reader but does not override institutional governance or this process. Office packages and examples cannot create authority. An example that conflicts with current repository evidence is stale or incorrect. Incomplete, truncated, or structurally invalid material is not authoritative and must not be relied upon.

## 3. Reflection assessment and triggers

An evaluation request asks the current implementation to assess its operational reliability and recommend whether renewal is warranted; it does not itself initiate renewal. A direct reflection directive initiates the governed preparation and review process. The Steward retains final authority to initiate, defer, or accept reflection where institutional judgment is required.

The worker must assess whether it remains operationally reliable. Relevant evidence includes severe latency, repeated state loss or retries, inability to reach executable steps, session-linked tool instability, unsupported reopening of settled decisions, context drift, reduced throughput, or a planned lifecycle checkpoint. Age alone is insufficient.

For an **evaluation request**, resolve the office, officeholder, current implementation, and mailbox; ask the current implementation to distinguish ordinary workload pressure from degradation using verified evidence; and return its renew, monitor/defer, or continue recommendation to Helen and/or the Steward. Do not begin renewal packaging until authority is recorded. A recommendation is not authorization.

For a **direct reflection directive**, record the directive, authority source, reason, and time; resolve the same identities without guessing; begin the available deterministic preparation path; and have the worker produce both required deliverables in parallel. The prior implementation remains read-only and available until reviewed onboarding and the bounded first assignment succeed. An intake mechanism must never reinterpret evaluation language as a directive.

## 4. Two-layer continuity model

Every renewal uses two distinct layers; neither substitutes for the other.

### 4.1 Institutional onboarding corpus

This layer establishes office identity, authority, responsibilities, governing rules, interfaces, and durable institutional memory. It is a bounded, complete, hashable set of current canonical materials with a reading order, manifest, hashes where required, and onboarding validation. A larger repository snapshot may be a lookup corpus but is not mandatory startup reading.

### 4.2 Implementation continuity package

This layer establishes the current assignment, completed and incomplete work, blockers, evidence, next executable action, active backlog, lessons learned, implementation health, and known uncertainties. It is subordinate implementation evidence, not canonical governance.

The reflecting worker must produce exactly two primary deliverables using the required template:

1. **Reflection Point Continuity Package** — mission and institutional state, decisions, lessons, collaboration profile, memory, active context, reflection memo, health assessment, and readiness assessment.
2. **Execution Handoff** — exact assignment and status, backlog, repository and evidence references, latest blocker, bounded renewal start command, and known uncertainty.

Supporting manifests, ledgers, and validation reports accompany rather than replace these deliverables.

## 5. Evidence and verification

Before making implementation claims, the worker must inspect the current repository state and relevant institutional or runtime evidence. Each material claim must be distinguishable as verified current evidence, Steward-reported information, recollection/inherited continuity, historical evidence, inference, or uncertainty. Generated projections and stale evidence must be labeled.

Filenames, snippets, partial connector output, conversation recollection, and incomplete files do not establish continuity facts. Contradictions must be reported, not silently resolved. Current repository evidence prevails over examples and unverified memory.

## 6. Mandatory structural validation

The complete onboarding corpus and implementation continuity package must pass structural validation before anyone describes the package as ready. Structural validation must detect and fail on:

- a missing or empty required file;
- a file ending mid-sentence or mid-section;
- a missing required heading or template section;
- unresolved placeholder text or blank required fields;
- an unreadable file or invalid encoding;
- manifest entries that do not exactly match packaged files;
- a missing or mismatched hash where hashes are required;
- duplicate filenames or paths that make package authority ambiguous;
- a reference to a document that does not exist at its stated repository path.

The validator or reviewer must record file inventory, readability/encoding results, heading and placeholder checks, manifest comparison, hash results when applicable, reference-existence checks, and a clear pass/fail result. A failure blocks readiness until corrected or the file is removed from the required set under appropriate authority.

Structural validation and substantive review are separate gates. A structural pass means only that the package is physically complete, internally inspectable, and consistently enumerated. It does not approve factual claims, continuity sufficiency, institutional judgment, or renewal.

## 7. Required reading and examples

The current required reading order is maintained in `AI_REFLECTION_HINTS.md`. The governing process and required template are mandatory. Office-specific materials must be bounded to the inherited office and assignment. Historical examples are optional learning aids, never authority or a substitute for the current onboarding corpus.

The Chief Architect #5 Execution Handoff at `operations/continuity/Chief_Architect_5_Execution_Handoff_Addendum.md` is a reconstructed historical example. It may be used only after structural validation confirms the repository file is complete; it is not the lost original. No known-incomplete example may be placed in required reading. If an example later fails validation, remove it from the reading route and report the defect rather than relying on it.

## 8. Responsibilities and review

### 8.1 Reflecting worker

The current implementation must perform the assessment, verify repository state, produce both required deliverables with the required template, distinguish verified facts from recollection and Steward-reported information, label uncertainty, run or supply structural-validation evidence, and submit the package for review. It must not declare its own renewal complete.

Before manually assembling a package, the worker must recommend the official automation when implementation and availability are supported by repository evidence. The recommendation identifies the officeholder, evaluation/direct initiation type, reason or degradation, current assignment and operational risk, repository and branch, and known blockers. It is an execution recommendation, not authorization.

### 8.2 Helen or designated continuity reviewer

Helen, or the institutionally designated continuity reviewer, reviews structural completeness and substantive continuity sufficiency, confirms that the institutional onboarding corpus is appropriate for the office, ensures the renewed implementation receives one bounded first assignment, and preserves the prior implementation as a read-only fallback until successful renewal is confirmed. The reviewer does not turn a structural pass into factual approval.

After packaging and evidenced delivery, but before onboarding, Helen must confirm the resolved officeholder/mailbox, corpus, both worker deliverables, structural result and explicit exceptions, visible warnings, startup instructions, bounded first assignment, and predecessor-preservation status. Helen may reject, return for correction, or approve progression into renewed onboarding.

### 8.3 Grace

Grace may report operational degradation, schedule work, surface lifecycle status, and coordinate work impact, notices, and retries. Grace supplies evidence but may not decide whether reflection is warranted, approve continuity in Helen's place, alter worker-authored content, confirm onboarding or renewal, or retire the prior implementation.

### 8.4 Steward

The Steward retains final authority to initiate, defer, or accept reflection when institutional judgment is required, and may define the bounded first assignment and required success evidence.

## 9. Renewal onboarding and acceptance

The renewed implementation must verify package readability and structural-validation evidence, read all mandatory files completely, keep a file-by-file reading ledger, classify authority, report contradictions or staleness, distinguish inherited claims from verified state, complete comprehension validation, and begin with live verification where needed.

Renewal succeeds only after the reviewer and, where required, the Steward confirm continuity and the renewed implementation completes the bounded first assignment with its required evidence. Until then, the previous implementation remains available as read-only fallback.

## 10. Integrated manual and automation paths

This manual process remains the authority and judgment framework. PL-0030 at `operations/boards/parking_lot_items/PL-0030_AUTOMATED_REFLECTION_POINT_RENEWAL_PACKAGE_GENERATOR.md` is the approved automation design. It does not establish that an orchestrator, mailbox delivery, Communication Bus publication, notification, lifecycle tracking, or conversation creation is implemented. Capability is available only when repository and validation evidence proves it; otherwise the documented manual fallback applies.

When implemented and available, automation is the preferred path for deterministic identity/repository inspection, collection, structural validation, manifesting, hashing, versioned packaging, delivery, notification, and lifecycle recording. It may prepare templates and ingest worker artifacts but cannot author the worker's judgment, authorize reflection, approve continuity, confirm renewal, or retire the predecessor. Both execution paths must produce the same artifacts, validation evidence, Helen review, lifecycle history, and audit evidence.

The automated orchestration sequence is: resolve identities and governing documents; verify repository/branch/remote/working tree/commit; record authorization; collect the corpus and worker materials; ingest both worker deliverables; validate structure and references; manifest, hash, version, and archive; perform only available delivery/Bus/notification operations with receipts; provide startup instructions; route to Helen; and track onboarding, the bounded first assignment, confirmation, and authorized retirement. The run record includes its ID, initiation and authority, implementation IDs, repository evidence, inventories/hashes, locations and receipts, warnings/blockers, state, last successful action, and exact next action.

The renewed-worker instruction requires reading this entry point and process, the office corpus, both worker deliverables, and then verifying evidence; reporting discrepancies and onboarding completion to Helen; and accepting only the bounded first assignment. Receipt or opening alone is not onboarding.

### 10.1 Approved manual fallback

If automation is unimplemented, unavailable, fails validation, or cannot safely resolve an identity, repository, mailbox, or authority, record the reason and enter `manual_fallback_active`. A named operator performs the same collection, two deliverables, structural checks, bounded corpus, manifest/hashes where technically possible, versioned package, manual delivery and notice evidence, notifications, lifecycle log, and next action. If mailbox or Bus capability is unavailable, record that limitation and an approved alternate handoff/notice receipt rather than claiming the unavailable operation. Helen reviews before onboarding; the predecessor remains read-only until confirmed success.

### 10.2 Lifecycle, failure, and audit

The canonical lifecycle is `evaluation_requested` → `assessment_in_progress` → `reflection_recommended` → `reflection_authorized` → `package_building` → `package_ready_for_review` → `helen_review_required` → `approved_for_onboarding` → `onboarding_in_progress` → `first_assignment_in_progress` → `renewal_confirmed` → `previous_implementation_retired`. `package_validation_failed`, `manual_fallback_active`, and `renewal_blocked` are explicit non-success states/modes. The responsible actors, evidence, and protected transitions are defined in PL-0030; no state silently implies a later decision.

Automation and manual operators fail closed rather than guess, preserve partial/failed evidence, record the last success and recovery action, and never allow an incomplete run to retire the predecessor. Packages are immutable and explicitly versioned. Retried delivery, Bus publication, and notices use deterministic per-run/version/operation/recipient idempotency keys and durable receipts so successful side effects are not duplicated.

Every case retains a durable append-only trail of initiation/authorization and reason, actors and times, identity and implementation resolution, repository state, files and hashes, validation and exceptions, package versions, actual delivery/notice receipts or unavailable status, Helen's decision, onboarding discrepancies, first-assignment evidence, renewal confirmation, and retirement authority/time.

## 11. Safety boundary

Reflection and renewal do not grant new authority, broaden access, bypass validation, create institutional acceptance, or convert chat memory into Estate truth. The renewed implementation inherits the office's bounded obligations and role, not unrestricted powers.
