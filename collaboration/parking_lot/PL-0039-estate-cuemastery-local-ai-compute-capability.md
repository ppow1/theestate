# PL-0039 — Estate and CueMastery Local AI Compute Capability

Status: Captured
Priority: Strategic
Category: AI Compute / Estate Infrastructure / CueMastery
Originator: Pat / Steward
Date Captured: 2026-08-06
Target Milestone: After Comms8 production stabilization and before AI compute procurement or deployment

## Idea

Establish a governed local AI compute capability centered on an eight-GPU NVIDIA Tesla P100 SXM2 server, the existing Estate development workstation with an RTX 4090, and the incoming PCIe Tesla P100. Use the Estate to coordinate the resulting compute fabric so it advances both Estate engineering and CueMastery product goals while preserving Comms8 as the escalation path for higher-level reasoning and the local Codex adapter as the bounded implementation path.

The proposed system is not one distributed model stretched across Ethernet. It is a governed set of separate compute nodes with different strengths:

- the development workstation provides fast interactive inference and modern GPU support;
- the workstation P100 provides an independent background worker;
- the SXM2 server provides eight matched P100 GPUs, 128 GB aggregate HBM2, parallel local workers, and the ability to host larger multi-GPU models;
- Comms8 provides selective escalation to stronger external reasoning when local models are insufficient;
- the local Codex command-line adapter performs approved implementation against the actual Estate filesystem and Git state;
- Grace and the Estate retain authority over work creation, routing, acceptance, execution authorization, evidence, and admission of change.

## Proposed Hardware Baseline

### Development workstation

Expected AI resources:

- NVIDIA RTX 4090 with 24 GB VRAM;
- one PCIe NVIDIA Tesla P100 with 16 GB HBM2;
- existing workstation storage, repositories, development tools, and interactive operator environment.

The two GPUs should initially be treated as separate workers. Do not assume that their memory can be combined into one transparent 40 GB pool.

### SXM2 server

Candidate baseline:

- Supermicro SYS-4028GR-TXRT / X10DGO-T class 4U platform;
- eight installed NVIDIA Tesla P100 16 GB SXM2 modules;
- 128 GB aggregate HBM2;
- CPUs, system RAM, and boot storage added to make the unit operational;
- Linux, compatible NVIDIA drivers, CUDA/tooling, monitoring, and Estate-controlled service startup.

Planning cost discussed at capture time:

- server with eight P100 SXM2 GPUs: approximately $1,399;
- CPUs and starting system RAM: approximately $200–300 depending on used-market sourcing;
- existing SSD may be used initially;
- estimated operational entry cost: approximately $1,600–1,700 before any infrastructure changes for power, cooling, rack placement, or networking.

These figures are planning assumptions, not procurement authorization or a verified final landed cost.

## Strategic Thesis

The SXM2 server fills the missing middle tier between the fast development workstation and advanced reasoning through Comms8.

The combined architecture is:

```text
Pat / Steward
    |
    v
Grace and Estate authority
    |
    +----------------------+----------------------+----------------------+
    |                      |                      |                      |
    v                      v                      v                      v
Deterministic Estate   RTX 4090 workstation   SXM2 P100 server      Comms8
logic and validators   fast interactive work  local volume/capacity  advanced reasoning
    |                      |                      |                      |
    +----------------------+----------------------+----------------------+
                                   |
                                   v
                         Governed Estate result
                                   |
                          Grace evaluates result
                                   |
                 advisory / reject / revise / park / authorize
                                   |
                                   v
                       Local Codex execution adapter
                                   |
                    implementation, tests, evidence, receipt
                                   |
                                   v
                     Estate review and admission of change
```

The Estate should use the lowest-cost, lowest-authority tier capable of producing a trustworthy result. Local compute handles routine volume and parallel work. Comms8 handles difficult bounded reasoning. Codex handles approved implementation. Grace controls transitions where authority changes.

## Estate Capability Enabled

### 1. Persistent private processing tier

The Estate gains a server that can remain available for long-running local work without monopolizing the development workstation.

Suitable workloads include:

