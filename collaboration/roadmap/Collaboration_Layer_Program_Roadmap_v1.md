# Collaboration Layer Program Roadmap v1

Status: Operational Planning Artifact
Classification: Estate Internal
Owner: Alfred / Chief of Staff
Architectural Oversight: Office of the Chief Architect

## Purpose

This roadmap converts the next functional worker tasks into a durable program plan for the Collaboration Layer.

The Daily Board tracks current operational work. This roadmap tracks planned capability advancement and provides the source from which work packages should be promoted, assigned, launched, audited, and completed.

## Planning Fields

Each roadmap item should include:

- Work Package ID
- Title
- Worker Type
- Capability Advanced
- Current Lifecycle State
- Target Lifecycle State
- Capability Gained
- Dependencies
- Required Inputs
- Expected Outputs
- Evidence Produced
- Validation Method
- Steward Cognitive Load Reduction
- Institutional Leverage
- Execution Profile
- Why This Is Next
- Risks / Constraints
- Status

## Scoring

### Steward Cognitive Load Reduction

1 = Negligible
2 = Small convenience
3 = Noticeable reduction
4 = Major operational leverage
5 = Eliminates a recurring manual Steward responsibility

### Institutional Leverage

1 = Local improvement
2 = Single subsystem
3 = Multiple subsystems
4 = Estate-wide infrastructure
5 = Foundational capability enabling many later capabilities

## Execution Profile Fields

- Preferred Worker Class
- Preferred Execution Environment
- Recommended Current Model
- Minimum Capability
- Execution Complexity
- Estimated Runtime
- Human Review Required
- Notes

Execution Complexity:

1 = Routine automation
2 = Simple documentation
3 = Multi-file implementation
4 = Architectural reasoning
5 = Constitutional or strategic reasoning

## Roadmap Items

### WP-0003 — Local Worker Launch Validation

Worker Type: Worker Launch Validation Worker

Capability Advanced: Worker Launch

Current Lifecycle State: Implemented

Target Lifecycle State: Operationally Validated

Capability Gained: Proves workers can execute real work packages locally.

Dependencies:
- Worker Runtime Contract
- Work Package Lifecycle

Required Inputs:
- Existing launcher
- Sample or real work package

Expected Outputs:
- Successful execution record
- Status report
- Validation evidence

Evidence Produced:
- Launch request archived
- Result JSON
- Clean transcript
- Git commit showing request/result preservation

Validation Method:
Independent local execution completes without GitHub interaction during worker runtime.

Steward Cognitive Load Reduction: 5

Institutional Leverage: 5

Execution Profile:
- Preferred Worker Class: Worker Launch Validation Worker
- Preferred Execution Environment: Local Ollama
- Recommended Current Model: qwen2.5-coder:7b
- Minimum Capability: Follow structured prompts and summarize execution evidence
- Execution Complexity: 3
- Estimated Runtime: 5–15 minutes
- Human Review Required: Yes

Why This Is Next:
The Estate gains nothing from architecture that cannot launch workers successfully.

Risks / Constraints:
Must remain local-first.

Status: Planned

---

### WP-0001 — Communication Bus Local Operations

Worker Type: Collaboration Infrastructure Worker

Capability Advanced: Communication Bus (Local)

Current Lifecycle State: Implemented → Operational Validation Pending

Target Lifecycle State: Operationally Validated

Capability Gained: Workers exchange messages locally without the Steward acting as the transport layer.

Dependencies:
- Collaboration Layer v1
- Worker Runtime Contract
- Instruction Precedence
- Local filesystem transport

Required Inputs:
- Existing collaboration directory
- Message templates
- Runtime contract
- Current communication artifacts

Expected Outputs:
- Validated message envelope
- Local inbox/outbox conventions
- Example worker conversations
- Operational documentation

Evidence Produced:
- Two-worker message exchange
- Message files preserved
- Status files showing receipt and response
- Audit or review note confirming no manual relay

Validation Method:
Independent workers exchange work messages exclusively through the Communication Bus without manual conversational relay.

Steward Cognitive Load Reduction: 5

Institutional Leverage: 5

Execution Profile:
- Preferred Worker Class: Collaboration Infrastructure Worker
- Preferred Execution Environment: ChatGPT for design review; Local Ollama for file implementation
- Recommended Current Model: qwen2.5-coder:7b for local implementation
- Minimum Capability: Multi-file documentation and schema reasoning
- Execution Complexity: 4
- Estimated Runtime: 20–45 minutes
- Human Review Required: Yes

Why This Is Next:
Every future capability depends on reliable worker-to-worker communication.

Risks / Constraints:
Do not redesign the Collaboration Layer architecture. GitHub remains a transport adapter, not the communication bus.

Status: Planned

---

### WP-0002 — Worker Claim & Status Lifecycle

Worker Type: Operations Worker

