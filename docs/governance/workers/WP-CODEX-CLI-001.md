# WP-CODEX-CLI-001 - Codex CLI Bridge Characterization, Security Policy, and Integration Plan

Status: Proposed
Priority: High
Owner: Chief Architect / Steward
Primary Consumers: Alfred, Ingrid, Helen, future Operations Manager, local workers, Codex workers
Classification: Estate Internal
Created: 2026-07-07

## Mission

Create the plan, policy, and technical characterization required to turn the newly proven Codex CLI bridge into a governed Estate capability.

This work package does not implement the full production bridge.

It produces the investigation, security framing, execution contract recommendations, and implementation plan needed before the Estate routinely allows local workers, Alfred, or an orchestrator to invoke Codex through the command line.

## Background

During the 2026-07-07 Codex CLI discovery session, the Estate proved that a local process can invoke Codex CLI programmatically.

The key proof was:

```text
PowerShell/controller
-> codex exec via stdin
-> Codex result captured in memory
-> Ollama reviews result
-> clean PASS/FAIL returned
```

The session also proved that `/status` inside Codex CLI exposes a usable fuel gauge for authenticated ChatGPT Business seat usage.

The discovery is captured in:

```text
observations/codex_cli_bridge_discovery_2026-07-07.md
```

This capability arrived earlier than expected and creates both an opportunity and a governance concern.

Opportunity:

```text
Codex can become an Estate-managed execution provider instead of a browser-operated tool requiring Steward copy/paste.
```

Concern:

```text
Codex was given direct access to A:\theestate before Ingrid had defined a formal boundary policy for what Codex may read, write, receive, or return.
```

## Strategic Context

The Estate is moving toward a planning/orchestration/execution architecture.

The planning layer creates work packages, specifications, acceptance criteria, policies, and dependency information.

The orchestration layer decides when, where, by whom, and under what budget/security constraints work is executed.

The execution layer performs assigned work through providers such as:

- Codex CLI
- Codex Cloud
- Ollama/local LLMs
- PowerShell
- Python
- GitHub
- future local services

This work package prepares Codex CLI to become one execution provider in that architecture.

## Scope

This package covers:

1. Codex CLI capability characterization.
2. ChatGPT-authenticated CLI usage and account identity behavior.
3. `codex exec` stdin/stdout behavior.
4. `/status` fuel gauge behavior.
5. `codex cloud` command characterization.
6. Multi-seat `CODEX_HOME` profile investigation.
7. Encoding and terminal-control cleanup requirements.
8. Ingrid/security boundary requirements.
9. Helen/worker provisioning implications.
10. Relationship to Alfred and a future orchestrator.
11. Relationship to the future local execution/application execution protocol.
12. Recommended implementation plan for a production Codex Bridge service.

## Out of Scope

This package does not:

- Build the full production bridge.
- Modify Alfred runtime.
- Modify Ingrid runtime.
- Modify Helen runtime.
- Create the full orchestrator.
- Decide all future office/department hierarchy changes.
- Create permanent background services.
- Grant unrestricted Codex access as a permanent pattern.

## Required Reading