- repository indexing and retrieval preparation;
- document classification and summarization;
- comparison of specifications, plans, receipts, and evidence;
- log and telemetry analysis;
- test-result review;
- work-package preflight analysis;
- bounded code-review assistance;
- generation of candidate diagnoses and hypothesis matrices;
- batch embedding and retrieval jobs;
- local model qualification and benchmarking;
- overnight analysis queues.

### 2. Parallel worker capacity

Eight P100s can run independent workers when the work is separable. One P100 is slower than the RTX 4090, but eight workers can produce greater aggregate throughput across independent jobs.

Examples:

- eight unrelated repository analyses;
- separate workers for Discovery retrieval, evidence extraction, log analysis, test review, contradiction detection, report drafting, validation review, and overflow;
- concurrent processing for multiple Estate projects;
- background review while the 4090 remains available to Pat.

More compute must produce more verified progress, not more simultaneous speculation. Grace should route bounded work, Discovery should ground it, and Audit should check conclusions before durable admission.

### 3. Larger local model capacity

The SXM2 server can operate in a large-model mode where several or all GPUs cooperate to host a model that does not fit on one 16 GB or 24 GB GPU.

The 128 GB figure is aggregate GPU memory, not one physically unified memory pool. Software must partition the model and communicate across the SXM2/NVLink topology. This mode should be used when capacity and local privacy matter more than latency.

Potential uses:

- large repository synthesis;
- broad architectural review;
- synthesis across many Estate artifacts;
- long-context planning;
- local analysis of private or sensitive operational material;
- preparing a high-quality bounded Comms8 escalation request.

### 4. Better Comms8 economics and request quality

The server does not replace Comms8. It reduces unnecessary escalation and improves escalations that remain necessary.

Local workers can:

- retrieve and organize evidence;
- identify contradictions;
- summarize failed attempts;
- separate verified facts from hypotheses;
- narrow the unresolved architectural question;
- assemble artifact references and constraints;
- draft a bounded request package.

Comms8 can then be reserved for difficult architectural reasoning, evidence reconciliation, risk analysis, and implementation-package design.

### 5. Codex preparation and review

Local compute can assist before and after local Codex execution without becoming execution authority.

Before execution:

- inspect repository context;
- verify likely affected subsystem;
- identify required reading;
- identify test and validation obligations;
- detect scope collisions;
- draft explicit non-actions.

After execution:

- compare changed files against authorized scope;
- review test evidence;
- inspect receipts;
- identify unresolved failures;
- prepare Audit input.

Codex remains the bounded local implementation worker. The Estate remains responsible for acceptance.

### 6. Discovery and Audit reinforcement

This proposal should strengthen existing Estate subsystems rather than create new institutional branches.

Discovery can absorb retrieval, indexing, context assembly, and evidence-location responsibilities.

Audit can absorb evidence sufficiency, claim classification, scope compliance, validation review, and contradiction checks.

Alfred and Helen can use job state and receipts for coordination and visibility. Grace remains the authority for routing, escalation, and acceptance.

## CueMastery Capability Enabled

CueMastery is a cue-sports intelligence platform whose near-term mission is to prove the integrated AuraHalo/AuraBot learning loop:

```text
Prepare the table
    -> Observe the attempt
    -> Measure the outcome
    -> Explain the weakness
    -> Rebuild the opportunity
    -> Repeat until the lesson sticks
```

The local compute fabric can support both immediate engineering work and later product intelligence.

### 1. Near-term engineering acceleration

Before production coaching exists, CueMastery already has substantial AI-suitable engineering workload:

- repository and documentation indexing;
- firmware-log analysis;
- BOT2 telemetry comparison;
- test and bench evidence reconciliation;
- AuraHalo camera and calibration report analysis;
- detector dataset evaluation;
- table-geometry evidence review;
- requirements traceability;
- cross-document contradiction detection;
- test-matrix generation;
- Codex output review;
- preparation of focused Comms8 escalations.

The workstation remains the fast interactive bench partner. The SXM2 server handles background synthesis and parallel work.

### 2. Post-session intelligence production

When AuraHalo produces reliable observations, the SXM2 server can become the post-session processing plant.

Potential worker pipeline:

1. ingest session media and structured telemetry;
2. segment shots and events;
3. reconstruct table states;
4. calculate shot and cue-ball position outcomes;
5. compare results against player history;
6. detect recurring weaknesses;
7. rank replay candidates;
8. propose next drills;
9. prepare film-study notes;
10. produce a supportive scorecard and coaching summary.

