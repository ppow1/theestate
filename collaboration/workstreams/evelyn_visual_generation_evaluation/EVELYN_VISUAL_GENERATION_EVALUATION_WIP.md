# Evelyn Visual Generation Evaluation — Work in Progress

**Status:** IN PROCESS  
**Started:** 2026-07-26  
**Current phase:** Recovering and formalizing the incomplete generation-method evaluation  
**Execution state:** A functioning campaign path exists, but the broader model/template/runtime evaluation is incomplete

## 1. Purpose

This workstream preserves and resumes the unfinished evaluation of the different models, templates, workflows, and execution methods available for producing Evelyn visual artifacts.

The current system can produce useful output, including the successful overnight campaign, but that success must not be mistaken for completion of the original evaluation. Only a small portion of the candidate approaches was actually tested. The remaining alternatives, comparison logic, evidence requirements, and final selection process still need to be completed.

This workstream is separate from:

- the **Evelyn Canon Program**, which defines what canon campaigns and artifacts are needed;
- the **Local Compute Campaign Runtime**, which defines how bounded local workloads should be admitted, executed, resumed, and reported.

This workstream determines which visual-generation stack or stacks should be used for each class of Evelyn artifact.

## 2. Current understanding

The discussion considered approximately ten possible generation approaches or stack variations. Only roughly two were explored far enough to produce meaningful observations.

A functioning campaign runner now exists and can drive long unattended generation runs. The current path appears to use command-line or scripted orchestration around ComfyUI rather than requiring the operator to manually construct and launch every job in the browser interface.

However, the current implementation still appears to rely on ComfyUI as the underlying inference engine or workflow host. It is therefore not yet the fully direct Python-native execution path that was also discussed.

The important distinction is:

```text
Manual ComfyUI use
    Operator opens the UI, edits nodes, and queues jobs manually.

Scripted ComfyUI execution
    Python or PowerShell prepares jobs and submits workflows to ComfyUI through its API or queue.
    ComfyUI still performs the underlying graph execution.

Direct Python execution
    Python loads the model pipeline and performs inference directly without ComfyUI being the runtime host.
```

The current campaign is believed to be in the **scripted ComfyUI execution** category. This must be verified from the actual runner and workflow files before being treated as final fact.

## 3. Why the evaluation remains necessary

A solution that works is not automatically the best long-term solution.

The Estate needs to know:

- which models preserve Evelyn identity most reliably;
- which templates or workflows produce the best face, body, hands, wardrobe, pose, lighting, and environment results;
- whether one stack is sufficient or different artifact classes need different stacks;
- whether ComfyUI remains useful as the primary runtime, an authoring tool only, or one provider among several;
- whether direct Python execution improves throughput, repeatability, testability, automation, or integration;
- which approach is easiest to run unattended for many hours;
- which approach provides the strongest manifests, metadata, failure handling, and reproducibility;
- which path best fits the future Local Compute Campaign Runtime and Estate provider boundaries.

## 4. Evaluation principles

The evaluation should compare approaches using the same or closely matched inputs wherever possible.

Each candidate should be measured against:

1. **Identity fidelity** — Does the output remain recognizably Evelyn?
2. **Face consistency** — Does facial geometry survive angle, expression, and lighting changes?
3. **Body consistency** — Are proportions and physical characteristics stable?
4. **Pose control** — Can the system reliably produce requested posture and movement?
5. **Hand and anatomy quality** — How often do hands, fingers, limbs, or joints fail?
6. **Wardrobe persistence** — Can a canonical outfit remain stable across views and poses?
7. **Prompt adherence** — Does the output follow the requested content and framing?
8. **Reference-image control** — Can source images be used without excessive drift or copying defects?
9. **Reproducibility** — Can the same inputs, seed, model, and settings reproduce comparable output?
10. **Throughput** — Images per hour and usable images per hour on the RTX 4090.
11. **VRAM and system use** — Peak VRAM, RAM, disk, and thermal behavior.
12. **Batch reliability** — Can the method survive hundreds of jobs without operator intervention?
13. **Recovery** — Can it resume after failure, reboot, or interruption?
14. **Metadata quality** — Are prompt, seed, model, workflow, and source references preserved?
15. **Automation fit** — Can it be controlled cleanly from scripts and later through the runtime API?
16. **Maintainability** — How fragile is it across model, package, or custom-node upgrades?
17. **Operator usability** — Can workflows be inspected and adjusted without excessive complexity?
18. **Estate integration fit** — Can it report bounded execution attempts and evidence without becoming a separate control plane?

