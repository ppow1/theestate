# Engineering Department Operational Reality Audit

**Date opened:** 2026-07-30  
**Campaign:** Grace–Engineering Operational Activation  
**Branch:** `recovery/grace-engineering-operational-activation`  
**Status:** VERIFIED GAP — REMEDIATION REQUIRED  
**Audit purpose:** Determine whether Engineering exists as a staffed, reasoning, callable department or whether current behavior consists primarily of governance records, deterministic state transitions, provider adapters, and demonstrations.

---

## 1. Final Audit Verdict

**VERDICT: THE ENGINEERING CONTROL PLANE EXISTS, BUT THE INSTALLED ENGINEERING WORKER IS NOT A REASONING ENGINEERING DEPARTMENT.**

The Estate contains substantial Engineering infrastructure: governance records, Helen-labeled staffing records, Grace objectives, Dispatch transitions, external-runtime invocation, evidence directories, deterministic validation, and closure records.

The live runtime installed at `A:\AI\Tools\EngineeringWorkerRuntime` was inspected through a read-only evidence collection performed on the Steward's dev machine on 2026-07-30. The installed runtime consists of only three files:

1. `runtime_manifest.json`
2. `engineering_worker_runtime.py`
3. `Invoke-EngineeringWorker.ps1`

The Python entrypoint does not call an LLM, planner, provider, Codex, Ollama, Open WebUI, ComfyUI, or any other execution system. It reads a bounded package, creates the requested worktree and evidence directories, and writes a `worker_result.json` declaring `status: completed` with a note that the package was received.

Therefore the currently installed Engineering worker is a **receipt-writing fixture**, not an Engineering reasoning worker and not an execution worker.

---

## 2. Evidence Examined

### 2.1 Repository implementation

Inspected artifacts include:

- `src/estate/core/local_engineering_department.py`
- `src/estate/cli/local_engineering_department.py`
- `src/estate/core/grace_operations_runtime.py`
- `src/estate/core/grace_helen_engineering_composition.py`
- `src/estate/core/helen_workforce.py`
- `src/estate/core/execution_dispatch.py`
- `src/estate/core/execution_adapter_handoff_runtime.py`
- `scripts/Sync-EngineeringWorkerRuntime.ps1`
- `tests/test_local_engineering_department.py`
- `docs/architecture/engineering_department_current_state_map.md`

### 2.2 Live-machine evidence

Evidence collection completed at:

`A:\AI\Reports\EngineeringOperationalEvidence\20260730-095705`

The collector verified:

- Estate root exists: `A:\theestate-wp4233`
- Runtime root exists: `A:\AI\Tools\EngineeringWorkerRuntime`
- Worktree root exists: `A:\AI\EngineeringWorktrees`
- Run root exists: `A:\AI\EngineeringRuns`
- Runtime manifest exists
- Runtime ID is `engineering-worker-runtime`
- Runtime version is `1.0.0`
- Declared entrypoint exists
- Runtime contains three files
- Reasoning/model/provider signal scan returned zero lines
- Eighteen recent Engineering run directories exist
- Eighteen recent Engineering worktree directories exist
- `python`, `py`, `git`, `codex`, and `ollama` are locally available

No collector errors were reported.

---

## 3. Confirmed Findings

### F-001 — Engineering infrastructure exists

**Status:** VERIFIED

The repository contains real Python for governance records, Dispatch handoff, external-runtime invocation, validation reports, evidence hashing, and closure records.

### F-002 — The local Engineering loop is a bounded demonstration

**Status:** VERIFIED

The principal closed-loop method is hard-coded to CAMPAIGN_0550/WP-0552 and a fixed worker identity. The repository's own current-state map classifies it as active but partial.

### F-003 — Staffing is deterministic record construction in the inspected path

**Status:** VERIFIED

The same Python path creates the staffing request and a favorable Helen assessment for `local-engineering-worker-001`. No independent worker discovery, model identity verification, availability check, or qualification reasoning was observed.

### F-004 — The installed worker does not reason

**Status:** VERIFIED

The installed `engineering_worker_runtime.py`:

- parses `--package`, `--worktree`, and `--evidence`;
- reads the package JSON;
- creates directories;
- writes `worker_result.json`;
- exits successfully.

It contains no planning loop, prompt construction, model invocation, tool invocation, provider selection, execution adapter call, artifact inspection, retry logic, or completion judgment.

### F-005 — Existing runs record receipt, not completed Engineering work

**Status:** VERIFIED

Recent `worker_result.json` files repeatedly report:

- `status: completed`
- the package and dispatch IDs
- the worktree and evidence paths
- a note that the external runtime received a bounded package

These files do not contain implementation results, generated artifacts, provider execution receipts, technical decisions, or Engineering validation evidence.

### F-006 — Independent validation is not validating the dispatched work product

**Status:** VERIFIED

The collected `independent_validation.json` files contain broad repository production-readiness blockers such as missing completion artifacts for unrelated work packages. They do not demonstrate validation of the specific dispatched Engineering output.

### F-007 — Provider choice is not proven to belong to Engineering

**Status:** VERIFIED

The inspected tests and Dispatch paths can receive a preselected provider, but the installed worker does not compare or select providers.

