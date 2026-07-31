# Estate Capability Onboarding Worked Examples

These are designs only. They do not implement Qwen Coder, Whisper, ComfyUI,
Historian, or Legal tooling. They overlay the canonical template and reuse
existing catalog, PTM, Dispatch, receipt, reconciliation, and resident-owner
contracts.

## Qwen Coder / Engineering execution

Capability engineering.repository_implementation@1, target Level 4, owner
Engineering. The worker may be Codex CLI, Qwen Coder, another qualified worker,
or a human. Inputs are immutable Grace action and Engineering commission prompt
records with SHA-256. Reads, writes, artifact, and receipt paths are exact
repository-relative paths. Authority is Grace/Helen/PTM/Engineering/
Operations/Dispatch/final handoff; no merge or institutional-acceptance
authority. Evidence includes qualification, capacity, health, authorization,
freshness, provider receipt, artifact digest, validation, reconciliation, and
Grace terminal evidence. Acceptance is one fresh governed task. Required worker
skills are bounded repository reading, schema/persistence safety, tests,
rollback, and truthful failure reporting.

## Whisper / transcription service

Capability media.transcription@1, target Level 3 or 4, owned by a Speech/Media
resident. Bind the local service and exact model/version. Input is one named
media file with format, size, duration, classification, and digest. Output is a
transcript with language, timestamps, confidence/uncertainty, model identity,
input digest, and receipt digest. Authority is the named input and named output
only: no repository implementation or merge authority. Evidence covers service
health, model presence, capacity, qualification, freshness, cancellation, and
partial transcript state. A Level 4 claim requires governed live acceptance.

## ComfyUI / image generation

Capability media.image_generation@1, target Level 3 or 4, owned by Media.
Bind the existing ComfyUI service manifest and a registered workflow adapter.
Record immutable workflow JSON, node versions, model/checkpoint identity, seed,
parameters, and prompt/reference digests. Output is image plus metadata sidecar
and receipt with create-once paths and hashes. Evidence covers health, GPU/model
availability, node dependencies, capacity, timeout, and cancellation. No
arbitrary model download, hidden network, repository implementation, or
automatic acceptance of generated media is allowed.

## Historian or Legal Expert research tool

Capability research.source_analysis@1, target Level 3 by default, owned by
Historian or Legal Expert. It is read-only and advisory. Inputs are named
sources, retrieval date, source IDs, classification, and for Legal the
jurisdiction/date boundary. Outputs preserve citations, evidence chain,
uncertainty, conflicts, limitations, and receipt; inference never silently
replaces source evidence. PTM/Dispatch are not applicable for a read-only
advisory result only with that rationale recorded. Owner review is not
institutional legal or historical acceptance.

