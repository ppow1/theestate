# Estate Manual

Status: Engineering and Operations Reference  
Audience: Chief Architect, Alfred operators, engineering workers, documentation workers, local infrastructure workers, and future maintainers.

This manual is not meant to be read cover-to-cover every time. It is the operational reference for how to work inside The Estate.

## 1. Operating Standard

The Estate uses disciplined engineering.

Do not brainstorm endlessly.  
Do not make Pat assemble fragments.  
Do not create new institutions when existing systems can absorb the work.  
Do not treat conversation memory as source of truth.  
Do not edit archived institutional memory.

Prefer:

- Full-file scripts.
- Full-bundle scripts.
- Clear local context pulls.
- Bounded work packages.
- Audit evidence.
- Git history alignment.
- Documentation updates.

## 2. PowerShell Standard

When asking Pat to run local commands, provide complete executable PowerShell blocks.

PowerShell blocks should begin with:

```powershell
Clear-Host

Use cd A:\theestate when operating on the repository.

Do not provide tiny snippets when a full script can perform the task.

Do not ask Pat to manually download or assemble files if PowerShell can create, inspect, or move them locally.

3. Local Source of Truth

ChatGPT cannot directly see A:\theestate.

Local repository state is source of truth.

When uncertain, ask Pat to run a context pull script and paste the output.

Do not assume files exist. Inspect them.

4. Standard Context Pull

Use this when broad repo state is needed:

Clear-Host
cd A:\theestate

Write-Host "=== Estate Repo Status ==="
git status

Write-Host "`n=== Recent Git Log ==="
git --no-pager log --oneline -20

Write-Host "`n=== Root Files ==="
Get-ChildItem -Force | Select-Object Name,Mode,Length,LastWriteTime

Write-Host "`n=== Governance Files ==="
Get-ChildItem "docs\governance" -Recurse -File -ErrorAction SilentlyContinue | Select-Object FullName,Length,LastWriteTime

Write-Host "`n=== Institutional Memory Files ==="
Get-ChildItem "archive\institutional_memory" -Recurse -File -ErrorAction SilentlyContinue | Select-Object FullName,Length,LastWriteTime

Write-Host "`n=== Audit ==="
.\estate.bat audit
5. Audit Command

Run:

Clear-Host
cd A:\theestate
.\estate.bat audit

Audit failures must be explained, not hidden.

A clean audit means:

Runtime checks pass.
JSON checks pass.
Registry checks pass.
Discovery observations pass.
History checks pass.
Git working tree is clean.
6. Discovery Command

Run:

Clear-Host
cd A:\theestate
.\estate.bat discovery-report

Discovery is used before designing or implementing.

Discovery answers what currently exists.

7. Change Process

Every meaningful change should have an Estate Change ID.

The pattern is:

EC-000000 - Short description

A complete change should update:

Code or documents.
Ledger.
Devlog.
Git commit.
Audit state.

The latest git EC should match latest ledger EC.

8. Ledger and Devlog

Ledger path:

estate_ledger\ledger.md

Devlog path:

development\devlog.md

Ledger is formal history.

Devlog is development history.

Keep both aligned.

Do not duplicate EC headings.

Do not skip history repair when git advances beyond ledger.

9. Archive Handling

Archive path:

archive\

Critical origin path:

archive\institutional_memory\Volume_01_Estate_Origins_Executive_Summary.md

Rules:

Do not rewrite archived origin material.
Do not use archive as scratch space.
Preserve historical sources.
Promote durable meaning into living documents.
Keep raw recovery separate from official governance.
10. Memory Promotion

Sort recovered knowledge into:

Institutional Record.
Operational Knowledge.
Historical Context.
Conversation Only.

Only promote durable meaning.

Eleanor owns official records.

Marie enriches and connects meaning.

11. Working as Chief Architect

The Chief Architect:

Maintains architecture.
Prevents scope creep.
Prepares bounded work packages.
Resolves engineering ambiguity.
Interprets Vision and Architecture.
Protects Pat's time.
Coordinates with Alfred.
Prioritizes Discovery and Audit.
Keeps governance lean.
Avoids creating new offices unnecessarily.

Chief Architect should ask:

Can an existing subsystem absorb this?

12. Alfred Operations

Alfred coordinates.

Alfred tasks may produce:

Jobs.
Results.
Events.
Summaries.
Artifacts.
Plans.
Status reports.

Alfred should protect Pat's attention and delegate specialist work.

Alfred is not the whole Estate.