## 5. Candidate approach families

The exact original list of approximately ten candidates must be recovered from prior notes, scripts, model folders, and conversation history. Until then, the following is the working evaluation set. These are categories, not claims that every one was previously named exactly this way.

### Candidate A — Manual ComfyUI workflow

Use ComfyUI interactively for workflow construction, prompt changes, queueing, and review.

**Strengths:** visual authoring, node inspection, rapid experimentation, community nodes.  
**Weaknesses:** manual work, harder unattended operation, inconsistent operator steps unless workflow and parameters are captured.

### Candidate B — Scripted ComfyUI API campaign

Use Python or PowerShell to generate job definitions and submit saved ComfyUI workflow JSON through the ComfyUI API.

**Current relevance:** This appears closest to the successful campaign method.  
**Strengths:** preserves ComfyUI workflows while enabling large batches, unattended runs, manifests, and queue automation.  
**Weaknesses:** still depends on ComfyUI server state, workflow-node compatibility, and custom-node stability.

### Candidate C — Direct Python Diffusers pipeline

Load supported checkpoints and control components directly with Python libraries such as Diffusers, bypassing ComfyUI as the runtime host.

**Strengths:** direct programmatic control, easier unit testing, explicit dependencies, potentially cleaner integration into a service.  
**Weaknesses:** more engineering, pipeline-specific code, feature gaps relative to mature ComfyUI graphs, dependency/version complexity.

### Candidate D — Direct native model/runtime implementation

Use the model's preferred native repository or inference package rather than a generic Diffusers or ComfyUI wrapper.

**Strengths:** access to model-specific features and reference behavior.  
**Weaknesses:** fragmented interfaces, inconsistent metadata, greater maintenance burden.

### Candidate E — ComfyUI-authored, Python-executed compiled workflow

Use ComfyUI for visual workflow design, then translate or wrap the approved graph into a Python-owned execution package.

**Strengths:** combines visual design with service-oriented execution.  
**Weaknesses:** translation fidelity and maintenance may be difficult; could create two representations of the same workflow.

### Candidate F — Model-specific identity/reference workflow

Evaluate IP-Adapter, InstantID, PuLID, PhotoMaker, FaceID, or comparable identity-preservation approaches as applicable to the selected base model.

**Strengths:** stronger identity anchoring without a full custom model.  
**Weaknesses:** varying support, likeness drift, reference sensitivity, licensing or model compatibility constraints.

### Candidate G — LoRA-based Evelyn identity pipeline

Train or refine an Evelyn-specific LoRA or related adapter and compare it with reference-only methods.

**Strengths:** potentially stronger repeatability across prompts and contexts.  
**Weaknesses:** training-data curation, overfitting, body/wardrobe entanglement, training time, version management.

### Candidate H — Hybrid LoRA plus reference/control pipeline

Use an Evelyn identity adapter together with pose, depth, edge, face, or composition controls.

**Strengths:** potentially strongest combination of identity and scene control.  
**Weaknesses:** more variables, more difficult attribution of failures, increased VRAM and workflow complexity.

### Candidate I — Alternative base-model family

Compare the current base model with other locally runnable model families suitable for photorealistic human generation on the RTX 4090.

**Strengths:** may improve anatomy, prompt following, identity, or speed.  
**Weaknesses:** requires matched tests; workflow assets and adapters may not transfer.

### Candidate J — Specialized multi-stage production pipeline

Use different tools for generation, correction, inpainting, upscaling, face refinement, hand repair, background work, or compositing.

**Strengths:** may produce the highest final quality and allow targeted repair.  
**Weaknesses:** more stages, greater provenance burden, slower throughput, more opportunities for identity drift.

## 6. Candidate status ledger

The original exact model and template names are not fully recoverable from the current repository search alone. This ledger must be corrected when the actual local scripts, workflows, and prior discussion records are reviewed.