Before executing this package, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Orientation_Handbook.md
docs/governance/Estate_Vision_and_Architecture.md
docs/governance/Estate_Manual.md
observations/codex_cli_bridge_discovery_2026-07-07.md
operations/boards/parking_lot.md
```

Relevant Parking Lot items:

```text
PL-0014 - External Worker Telemetry Adapter
PL-0016 - Parallel Worker Orchestration
PL-0025 - Role/task security classification should determine onboarding depth
```

## Do-Not-Touch Boundaries

Do not alter archived institutional memory.

Do not implement unrestricted autonomous Codex execution.

Do not treat Codex CLI as approved for routine production use until Ingrid boundary review is addressed.

Do not collapse Alfred, Helen, Ingrid, and Operations into a single responsibility.

Do not create new offices casually. If an Operations Manager or equivalent role appears necessary, document it as a recommendation for Steward review rather than implementing it directly.

Do not assume GitHub is the only source of truth. Local repo state remains source of truth during local execution, while GitHub remains the current shared transport and institutional persistence layer.

## Key Questions To Answer

### Codex CLI Capability

- What can `codex exec` reliably do non-interactively?
- What output formats are available?
- Can output be made JSON or otherwise structured?
- Can token usage be captured reliably?
- Can `codex exec` run with read-only, workspace-write, or other permission modes?
- How does approval policy affect automation?
- How does sandboxing behave under different modes?

### Fuel Gauge

- Can `/status` output be captured non-interactively, or only through interactive TUI?
- Is there another command that exposes equivalent usage data?
- Can usage be parsed per seat?
- Does context-window usage matter for orchestration decisions?
- Can reset times be parsed reliably?

### Cloud Tasks

- Can `codex cloud exec` submit tasks from a script?
- What does `codex cloud list` show for tasks created by CLI?
- What identifier is returned for submitted tasks?
- Can `codex cloud status` be polled reliably?
- Can `codex cloud diff` retrieve useful output?
- Can `codex cloud apply` safely apply changes locally?
- Does cloud-task state map to browser Codex state?

### Multi-Seat Operation

- Can separate `CODEX_HOME` folders isolate three Business seats?
- Can each seat maintain a separate `auth.json`?
- Can three seats run concurrently in separate shells or services?
- If concurrent use is unreliable, what is the safe sequential seat-burn fallback?
- How should the Estate identify which seat is active?

### Security and Boundary

- What should Codex be allowed to read by default?
- What should Codex be allowed to write by default?
- Which task classifications require Ingrid review before dispatch?
- Which repository areas are safe for Codex access?
- Which repository areas require read-only or no access?
- How should outputs from Codex be classified before promotion back into the Estate?
- What logging is required so Ingrid can audit what crossed the boundary?

### Local Execution Protocol / Adapter Layer

- What should a generic execution provider contract look like?
- What minimum methods are needed?
  - submit
  - status
  - cancel
  - result
  - capabilities
  - health
  - estimate_cost
  - estimate_time
- How should Codex CLI map onto that contract?
- How should Ollama/local LLMs map onto that contract?
- What parts belong in the future local execution/application execution protocol rather than the Codex adapter?

### Planning and Orchestration

- What does the planning layer need to include in a work package so an orchestrator can route it?
- What fields are needed for model/provider selection?
  - required capability
  - quality tier
  - security classification
  - expected duration
  - budget priority
  - latency priority
  - required tools
  - allowed providers
  - forbidden providers
  - acceptance criteria
- What belongs to Chief Architects and Character Development Engineers at planning time?
- What belongs to Alfred or the orchestrator at scheduling time?
- What belongs to Helen/HR at worker provisioning time?
- What belongs to Ingrid at boundary review time?

## Required Investigation Tasks

1. Reproduce the direct pipe test from the discovery session.
2. Capture clean output from `codex exec` into a variable.
3. Capture token-usage output or determine whether it is only printed outside stdout.
4. Test `codex exec --json` or equivalent JSONL mode if available.
5. Test `codex exec` with a file-backed work package prompt.
6. Test output cleanup for ANSI/control characters.
7. Test encoding normalization for apostrophes and other UTF-8 characters.
8. Test whether `CODEX_HOME` can isolate multiple account profiles.
9. Test one safe `codex cloud exec` task if acceptable.
10. Test `codex cloud list`, `status`, `diff`, and `apply` on a harmless task.
11. Determine whether `/status` can be automated or needs TUI observation.
12. Produce a security matrix for Codex read/write boundaries.
13. Produce a recommended minimal bridge architecture.
14. Produce a recommended follow-up implementation work package.

## Expected Deliverables

### 1. Capability Matrix

Create a document summarizing what Codex CLI can and cannot do for Estate use.

Suggested path:

```text
docs/integration/codex_cli_capability_matrix.md
```

### 2. Security Boundary Draft

Create a draft Codex boundary policy for Ingrid review.

Suggested path:

```text
docs/security/codex_cli_boundary_policy_draft.md
```

### 3. Execution Provider Mapping

Create a mapping from generic execution-provider concepts to Codex CLI commands.

Suggested path:

```text
docs/architecture/execution_provider_codex_cli_mapping.md
```

### 4. Bridge Prototype Notes

Document the tested commands, results, observed issues, and recommended wrapper behavior.

Suggested path:

```text
observations/codex_cli_bridge_characterization_results.md
```

### 5. Follow-Up Implementation Package

Create a recommended implementation work package for the production bridge.

Suggested path:

```text
docs/governance/workers/WP-CODEX-BRIDGE-IMPLEMENTATION.md
```

## Acceptance Criteria

This work package is complete when:

- The 2026-07-07 discovery has been translated into a clear Codex CLI capability matrix.
- Ingrid/security concerns are explicitly documented.
- The Estate has a recommended policy for what Codex may read/write.
- The Estate has a recommended bridge/service contract.
- Multi-seat behavior has been tested or clearly marked as unresolved.
- Fuel-gauge behavior has been tested or clearly marked as unresolved.
- Cloud commands have been characterized or explicitly deferred.
- A follow-up implementation package exists.
- The result is committed to GitHub for local pull-down into `A:\theestate`.

## Definition of Done

- Required deliverables exist in the repository.
- Findings are specific, not speculative.
- Unknowns are clearly marked.
- Security concerns are not buried.
- Recommendations distinguish between immediate safe use, experimental use, and prohibited/unapproved use.
- The package produces a plan that can be handed to Codex or a local worker without relying on conversation memory.

## Initial Recommendation

The first production bridge should be conservative.

Recommended first version:

```text
A local wrapper that reads a work package, builds a deterministic prompt, invokes codex exec, captures stdout, normalizes output, writes an audit log, and returns a structured result.
```

It should not initially:

```text
Run unrestricted against the entire Estate.
Auto-apply changes.
Bypass Ingrid/security review.
Use API-key billing.
Assume multi-seat concurrency until proven.
```

## Open Institutional Question

The session raised a possible hierarchy issue.

Alfred currently occupies Chief of Staff and may be acting as both governance coordinator and orchestrator.

Helen/HR controls worker hiring/provisioning.

Ingrid controls boundaries.

There may be a missing Operations Manager or Operations Office layer between Alfred and execution workers, responsible for day-to-day scheduling, queue movement, provider selection, and execution routing.

This work package should document the need if confirmed, but not create the office without Steward approval.
