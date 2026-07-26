# Local Compute Campaign Runtime — Work in Progress

**Status:** IN PROCESS  
**Started:** 2026-07-26  
**Current phase:** Concept clarification and canonical-integration discovery  
**Execution state:** Deliberately paused after kickoff; no implementation authorized yet

## 1. Why this workstream exists

The immediate need arose from Evelyn canon-development campaigns that can occupy the local RTX 4090 for long unattended runs. The Steward needs a durable way to see pending campaigns, start them manually or during safe idle windows, preserve progress, verify outputs, and avoid wasting available local compute capacity.

The discussion established that this should not remain an Evelyn-only checklist. It may become a reusable local execution capability for image generation, model benchmarking, LoRA training, transcription, text-to-speech, video processing, dataset preparation, and other bounded local workloads.

At the same time, this capability must not become a parallel miniature Estate with its own institutional scheduler, approval system, provider registry, validation authority, or acceptance process.

## 2. Current working concept

The proposed capability is a **Local Compute Campaign Runtime**: a local, API-addressable execution service that accepts bounded work, checks prerequisites and local resource availability, runs workload adapters, preserves resumable state, verifies expected artifacts, and returns machine-readable evidence.

Evelyn canon generation is the first workload family and proving use case, not the platform identity.

The local runtime would eventually support adapters such as:

- ComfyUI batch image generation and editing;
- LoRA or other training runs;
- local model evaluation and benchmarking;
- faster-whisper transcription;
- text-to-speech generation;
- FFmpeg and video-processing campaigns;
- dataset preparation and indexing;
- future Engineering workloads with bounded inputs and measurable outputs.

## 3. Estate placement

The intended relationship is:

```text
Steward / Chief Architect
        ↓
approved intent, authority and priority
        ↓
PTM / Estate Orchestrator
        ↓
readiness, dependency and Estate-level scheduling
        ↓
Execution Dispatch
        ↓
provider selection and authorized handoff
        ↓
Local Compute Campaign Runtime
        ↓
ComfyUI / GPU / scripts / models / local tools
        ↓
artifacts, execution evidence and validation inputs
```

The Local Compute Campaign Runtime is therefore an execution provider and provider-local workload manager. It does not decide institutional priority or acceptance.

## 4. Roles and actor integration

### Steward

The Steward retains authority over priority, exceptions, safety decisions and institutional direction. The system should reduce routine manual launching without obscuring or replacing Steward authority.

### Chief Architect

The Chief Architect reviews architecture and cross-system integration and retains the applicable Engineering acceptance role. A successful run or passing artifact verification is not architectural or institutional acceptance.

### Grace — acting Engineering manager

Grace must be able to:

- see workload readiness, progress, blockers and completion evidence;
- request or advance properly authorized Dispatch work;
- call the runtime through the existing Dispatch/provider boundary when execution is eligible;
- coordinate retries, checkpoints, interruption and escalation within delegated authority;
- avoid gaining architecture approval, merge authority or self-acceptance authority.

Grace should not operate a separate private queue inside this runtime. Her actions must remain linked to canonical campaign, work-package and Dispatch identities.

### Helen / HR

Helen and HR must be able to inspect the capability from the staffing and qualification perspective, including:

- which human or AI roles are required for a workload family;
- what qualifications or local-tool access are required;
- which actor initiated, supervised or reviewed an execution attempt;
- whether a proposed assignment exceeds an actor’s role or qualification;
- workforce and onboarding implications as the capability expands.

The runtime must not create a second personnel registry or hiring workflow.

### Alfred

Alfred may expose summaries, reminders, notices, duty awareness and operator attention requirements. Alfred should consume structured events and canonical references rather than becoming the campaign state store or execution authority.

### Estate Orchestrator / PTM

These remain the governed seams for approved intake, dependencies, readiness and Estate-level scheduling. The runtime may report local eligibility and capacity but must not replace them.

### Execution Dispatch and provider adapters

Estate-managed work should enter through the canonical provider-neutral Dispatch and adapter boundary. The runtime API is the local execution endpoint beneath that boundary.

### Validation and review systems

The runtime verifies that expected local artifacts and ledgers exist and are internally consistent. Canonical Estate validation, reconciliation, review and acceptance remain external.

## 5. Local operator surface

A local client or browser dashboard remains useful, but it is an operator console rather than the Estate source of truth.

Expected operator functions include:

- campaign and workload list;
- pending, in-process, blocked and locally completed views;
- persistent state across restarts;
- copyable manual launch commands;
- scheduled execution windows;
- idle-GPU and ComfyUI availability checks;
- two-minute warning with cancel or postpone controls;
- stop-after-current-job and emergency-stop controls;
- output-folder, manifest and ledger inspection;
- failure and retry visibility;
- notes and local experimental workloads.

The client should obtain state from the runtime API instead of duplicating the service’s internal state.

## 6. Scheduling boundary

Two scheduling concepts must remain distinct.