This work is naturally parallel and generally does not require millisecond latency.

### 3. Replay queue and runback selection

CueMastery should not save every miss indiscriminately. AI workers can help identify which failed states are:

- reliably observed;
- physically reconstructable by AuraBot;
- representative of a recurring weakness;
- pedagogically valuable;
- appropriate for immediate retry or future practice;
- supported by sufficient confidence and evidence.

The output can feed a governed replay queue. AI interpretation must remain distinguishable from measured observations and human-confirmed conclusions.

### 4. Personalized drill generation

After sufficient verified data exists, the compute fabric can generate and evaluate drills tailored to observed weaknesses such as:

- cue-ball control;
- speed control;
- banks;
- safeties;
- breakouts;
- end patterns;
- position play;
- recovery routes.

Generated drills should remain downstream of validated table geometry, placement capability, evidence quality, and product rules. The system should not invent capabilities that AuraBot or AuraHalo has not proven.

### 5. AI Coach and AI Caddy development

The server can support early AI Coach prototypes focused on post-session review, progression, drill sequencing, and replay planning.

The RTX 4090 is better suited to fast interactive experimentation and current-table response work.

The SXM2 server is better suited to deeper post-session synthesis, historical comparison, batch processing, and larger local models.

Real-time AI Caddy behavior should remain a separate evidence- and safety-gated product investigation.

### 6. Media, reporting, and possible revenue capability

The same processing pipeline can eventually create reviewed, rights-aware outputs such as:

- post-session player reports;
- coach review packages;
- Beat the Table scorecards;
- annotated film-study summaries;
- venue performance reports;
- drill and curriculum material;
- carefully reviewed technical and educational content;
- internal datasets and analytics products.

The compute lowers production cost and increases throughput. It does not create demand, rights, consent, trustworthy measurements, or editorial quality by itself.

## Estate Coordination Model

### Job classes

The Estate should classify work before dispatch:

- deterministic or model-based;
- interactive or background;
- single-worker or parallel;
- small-model or large-model;
- exploratory or evidence-bearing;
- local-capable or Comms8-worthy;
- advisory or implementation-bound;
- safe for automation or requiring human approval.

### Suggested routing

| Work type | Preferred destination |
|---|---|
| Validators, parsers, state machines, exact checks | Deterministic Estate code |
| Fast interactive coding and bench reasoning | RTX 4090 |
| Modern vision/image model experiments | RTX 4090 |
| Independent background processing | Workstation P100 or SXM2 worker |
| Many independent analyses | SXM2 worker fleet |
| Large private synthesis | Multi-GPU SXM2 mode |
| Difficult architecture or evidence reconciliation | Comms8 |
| Approved repository implementation | Local Codex adapter |
| Final authority, acceptance, and exceptions | Pat / Grace / governed Estate process |

### Required job record

A future promoted implementation should reuse existing Estate work, campaign, runtime, and evidence systems where possible. Each dispatched AI job should have at least:

- stable job or work identity;
- project/workflow identity;
- objective;
- bounded input references;
- evidence classification;
- assigned node and model;
- GPU allocation;
- priority;
- start time;
- progress or heartbeat state;
- output location;
- validation requirement;
- completion status;
- receipt or result reference;
- acceptance disposition.

Do not create a new registry if existing worker telemetry, campaign execution, Comms8 lifecycle, work-package, Discovery, Audit, or operations state can absorb the responsibility.

## Example Combined Workflow

### CueMastery engineering failure

```text
BOT2 or AuraHalo produces a failure and evidence
    -> Estate creates bounded local analysis jobs
    -> SXM2 workers inspect logs, docs, tests, and prior decisions in parallel
    -> local synthesis produces evidence-backed candidate diagnoses
    -> Audit checks evidence quality
    -> Grace accepts locally, requests more evidence, or escalates through Comms8
    -> Comms8 returns advanced bounded reasoning
    -> Grace accepts only the authorized implementation package
    -> local Codex adapter implements, tests, and records evidence
    -> Estate reviews result before admission
```

### CueMastery player session