### F-008 — The local machine already has candidate execution providers

**Status:** VERIFIED

The collector found `codex` and `ollama` available as shell commands. The immediate gap is not absence of all providers; it is the absence of an Engineering reasoning and execution layer that can select and operate them under Estate governance.

---

## 4. Capability Matrix

| Capability | Current classification | Confidence |
|---|---|---:|
| Governance records | OPERATIONAL | High |
| Grace objective creation | OPERATIONAL, PARTIAL | High |
| Helen staffing record creation | OPERATIONAL AS RECORDING; INDEPENDENT ASSESSMENT ABSENT IN THIS PATH | High |
| Dispatch queue and handoff | OPERATIONAL | High |
| External worker adapter | OPERATIONAL | High |
| Live external worker installation | PRESENT | High |
| Live external worker reasoning | ABSENT | High |
| Live external worker provider execution | ABSENT | High |
| General commission intake | PARTIAL | High |
| Technical planning | ABSENT IN INSTALLED WORKER | High |
| Provider comparison/selection | ABSENT IN INSTALLED WORKER | High |
| Artifact inspection by Engineering | ABSENT IN INSTALLED WORKER | High |
| Retry/reject/approve judgment | ABSENT IN INSTALLED WORKER | High |
| Deterministic repository validation reports | OPERATIONAL | High |
| Dispatched-work-product validation | NOT DEMONSTRATED | High |
| Institutional Engineering completion judgment | ABSENT | High |
| Chief Architect/Steward acceptance boundary | PRESERVED IN INSPECTED PATH | High |

---

## 5. Operational Consequence

The Estate currently permits a false-positive completion sequence:

1. A bounded package is dispatched.
2. The external runtime receives it.
3. The runtime writes `status: completed` without performing Engineering work.
4. A broad repository validation report is generated.
5. Grace/Dispatch records can advance based on runtime process completion rather than verified work-product completion.

This explains why the system can appear institutionally complete while failing to commission Engineering to produce a bicycle image or any other substantive result.

The word `completed` currently means **the receipt-writing subprocess exited successfully**, not **Engineering completed and validated the commission**.

---

## 6. Required Remediation

### P1-A — Replace the receipt fixture with a Minimum Viable Engineering Worker

The next implementation must provide, at minimum:

1. **Commission interpretation**
   - Read objective, constraints, acceptance criteria, authority boundaries, and evidence requirements.

2. **Planning**
   - Produce a durable execution plan before provider invocation.

3. **Provider selection**
   - Inspect registered provider capabilities.
   - Select a provider based on the commission rather than receiving an unexplained preselection.

4. **Provider execution**
   - Invoke the selected adapter or provider.
   - Preserve raw provider receipts and produced artifacts.

5. **Work-product validation**
   - Validate the artifact against commission-specific acceptance criteria.
   - Do not substitute repository-wide readiness checks for work-product validation.

6. **Retry and escalation**
   - Retry within policy.
   - Escalate blocked work with evidence.

7. **Truthful status semantics**
   - `received`: package accepted by worker.
   - `planned`: durable plan exists.
   - `executing`: provider invocation underway.
   - `validation_required`: artifact exists and awaits validation.
   - `completed`: required artifact exists and commission-specific validation passed.
   - `blocked` or `failed`: work did not complete.

### P1-B — Separate process success from commission success

The adapter must not translate subprocess exit code zero into Engineering completion. A zero exit code may establish only that the worker process returned normally. Commission completion must require a schema-valid result declaring produced artifacts, provider receipts, and validation evidence.

### P1-C — Establish a first institutional acceptance test

The first acceptance test remains:

**Grace commissions Engineering to produce a validated bicycle image.**

The test passes only when:

- Grace creates the objective without selecting the execution provider;
- Helen verifies or assigns an Engineering worker;
- Engineering plans the work;
- Engineering selects an image-capable provider;
- the provider produces the bicycle image;
- Engineering validates the returned artifact against explicit criteria;
- Grace receives a truthful completion report;
- the Steward retains final acceptance authority.

---

## 7. Campaign Dashboard Update

| Workstream | Status | Evidence-based note |
|---|---|---|
| Grace Operational Recovery | INVESTIGATING | Grace can create records, but completion semantics depend on a non-functional worker. |
| Engineering Reality Audit | VERIFIED | Control plane exists; reasoning/execution worker is absent. |
| Engineering Department Stand-Up | IN PROGRESS | Minimum viable worker is now the next required implementation. |
| End-to-End Bicycle Commission | BLOCKED | Blocked by absence of Engineering reasoning/provider execution. |
| CME Operational Progression | NOT STARTED | Deferred until a truthful Engineering lifecycle exists. |
| Grace Runtime Composition | NOT STARTED | Deferred behind operational commissioning recovery. |
| Resident Lifecycle Framework | NOT STARTED | Engineering lifecycle will provide the first concrete implementation pattern. |

---

## 8. Current Next Action

Author the Minimum Viable Engineering Worker implementation package that replaces the receipt-writing fixture with a governed planning, provider-selection, execution, evidence, and commission-specific validation loop.

The package must preserve existing authority boundaries and must not make Grace provider-aware.