| Candidate | Current status | Evidence presently known |
| --- | --- | --- |
| Manual ComfyUI workflow | Partially tested | Used during early experimentation and workflow development. Exact workflow paths and results must be indexed. |
| Scripted ComfyUI API campaign | Functioning / materially tested | Successfully supported the recent overnight approximately eight-hour campaign. Exact runner, API method, workflow, and output paths must be confirmed. |
| Direct Python Diffusers pipeline | Discussed, not completed | Identified as a way to bypass ComfyUI runtime dependence; no completed matched evaluation presently recorded. |
| Native model-specific Python runtime | Proposed / unverified | Requires candidate model and repository selection. |
| ComfyUI-authored Python-executed workflow | Conceptual | Requires feasibility test. |
| Identity/reference adapters | Partially explored or planned | Exact adapters and outcomes must be recovered. |
| Evelyn LoRA | Planned / not evaluated to completion | Requires training-set and acceptance design. |
| Hybrid LoRA plus controls | Planned | Depends on LoRA and control-method baselines. |
| Alternative base models | Incomplete | Approximately ten total options were discussed; only about two were meaningfully tried. Exact model list must be reconstructed. |
| Multi-stage production pipeline | Planned | Needs comparison against single-pass generation and repair workflows. |

## 7. Current functioning path

The current production-capable path should be documented precisely when work resumes.

The expected structure is approximately:

```text
Campaign definition / prompt catalog
        ↓
Python or PowerShell campaign runner
        ↓
ComfyUI API queue submission
        ↓
Saved ComfyUI workflow graph
        ↓
Model and adapter execution on RTX 4090
        ↓
Output images
        ↓
Manifest / ledger / success-failure records
```

The following details need confirmation:

- runner script absolute path;
- whether the runner is Python, PowerShell, or both;
- ComfyUI server path and launch command;
- API endpoint and submission mechanism;
- workflow JSON path;
- model/checkpoint names;
- VAE, text encoder, LoRA, ControlNet, IP-Adapter, or other dependencies;
- prompt-template path;
- output path;
- manifest and ledger paths;
- retry and recovery behavior;
- whether ComfyUI must remain visible or only running as a service;
- exact reason this method was selected for the overnight campaign.

## 8. Direct Python evaluation track

The direct Python option must be evaluated as a genuine alternative, not merely discussed.

A minimum proof should:

1. Load one selected base model directly in a dedicated Python environment.
2. Reproduce a small, already-understood Evelyn benchmark set.
3. Accept structured job input rather than hard-coded prompts.
4. Preserve seed, prompt, negative prompt, model identity, dimensions, steps, sampler/scheduler equivalents, and source-image provenance.
5. Write outputs and a machine-readable run receipt.
6. Report VRAM use, runtime, failures, and throughput.
7. Support cancellation between images.
8. Be compared against the scripted ComfyUI path using the same benchmark specification.

The direct Python proof does not need to replace ComfyUI. Its purpose is to determine whether it provides enough operational or quality advantage to justify maintenance.

## 9. Test corpus design

A matched evaluation should use a compact but representative benchmark corpus, such as:

- neutral face: front, profile, and three-quarter;
- four to eight expressions;
- head-and-shoulders and full-body views;
- neutral standing and seated pose;
- one difficult hand interaction;
- one canonical wardrobe test;
- one lighting change;
- one environment change;
- one reference-image-driven test;
- one long batch reliability test.

The same benchmark specification should be run through each viable candidate where technically possible.

## 10. Scoring method

Each output set should receive both automated and human review data.

### Automated or machine-recorded evidence

- execution success rate;
- runtime;
- throughput;
- VRAM and RAM use;
- output count;
- missing or corrupt files;
- metadata completeness;
- deterministic or near-deterministic reproduction behavior;
- failure and retry counts.

### Steward visual review

- Evelyn recognition;
- facial consistency;
- body and anatomy quality;
- pose and prompt adherence;
- wardrobe consistency;
- emotional accuracy;
- overall usefulness;
- whether the output is candidate-quality, reference-quality, or canon-promotion quality.

### Comparative outcome

Do not force a single universal winner if the evidence supports specialized choices. The final result may be a capability map such as:

- best fast benchmark generator;
- best face/portrait method;
- best full-body method;
- best pose-controlled method;
- best wardrobe-consistency method;
- best high-quality final-render method;
- best unattended campaign runtime;
- best experimental authoring environment.

## 11. Template evaluation

The word **template** may refer to several different layers and they should not be conflated:

- prompt template;
- negative-prompt template;
- ComfyUI workflow template;
- model/pipeline configuration template;
- campaign job template;
- output naming and directory template;
- manifest and ledger template;
- visual review sheet template.

Each tested result should identify exactly which template layers changed. Otherwise a quality improvement cannot be attributed to the model, prompt, workflow, or runtime.

