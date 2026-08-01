# Steward Cheat Sheet — Current Capabilities

Generated: 2026-08-01T22:28:08Z

This is a read-only current-state view. Help never executes a Skill or grants authority.

## What is operational now

- **Grace** (`grace`): Sequences approved operational movement, dependencies, checkpoints, and governed Dispatch handoffs without provider execution or authority expansion.
- **Helen** (`helen`): Capability, qualification, availability, capacity, and gap assessment.
- **Estate Skills framework** (`estate-skills`): Canonical versioned governed procedure registry and read-only discovery.
- **Open WebUI / Grace / Resident Gateway** (`openwebui-estate-path`): Canonical authenticated Open WebUI path through Grace runtime and the Resident Gateway.

## What requires authorization

- **Engineering** (`engineering`): Bounded repository implementation, review, documentation, test execution, technical intake, validation, reconciliation, and truthful failure evidence. Block: each request needs current authority, scope, worker, provider, and readiness.
- **qwen.local.text** (`qwen.local.text`): Loopback Qwen-family text generation and bounded repository reads. Block: fresh loopback reachability is present, but governed authorization and validation remain required.
- **Repository Health** (`repository-health`): Inspect repository and worktree health without changing repository state. Block: explicit execution authority is still required.
- **Capability onboarding framework** (`capability-onboarding`): Existing capability/provider registration and Grace/Helen/Engineering readiness path. Block: capability-specific evidence may be stale or missing.

## What is registered but unavailable

- **ComfyUI** (`comfyui.local.image`): Local image workflow preparation and governed submission. Block: fresh health/capacity and separate live submission authorization are required.
- **Qwen Coder** (`qwen-coder`): Observed Qwen coder model record; no current formal routing or fresh dispatch evidence is claimed. Block: observed model record is historical and formal routing policy is pending.

## What is temporarily unavailable

- **codex.execution.cli** (`codex.execution.cli`): Bounded Codex CLI execution with declared workspace and outputs. Block: provider health is stale/offline; provider catalog does not grant execution authority.

## Capability gaps

- **Whisper** (`CAP-000006`): Planned local speech-to-text capability for speech transcription workflows. Block: registry says Pending Install; no current operational provider evidence.

## What is planned

- None proven in the current snapshot.

## Common things the Steward can say

- Grace, help.
- Grace, what can we do?
- Grace, show my commands.
- Grace, what Skills are available?
- Grace, use the Check Git Skill and report only.
- Helen, do we have a governed transcription capability?
- Grace, prepare a proposal before execution.

## Known limits

- Catalog registration, installation, historical success, or a passing test does not prove current dispatchability.
- Help and discovery never execute providers, Skills, repository changes, merges, deletions, purchases, external messages, or acceptance actions.
- Fresh authority, worker, provider health/capacity, PTM/readiness, and validation remain request-specific.

## Institutional acceptance

- `not_granted`; this surface never infers acceptance.

## Sources

- data/registry/capabilities.json — sha256 `17894e0eaa0b17bdad4c9739975cb6abf637bf8b872ce4456e52f095ebbf8428`
- data/registry/providers.json — sha256 `0fa5ce443b21a7234840d5903fa27a6848d79f71babcd9336e4aa93aa7e0d57a`
- data/registry/residents.json — sha256 `41f68cefe49232133229955a4b8728859f2af481c95d33d7a93c2fb1b22333fe`
- config/providers/catalog.json — sha256 `045ceed06484e92b7218a01948624e7d08a356a421c264f4e7900fdc0b4b0c79`
- config/skills/estate_skill_registry.json — sha256 `3efca58be115c3826172ebd04a48205566d6e97c19664a473cf765a76ef80490`
- runtime/residents/helen/readiness.json — sha256 `6dc8c3ea64a8e01fab2fffc1bf71088a3e9877db837b3d93f2c2a66cbde6df52`
- runtime/providers/health/status/latest.json — sha256 `f103845f37bf25c50e27d1919bdd3731a3c402b6cbf5d2e3c62d0cbe7a9e52a5`
- runtime/provider_health/providers/codex_cli_openai.json — sha256 `2475327de11ab76a5b8d3aae522e363f9f054b9609d24805daab115d05647410`
- runtime/ai_services/implementations/comfyui/service.manifest.json — sha256 `ddc5c23dbc196d06418849016e8539beb2d4b42bcc8a7b453fa5736051a346a6`
- config/runtime/canonical_webui_gateway.json — sha256 `984d7343d89af8370e0fb1d30ee507a7c34d5d11ca9808ac9673b8d33e2ed065`