Capability Advanced: Work Package Lifecycle

Current Lifecycle State: Implemented

Target Lifecycle State: Operationally Validated

Capability Gained: Workers can safely coordinate ownership and execution state.

Dependencies:
- Communication Bus
- Collaboration Layer

Required Inputs:
- Work package templates
- Status schema

Expected Outputs:
- Claim records
- Status transitions
- Lifecycle documentation

Evidence Produced:
- Claim files
- Status transition examples
- Multi-worker non-conflict test

Validation Method:
Multiple workers successfully claim, execute, and complete work without conflicting ownership.

Steward Cognitive Load Reduction: 4

Institutional Leverage: 5

Execution Profile:
- Preferred Worker Class: Operations Worker
- Preferred Execution Environment: Local Ollama
- Recommended Current Model: qwen2.5-coder:7b
- Minimum Capability: Schema editing and state-machine reasoning
- Execution Complexity: 3
- Estimated Runtime: 20–40 minutes
- Human Review Required: Yes

Why This Is Next:
Communication without ownership still creates collisions.

Risks / Constraints:
Maintain existing lifecycle states; extend, do not replace.

Status: Planned

---

### WP-0004 — Collaboration Audit Validation

Worker Type: Audit Worker

Capability Advanced: Collaboration Audit

Current Lifecycle State: Implemented

Target Lifecycle State: Operationally Validated

Capability Gained: Automatic validation of collaboration artifacts.

Dependencies:
- Communication Bus
- Work Package Lifecycle

Required Inputs:
- Message schema
- Status schema
- Existing Audit Worker v1

Expected Outputs:
- Audit checks
- Validation report
- Failure classifications

Evidence Produced:
- Known-valid artifacts pass
- Malformed artifacts fail
- Audit result JSON
- Failure classification examples

Validation Method:
Known-valid artifacts pass; malformed artifacts fail.

Steward Cognitive Load Reduction: 4

Institutional Leverage: 5

Execution Profile:
- Preferred Worker Class: Audit Worker
- Preferred Execution Environment: Local PowerShell plus Local Ollama for interpretation if needed
- Recommended Current Model: qwen2.5-coder:7b for implementation assistance
- Minimum Capability: Script validation and schema inspection
- Execution Complexity: 3
- Estimated Runtime: 20–45 minutes
- Human Review Required: Yes

Why This Is Next:
Without Audit, communication becomes trust-based rather than evidence-based.

Risks / Constraints:
Audit validates structure and evidence, not architectural merit.

Status: Planned

---

### WP-0009 — History Queue Operational Validation

Worker Type: History Worker

Capability Advanced: History Queue

Current Lifecycle State: Implemented

Target Lifecycle State: Operationally Validated

Capability Gained: Verified promotion into institutional history.

Dependencies:
- Audit
- Promotion workflow

Required Inputs:
- Completed work artifacts
- Existing history queue/drain materials

Expected Outputs:
- Validated history entries
- Reconciliation evidence

Evidence Produced:
- Pending history request
- Drain result
- Updated institutional history
- Audit reference

Validation Method:
History is updated through the approved workflow.

Steward Cognitive Load Reduction: 4

Institutional Leverage: 5

Execution Profile:
- Preferred Worker Class: History Worker
- Preferred Execution Environment: ChatGPT for review; Local execution for drain script
- Recommended Current Model: qwen2.5-coder:7b for local script support
- Minimum Capability: High-integrity document reconciliation
- Execution Complexity: 4
- Estimated Runtime: 30–60 minutes
- Human Review Required: Yes

Why This Is Next:
Institutional memory should advance through evidence, not manual edits.

Risks / Constraints:
Preserve history integrity. Routine workers must not directly edit ledger/devlog.

Status: Planned

---

### WP-0005 — Discovery Collaboration Observation

Worker Type: Discovery Worker

Capability Advanced: Discovery

Current Lifecycle State: Implemented

Target Lifecycle State: Operationally Validated

Capability Gained: Operational visibility into active collaboration.

Dependencies:
- Work lifecycle
- Communication Bus

Required Inputs:
- Collaboration state
- Status files

Expected Outputs:
- Discovery report
- Active work inventory

Evidence Produced:
- Discovery output matching current repository state
- Comparison against known active work

Validation Method:
Discovery accurately reflects current collaboration state.

Steward Cognitive Load Reduction: 4

Institutional Leverage: 4

Execution Profile:
- Preferred Worker Class: Discovery Worker
- Preferred Execution Environment: Local Ollama or script-first local worker
- Recommended Current Model: llama3.2:3b for summary; qwen2.5-coder:7b for script work
- Minimum Capability: File inventory and summarization
- Execution Complexity: 2
- Estimated Runtime: 10–30 minutes
- Human Review Required: Yes

Why This Is Next:
The Estate should answer what is happening now without manual investigation.

