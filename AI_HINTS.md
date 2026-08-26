# AI_HINTS.md

Status: Fast recovery pointer.

You are working inside The Estate.

Pat is the Steward and final authority.  
Alfred is Chief of Staff. Alfred coordinates the Estate; Alfred is not the whole Estate.

## Fast Recovery

### About to create, modify, repair, integrate, test, deploy, or promote Estate software?

Read completely:

`AI_SOFTWARE_DEVELOPMENT_HINTS.md`

This is the canonical minimum engineering contract for Estate software work. It applies to cloud Codex, ChatGPT, local AI workers, future providers, automation, and human developers. It covers scope discipline, environment identity, Blue/Green/Live/Archive responsibilities, revision and implementation provenance, Diagnostic Impact Packets and first-pass troubleshooting knowledge, local-AI diagnostic review, observer-effect/process-isolated testing, real-boundary acceptance, incoming browser-integrated testing, Git/publication, generated/runtime/secret handling, and minimum completion deliverables.

A work package may impose stricter or additional requirements. It does not silently remove this minimum contract.

### Working on Estate Comms8 or the ChatGPT MCP provider?

Read completely:

`docs/mcp/Estate_Comms8_MCP_App_Repair_and_Correct_Creation_Reference.md`

This is the canonical engineering reference for the Estate Comms8 ChatGPT MCP provider, including the working architecture, authentication boundaries, notification compatibility repair, seven-tool acceptance criteria, correct ChatGPT App configuration, the distinction between workspace publication/enablement and personal Settings → Plugins connection, action refresh order, the corrected Blue tunnel route, the recovered candidate launch context, all three persistent Blue scheduled tasks, and remaining reboot/controller verification boundaries.

Read it before modifying Estate Comms8, the Blue candidate service, ChatGPT Custom Apps, MCP authentication, the seven-tool contract, provider integration, repair work, or functional acceptance packages. For a new App, remember: publish and enable it in workspace Apps administration, then connect it with the token in the individual user's personal **Settings → Plugins**, then refresh and verify all seven actions. If recovery is required, check the Blue candidate-server, notification-proxy, and reverse-tunnel scheduled tasks; require listeners `11808` and `11809`, tunnel route `11808 → 11809`, and public MCP results `200/202/200` with seven tools. Do not repeat investigations or redesign architecture already resolved there. If it conflicts with older work packages or conversation history, treat this reference as authoritative until a newer revision explicitly supersedes it.

### Forgot how Estate communications work?

Read completely:

`AI_COMMUNICATION_HINTS.md`

Use it to decide whether the item belongs in the Parking Lot, a repository-backed message, mailbox discovery, or a governed work package. Do not guess.

### Reached a reflection point or lost continuity procedure?

Read completely:

`AI_REFLECTION_HINTS.md`

Then follow its required reading order. The governing specification is:

`docs/operations/ChatGPT_Worker_Reflection_and_Continuity_Process_v1.md`

Do not claim readiness from filenames, snippets, partial connector output, or incomplete files.

### Need full onboarding or general orientation?

Read:

`AI_START_HERE.md`

### Working with Campaign Runner or governed development packages?

Read before launching, resuming, repairing, debugging, or changing Campaign
Runner, or before using it to implement a governed package:

`docs/operations/Campaign_Runner_Operational_and_Recovery_Guide.md`

It covers package-level self-repair, PostgreSQL durable state, independent
acceptance at the package boundary, main-only Riverview development,
restart/resume, and validator ownership fencing.

### Repository branch authority

**Default authority is `main`. Existing branches are not authorization.**
Before modifying a repository, verify that the work package explicitly
authorizes the current branch. If it does not name another branch, use `main`.

Read:

`docs/operations/Repository_Branch_Authority.md`

### Using multiple AI coding workers or independent adversarial review?

Read before coordinating multiple Codex seats, local coding models, Hermes
workers, or mixed AI engineering roles:

`docs/operations/Multi_Seat_Adversarial_AI_Engineering_Method.md`

## Guardrails

- Do not redesign the Estate merely because context was lost.
- Do not create new offices or departments unless existing systems cannot absorb the work.
- Do not edit archived institutional memory.
- Verify repository state before claiming a repository change is complete.

Critical archived source:

`archive/institutional_memory/Volume_01_Estate_Origins_Executive_Summary.md`
