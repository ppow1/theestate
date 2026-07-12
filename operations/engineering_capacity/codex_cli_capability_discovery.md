# Codex CLI Capability Discovery

Generated: 2026-07-12T00:46:22Z
Provider ID: codex.execution.cli
Codex CLI path: not found
Installed state: not_discovered

## Advertised Capabilities
- repository_implementation
- code_review

## Polling Policy
- Status polling: manual_or_disabled_until_billing_delta_verified
- Automated interval seconds: None
- Rationale: The Estate has no authoritative local counter proving that Codex CLI status checks do not consume quota, tokens, messages, or other limited capacity.

## Boundary
- Metadata-only discovery; no prompts are submitted and no provider work is executed.
- Registry policy: Codex CLI identity and advertised capabilities are owned by config/providers/catalog.json; discovery artifacts may report local metadata but must not mutate catalog status automatically.

## Observations
- {'executed': False, 'reason': 'codex executable not found on PATH'}