```text
AuraHalo and AuraBot produce measured session evidence
    -> Estate stores and classifies evidence
    -> SXM2 workers process shots, outcomes, history, and replay candidates
    -> synthesis generates scorecard, coaching draft, and replay plan
    -> evidence and confidence gates are applied
    -> approved outputs enter the CueMastery product workflow
    -> replay states are rebuilt and verified on the physical table
```

## Initial Operating Modes

### Estate engineering mode

Possible starting allocation:

- GPUs 0–1: repository and documentation reasoning;
- GPUs 2–3: logs, telemetry, and evidence analysis;
- GPU 4: dataset preprocessing/evaluation;
- GPU 5: requirements and consistency review;
- GPU 6: embeddings and Discovery support;
- GPU 7: experimental or overflow worker.

### CueMastery intelligence mode

Possible future allocation:

- GPUs 0–1: larger coaching/synthesis model;
- GPU 2: shot/session summarization;
- GPU 3: player-history comparison;
- GPU 4: replay-candidate scoring;
- GPU 5: drill generation;
- GPU 6: report and film-study generation;
- GPU 7: evidence validation or backlog processing.

These are hypotheses for benchmarking, not fixed policy.

## Phased Adoption Proposal

### Phase 0 — Procurement validation

Before purchase:

- confirm all eight P100 SXM2 modules are installed;
- confirm SXM2 baseboard, heatsinks/cold plates, power supplies, fans, and required internal assemblies are present;
- confirm exact supported CPU list and required matched CPU population;
- confirm starting RAM layout;
- confirm freight terms and damage/return policy;
- confirm electrical input requirements;
- confirm rack depth, weight, noise, heat, and cooling implications;
- confirm compatible NVIDIA driver/CUDA path for the selected inference stack.

### Phase 1 — Hardware bring-up

- install CPUs, RAM, and existing SSD;
- install Linux;
- validate all CPUs, DIMMs, storage, fans, PSUs, BMC, and network interfaces;
- verify all eight GPUs enumerate;
- run memory, compute, thermal, and sustained-load checks;
- record a baseline hardware receipt;
- do not integrate with production Estate services until standalone stability is proven.

### Phase 2 — Local inference qualification

- qualify compatible runtimes and models;
- benchmark one-GPU, multi-GPU, and independent-worker modes;
- measure tokens per second, load time, memory use, stability, power, and thermals;
- test model partitioning across the SXM2 topology;
- compare with RTX 4090 latency and throughput;
- establish which jobs should never be routed to P100s due to software or performance limitations.

### Phase 3 — Estate worker integration

- expose a bounded local inference/job interface;
- reuse existing Estate execution, telemetry, Discovery, Audit, and operations patterns;
- add node health, job state, evidence location, and completion receipts;
- route only non-authoritative background work initially;
- retain human approval and current repository authority boundaries.

### Phase 4 — CueMastery engineering workloads

- start with repository, logs, telemetry, calibration, and dataset work;
- measure actual value and queue utilization;
- improve Comms8 escalation packages;
- keep current BOT2/AuraHalo critical-path work authoritative and scoped.

### Phase 5 — CueMastery session intelligence

Only after reliable observation and shot records exist:

- add post-session scorecards;
- add replay-candidate ranking;
- add film-study drafts;
- add personalized drill proposals;
- preserve consent, rights, confidence, and human-review gates.

## Risks and Constraints

### Hardware age and software support

P100 is Pascal-generation hardware without modern Tensor Cores. It provides capacity and parallelism but is substantially slower than an RTX 4090 for many modern quantized inference kernels. Some current frameworks or kernels may reduce or drop Pascal support.

### Aggregate VRAM is not unified VRAM

Eight 16 GB GPUs provide 128 GB aggregate capacity only when software can partition the model or workload. Multi-GPU inference may be slower and topology-sensitive.

### Power, heat, and noise

An eight-GPU 4U server is datacenter equipment. Deployment may require 200–240 V power, substantial continuous electrical capacity, high airflow, heat removal, rack space, and tolerance for severe fan noise.

### Integration cost

The server creates value only if the Estate can dispatch, observe, validate, and retain work. Without integration, it risks becoming a manually invoked experimental box.

### Scope displacement

The purchase must not displace CueMastery's current critical path: reliable electronics, motion, pickup/placement, AuraHalo perception, calibration, and table-state verification.