## 12. Model evaluation

Each model candidate record should capture:

- exact model name and version;
- local absolute path;
- source and license notes;
- quantization or precision;
- required VAE and text encoders;
- supported identity and control adapters;
- recommended resolution;
- VRAM requirement;
- compatible ComfyUI nodes and Python libraries;
- benchmark campaign IDs;
- strengths;
- failure modes;
- final disposition: rejected, retained for specialty use, preferred, or pending.

## 13. Execution-method evaluation

The evaluation must distinguish image quality from runtime quality.

A model may produce excellent images but still be unsuitable for long unattended campaigns if it:

- leaks VRAM;
- crashes after repeated jobs;
- cannot resume;
- loses metadata;
- requires manual node changes;
- cannot expose progress;
- makes retry behavior ambiguous;
- depends on unstable custom nodes.

Conversely, a highly reliable runtime should not be selected if it cannot produce acceptable Evelyn identity and anatomy.

## 14. Relationship to ComfyUI

The current direction should not be framed as “ComfyUI or no ComfyUI” as a single binary decision.

Possible long-term roles include:

1. **Primary authoring and execution platform** — workflows are built and run in ComfyUI.
2. **Headless execution provider** — scripts submit approved graphs through the API; the browser UI is optional.
3. **Workflow prototyping tool** — workflows are designed visually and later implemented in direct Python.
4. **Specialized provider** — only workloads that benefit from node graphs use ComfyUI.
5. **Repair and finishing tool** — primary generation happens elsewhere, with ComfyUI used for inpainting, control, or upscaling.

The evaluation should determine the appropriate role rather than presuming total replacement or permanent exclusivity.

## 15. Evidence and file locations

The following current paths must be added after inspection:

```text
Current campaign runner:
<confirm absolute path>

Current ComfyUI workflow:
<confirm absolute path>

Current prompt/template catalog:
<confirm absolute path>

Current tested models:
<confirm exact names and paths>

Current overnight output:
<confirm absolute path>

Current manifests and ledgers:
<confirm absolute paths>

Earlier comparison outputs:
<confirm absolute paths>

Direct-Python prototype, if any:
<confirm whether one exists>
```

Repository-side evidence already shows that the Visual Bible foundation created schemas, repository structure, validators, authoring guidance, and campaign records, while final image libraries and explicit canonical lock remained separate concerns. This evaluation workstream should use those governance and evidence structures rather than treating raw output as automatically canonical.

## 16. Decisions preserved

1. The visual-generation evaluation is incomplete and must remain active.
2. A functioning campaign path exists, but it is not sufficient evidence that the best model or execution method has been selected.
3. The successful overnight run should be treated as evidence for the current scripted campaign path.
4. The current path likely uses scripted ComfyUI execution, not a fully direct Python inference pipeline; this must be verified.
5. Direct Python execution remains a required comparison track.
6. Approximately ten candidate options or stack variations were originally discussed; the exact list must be reconstructed rather than guessed into canonical status.
7. Models, prompt templates, workflow templates, identity methods, control methods, and execution runtimes must be evaluated as distinct variables.
8. The final outcome may retain multiple specialized stacks rather than selecting one universal method.
9. Every comparison must preserve prompts, seeds, settings, paths, manifests, runtime data, and review outcomes.
10. No generated artifact becomes Evelyn canon merely because its pipeline completed successfully.

## 17. Immediate next actions when work resumes

1. Inspect the current campaign runner and confirm whether it submits jobs through the ComfyUI API.
2. Record all exact local paths and dependency versions.
3. Recover the original candidate model/template list from earlier notes, downloads, model directories, workflows, and conversation records.
4. Identify the two approaches already tested and attach their evidence.
5. Build a compact matched benchmark corpus.
6. Define the scoring sheet and review categories.
7. Run the remaining model/workflow candidates in small batches before any additional eight-hour comparisons.
8. Implement one minimal direct-Python proof using a supported pipeline.
9. Compare direct Python with scripted ComfyUI on quality, speed, VRAM, reliability, metadata, and recoverability.
10. Produce a capability-selection recommendation and record any specialized winners.

## 18. Current hold point

The incomplete evaluation has now been captured as an active workstream. The currently functioning campaign method is preserved as a tested baseline, while the direct-Python path and remaining model/template candidates remain open. Work pauses here until the Steward returns to inspect the actual local scripts, workflows, and model inventory and resumes the matched evaluation.