### Estate-level scheduling

Determines which approved assignment is next, its priority, dependencies, earliest start, deadline and authority basis. This belongs to PTM/orchestrator and related canonical systems.

### Provider-local execution timing

Determines when an already authorized workload can safely run on this workstation. It may consider:

- GPU utilization and VRAM use;
- ComfyUI queue depth;
- active runner processes;
- user activity and optional system-idle duration;
- execution window and latest permitted stop time;
- disk capacity;
- required source files and scripts;
- operator cancellation or a temporary do-not-run switch.

A local 2:00 AM countdown and automatic launch is provider-local admission control, not a second Estate scheduler, provided the work has already been authorized or is explicitly a local Steward-run experiment.

## 7. API direction

The runtime should be API-first so that the local dashboard, Grace, Alfred, Helen-facing views and future Estate integrations can use structured interfaces.

Likely runtime surfaces include:

- health, capabilities and current capacity;
- workload-adapter catalog;
- execution-attempt admission;
- attempt status and progress;
- pause, resume, stop-after-current and emergency termination;
- local schedule-window and countdown state;
- artifacts, ledgers, failures and verification evidence;
- event stream for progress, attention and completion;
- audit records identifying actor, authority basis and request identity.

Estate-managed requests should normally reach these hooks through Dispatch/provider adapters rather than bypassing canonical routing.

## 8. State and evidence principles

- Preserve campaign ID, work-package ID, Dispatch ID and execution-attempt ID where applicable.
- Treat every retry or resumed run as an identifiable attempt linked to its predecessor.
- Store durable local state and append-only audit events.
- Persist progress frequently enough to survive reboot or interruption.
- Verify output presence, manifests, ledgers, failed jobs, skipped jobs and empty or missing files.
- Report local execution completion separately from Estate validation and institutional acceptance.
- Reference canonical Estate records rather than copying them into a competing local database.
- Keep local experimental workloads visibly distinct from Estate-managed workloads.

## 9. Expandability model

Expansion should occur through workload adapters rather than special-case growth in the core service.

Each adapter should declare:

- adapter and schema version;
- required hardware and software capabilities;
- input contract;
- launch mechanism;
- progress-observation method;
- checkpoint, pause, resume and cancellation behavior;
- expected artifacts;
- artifact-verification method;
- resource estimates and safe operating constraints.

The common runtime owns admission, lifecycle, resource checks, audit, recovery and reporting. The adapter owns workload-specific execution details.

## 10. Explicit non-goals and prohibitions

This workstream must not create:

- a second Estate intake or approval inbox;
- a second PTM dependency graph or institutional scheduler;
- a second Execution Dispatch queue;
- a parallel provider, health, capacity or personnel registry;
- a competing validation or acceptance authority;
- automatic merge or self-acceptance behavior;
- an Evelyn-specific architecture that prevents other workload adapters;
- campaign state that exists only in chat, a dashboard or folder placement;
- direct Estate execution that bypasses required authorization and provider handoff.

## 11. Current decisions

1. Proceed as an active work-in-progress concept, not a parking-lot item.
2. Do not begin implementation yet.
3. Treat Evelyn as the first workload profile, not the system name.
4. Treat the core as a reusable Local Compute Campaign Runtime or equivalent provider capability.
5. Use API-first design with a local operator client as one consumer.
6. Integrate all relevant Estate actors through their existing responsibilities and authority boundaries.
7. Give Grace sufficient operational visibility and Dispatch interaction to act as Engineering manager without granting new acceptance authority.
8. Give Helen/HR appropriate qualification, staffing and assignment visibility without duplicating HR systems.
9. Use Alfred for communication and attention surfaces, not execution state or authority.
10. Reuse Estate Dispatch, provider, PTM/orchestrator and validation seams.
11. Distinguish provider-local timing from Estate-level scheduling.
12. Preserve durable evidence and resumability from the first implementation slice.

## 12. Open questions requiring later design

- Which canonical Estate record authorizes a local compute attempt for each workload class?
- Which existing provider adapter should be extended, or is a new adapter implementation needed under the existing provider contract?
- How should Grace’s Engineering-manager actions map to current Grace objectives, actions and Dispatch requests?
- What read model should Helen/HR receive, and what qualification rules apply to AI and human operators?
- Which events should Alfred surface, and through which existing mailbox or duty mechanism?
- What minimum evidence contract applies to image generation versus training, transcription and other adapters?
- Where should the runtime live physically on `A:` and which configuration belongs in the Estate repository?
- How should local Steward experiments later be promoted into governed Estate campaigns without rewriting their history?
- What security and credential mechanism should protect local API mutation endpoints?
- What is the smallest useful implementation slice that proves the architecture without building a duplicate control plane?

## 13. Current hold point

The concept has been captured and formally kicked off. Work is paused before architecture selection, work-package authoring or implementation. Resume only after the Steward returns to this workstream and authorizes the next action.