### Authority confusion

Local model output must not become authoritative merely because it is local or produced by eight GPUs. Comms8 responses must not become implementation orders merely because they are advanced. Codex output must not become accepted change merely because tests ran. Grace and the governed Estate lifecycle retain authority.

### Revenue assumptions

Possible CueMastery reports, coaching products, media, technical content, and analytics are future business hypotheses. Compute capacity alone does not validate demand or commercialization.

## Evaluation Metrics

A promoted pilot should measure:

- percentage of background Estate work moved off the RTX 4090;
- local jobs completed per day;
- parallel-worker utilization;
- Comms8 requests avoided because local reasoning was sufficient;
- improvement in Comms8 request quality and boundedness;
- reduction in repeated context reconstruction;
- time from evidence arrival to reviewed result;
- job failure and retry rate;
- sustained thermal and hardware stability;
- CueMastery engineering tasks accelerated;
- post-session processing time when session data becomes available;
- operator attention saved;
- cost per useful accepted result.

## Why It Is Parked

This proposal is strategically valuable but should not interrupt current Comms8 stabilization, Discovery strengthening, Audit strengthening, or CueMastery critical-path hardware and perception work.

Procurement and integration require additional verification of hardware condition, CPU/RAM compatibility, electrical service, thermal placement, software support, and the smallest Estate integration slice.

Capturing the proposal now preserves the architecture and decision context without authorizing purchase, creating new services, or expanding current engineering campaigns.

## Promotion Condition

Promote when all of the following are true:

1. Pat intentionally authorizes procurement or a final procurement evaluation.
2. The exact server configuration, included SXM2 hardware, return terms, and completion cost are verified.
3. Power, cooling, rack placement, noise, and networking are acceptable.
4. A compatible Linux/NVIDIA/CUDA/inference software path is demonstrated or credibly validated for P100.
5. Comms8 production stabilization is complete enough that this work will not disrupt current acceptance.
6. Discovery and Audit can absorb retrieval and review duties without creating a parallel institution.
7. A first bounded implementation slice is defined: standalone bring-up and benchmark first, Estate integration second.
8. Success metrics and an exit/repurpose condition are documented.

## Explicit Non-Action

Do not purchase hardware solely because this proposal has been captured.

Do not modify current Comms8 acceptance, Blue/Green topology, ChatGPT provider configuration, local Codex adapter, Estate production services, CueMastery runtime, or repository workflows as part of parking this idea.

Do not create a new AI department, compute office, job registry, scheduler, memory system, or authority layer unless existing Estate subsystems cannot absorb the responsibility.

Do not treat 128 GB aggregate HBM2 as one unified 128 GB GPU.

Do not assume the RTX 4090 and workstation P100 form one unified 40 GB device.

Do not assume a model can be split efficiently between the workstation and SXM2 server over ordinary Ethernet.

Do not promote AI interpretations into verified CueMastery observations, coaching claims, repository truth, or executable work without the required evidence and approval.

## Related Evidence

Estate references:

- `AI_HINTS.md`
- `AI_COMMUNICATION_HINTS.md`
- `docs/mcp/Estate_Comms8_MCP_App_Repair_and_Correct_Creation_Reference.md`
- `operations/boards/parking_lot.md`
- existing Discovery, Audit, worker telemetry, campaign, Comms8, work-package, and Codex adapter capabilities

CueMastery references:

- `ppow1/CueMastery:AI_HINTS.md`
- `ppow1/CueMastery:docs/ai_start_here.md`
- `ppow1/CueMastery:docs/new_chat_orientation_handbook.md`
- `ppow1/CueMastery:docs/ops/cuemastery_active_index.md`
- `ppow1/CueMastery:docs/product/auraarena_north_star_vision.md`
- `ppow1/CueMastery:docs/product_spec.md`
- `ppow1/CueMastery:docs/strategy/cuemastery_platform_vision_extended.md`

Conversation-derived planning assumptions to verify before promotion:

- candidate SXM2 listing includes eight P100 16 GB SXM2 modules;
- candidate purchase price is approximately $1,399 before CPUs/RAM;
- estimated complete entry cost is approximately $1,600–1,700 when an existing SSD is used;
- development workstation includes RTX 4090 and an incoming PCIe P100.