Risks / Constraints:
Observation only; no routing or modification.

Status: Planned

---

### WP-0006 — Operations Board Automation

Worker Type: Operations Worker

Capability Advanced: Operations Board

Current Lifecycle State: Implemented

Target Lifecycle State: Operationally Validated

Capability Gained: Unified operational visibility.

Dependencies:
- Discovery
- Audit
- Worker status

Required Inputs:
- Collaboration status
- Discovery outputs

Expected Outputs:
- Updated Operations Board

Evidence Produced:
- Board update
- Source references to collaboration artifacts
- Steward review confirmation

Validation Method:
Board reflects actual operational state.

Steward Cognitive Load Reduction: 4

Institutional Leverage: 4

Execution Profile:
- Preferred Worker Class: Operations Worker
- Preferred Execution Environment: Local Ollama
- Recommended Current Model: llama3.2:3b for routine board updates; qwen2.5-coder:7b for automation edits
- Minimum Capability: Summarization and structured status update
- Execution Complexity: 2
- Estimated Runtime: 10–25 minutes
- Human Review Required: Yes initially; may reduce after validation

Why This Is Next:
Provides one authoritative operational view for the Steward and architects.

Risks / Constraints:
Board summarizes state; it does not become a new system of record.

Status: Planned

---

### WP-0007 — Parking Lot Operational Workflow

Worker Type: Governance Support Worker

Capability Advanced: Parking Lot

Current Lifecycle State: Implemented

Target Lifecycle State: Operationally Validated

Capability Gained: Controlled capture of future ideas without scope creep.

Dependencies:
- Operations Board v1

Required Inputs:
- Current Parking Lot

Expected Outputs:
- Operational intake and review process

Evidence Produced:
- Captured parking item
- Review disposition
- No unauthorized work package created

Validation Method:
Ideas are captured and execution remains focused.

Steward Cognitive Load Reduction: 3

Institutional Leverage: 3

Execution Profile:
- Preferred Worker Class: Governance Support Worker
- Preferred Execution Environment: ChatGPT or Local Ollama
- Recommended Current Model: llama3.2:3b for routine capture; ChatGPT for policy judgment
- Minimum Capability: Classification and concise documentation
- Execution Complexity: 2
- Estimated Runtime: 10–20 minutes
- Human Review Required: Yes

Why This Is Next:
Supports disciplined execution as worker throughput increases.

Risks / Constraints:
Must never become implicit authorization.

Status: Planned

---

### WP-0008 — Local Adapter Extension Validation

Worker Type: Integration Worker

Capability Advanced: Local Adapter Extension Protocol

Current Lifecycle State: Designed

Target Lifecycle State: Implemented

Capability Gained: Repeatable adapter development process.

Dependencies:
- Communication Bus
- Worker Launch Adapter
- Audit Worker

Required Inputs:
- Existing adapter architecture

Expected Outputs:
- Validated protocol
- Reference adapter

Evidence Produced:
- Adapter request
- Adapter implementation
- Validation result

Validation Method:
A new adapter can be created using the protocol.

Steward Cognitive Load Reduction: 3

Institutional Leverage: 4

Execution Profile:
- Preferred Worker Class: Integration Worker
- Preferred Execution Environment: ChatGPT for design; Local Ollama for implementation
- Recommended Current Model: qwen2.5-coder:7b
- Minimum Capability: Multi-file implementation and protocol reasoning
- Execution Complexity: 4
- Estimated Runtime: 45–90 minutes
- Human Review Required: Yes

Why This Is Next:
Protects architectural consistency as transports expand.

Risks / Constraints:
Adapters must remain subordinate to institutional governance.

Status: Planned

---

### WP-0010 — Capability Lifecycle Dashboard

Worker Type: Documentation Worker

Capability Advanced: Capability Lifecycle Management

Current Lifecycle State: Designed

Target Lifecycle State: Implemented

Capability Gained: Institution-wide maturity visibility.

Dependencies:
- Capability owners
- Operational evidence

Required Inputs:
- Capability inventory
- Lifecycle standard

Expected Outputs:
- Lifecycle dashboard

Evidence Produced:
- Capability inventory
- Maturity mapping
- Evidence links

Validation Method:
Capabilities map consistently to Estate lifecycle states.

Steward Cognitive Load Reduction: 3

Institutional Leverage: 3

Execution Profile:
- Preferred Worker Class: Documentation Worker
- Preferred Execution Environment: Local Ollama
- Recommended Current Model: llama3.2:3b
- Minimum Capability: Structured summarization
- Execution Complexity: 2
- Estimated Runtime: 20–40 minutes
- Human Review Required: Yes

Why This Is Next:
Allows future planning based on evidence rather than intuition.

Risks / Constraints:
Lifecycle states must reflect operational evidence, not aspiration.

Status: Planned