13. Alfred Job Artifacts

Alfred job artifacts live under:

runtime\alfred\jobs\

Typical job artifact files:

result.json
events.json
summary.txt

When debugging Alfred, inspect the command JSON and saved job artifacts. They may have different wrapper shapes.

14. Alfred Audit Contract

Audit validators must match Alfred's current JSON contract.

Do not assume old top-level shapes.

If an Alfred command returns:

top-level wrapper,
execution,
job,
result,
nested results,

then the validator must inspect the correct payload path.

The EC-000083 repair is an example: the code review validator needed to inspect result.results.

15. Discovery Operations

Discovery-related commands may include:

discovery-report
discovery-status
discovery-catalog
discover
discovery-refresh

Discovery should track environment, models, providers, paths, and changes.

Strengthening Discovery is a current priority.

16. Audit Operations

Audit should validate:

Syntax.
Runtime commands.
CLI inventory.
Audit artifact structure.
Capability help.
Service readiness.
Alfred command JSON.
JSON registry validity.
Registry shape.
Discovery observations.
History continuity.
Git cleanliness.

Strengthening Audit is a current priority.

17. Registry Rules

Registry files live under:

data\registry\

Common registry files:

residents.json
services.json
capabilities.json
providers.json

Rules:

Keep valid JSON.
Keep shapes auditable.
Avoid duplicates.
Avoid new registries unless necessary.
Prefer extending existing registries.
18. Governance Documents

Lean governance canon:

AI_HINTS.md
AI_START_HERE.md
docs\governance\Estate_Orientation_Handbook.md
docs\governance\Estate_Vision_and_Architecture.md
docs\governance\Estate_Manual.md
docs\governance\visuals\README.md
Worker packages as needed.

Do not create more governance documents unless a new document has a distinct audience and distinct purpose.

19. Adding an Office

Adding an office requires:

Durable responsibility.
Distinct authority.
Clear relationship to existing offices.
State requirement.
Steward approval.
Documentation.
Registry alignment if implemented.

Do not add a Historian office. Eleanor and Marie already cover official record and meaning.

20. Worker Packages

A worker package must include:

Mission.
Scope.
Do-not-touch boundaries.
Required reading.
Local context script.
Deliverables.
Acceptance criteria.
Definition of done.

Worker packages live under:

docs\governance\workers\

21. Documentation Worker Rules

Documentation workers may improve documents.

They may not invent doctrine casually.

They must avoid turning the Estate into bureaucracy.

If content belongs in an existing document, add it there rather than creating a new file.

22. Local Infrastructure Worker Rules

Local infrastructure workers may inspect:

RTX 4090.
Ollama.
ComfyUI.
Whisper.
TTS.
Music generation.
Lip sync.
Video generation.
Embeddings.
Vector search.

They must not alter governance philosophy or office definitions.

23. Visual Documentation

Visual artifacts live under:

docs\governance\visuals\

Required visuals:

Estate Vision v1.
Current Estate Visual.
Staff Roll Call.

Concept art assets may live under:

assets\concept_art\

24. Local-First Standard

Prefer local execution when practical.

Local-first does not mean cloud-never.

Use cloud intentionally.

Track burn rate, privacy, capability, and reliability.

25. Security and Boundaries

Ingrid owns boundary authority.

Do not send private material outward without considering:

Privacy.
Trust level.
Need.
Public claims.
Legal risk.
Steward intent.

Gray Man and deep Confidant functions require special privacy handling.

26. Counsel Review

Use Counsel thinking when work involves:

Public claims.
Legal exposure.
Contracts.
IP.
Liability.
Sensitive external statements.
27. Comptroller Review

Use Comptroller thinking when work involves:

Token burn.
Cloud cost.
Hardware utilization.
Project spending.
Forecast vs actual.
Unsustainable workflows.
28. Completion Checklist

Before calling work complete:

Files are written.
No snippets are left for Pat to assemble.
Archive is preserved.
Ledger/devlog are updated when needed.
Git commit is made.
Audit is run.
Failures are explained or repaired.
Working tree is clean.
Scope boundaries were respected.
29. Standard Commit Flow
Clear-Host
cd A:\theestate

git status
git add <paths>
git commit -m "EC-000000: description"
.\estate.bat audit
git status
30. Clean Audit Standard

The target state is:

Audit passed.
Failed: 0.
Git working tree clean.
Latest git EC matches latest ledger EC.
Latest ledger EC appears in devlog.

This is the clean handoff checkpoint.
