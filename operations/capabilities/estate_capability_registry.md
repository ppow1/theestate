# Estate Capability Registry

Generated: 2026-07-04T12:22:41+00:00

Read-only aggregation. This report is not the source of truth.

## Summary
- Capabilities: 6
- Providers: 6
- Services: 3
- Warnings: 1

## Capabilities

### RTX 4090 CUDA (CAP-000001)
- Owning subsystem: Administration
- Implementation status: Operational
- Maturity: partial
- Dependencies: None
- Validation status: evidence_found
- Providers: None
- Source artifacts: data/registry/capabilities.json, Local AI Workstation, A:\AI, observations/ai_environment_2026-06-29_23-47-42.json, estate_ledger/ledger.md, development/devlog.md, docs/service_catalog.md, README.md, runtime/validation/operational_validation_report.json

### Kokoro TTS (CAP-000002)
- Owning subsystem: Administration
- Implementation status: Operational
- Maturity: partial
- Dependencies: None
- Validation status: evidence_found
- Providers: Kokoro Provider
- Source artifacts: data/registry/capabilities.json, A:\AI\TTS, observations/ai_environment_2026-06-29_23-47-42.json, estate_ledger/ledger.md, development/devlog.md, docs/service_catalog.md, runtime/validation/operational_validation_report.json

### F5-TTS (CAP-000003)
- Owning subsystem: Administration
- Implementation status: Operational
- Maturity: partial
- Dependencies: None
- Validation status: evidence_found
- Providers: F5-TTS Provider
- Source artifacts: data/registry/capabilities.json, A:\AI\TTS\F5-TTS, observations/ai_environment_2026-06-29_23-47-42.json, estate_ledger/ledger.md, development/devlog.md, docs/service_catalog.md, runtime/validation/operational_validation_report.json

### ComfyUI (CAP-000004)
- Owning subsystem: Administration
- Implementation status: Installed
- Maturity: partial
- Dependencies: None
- Validation status: evidence_found
- Providers: ComfyUI Provider
- Source artifacts: data/registry/capabilities.json, A:\AI\ComfyUI, observations/ai_environment_2026-06-29_23-47-42.json, estate_ledger/ledger.md, development/devlog.md, docs/service_catalog.md, runtime/validation/operational_validation_report.json

### FFmpeg / FFplay (CAP-000005)
- Owning subsystem: Administration
- Implementation status: Operational
- Maturity: partial
- Dependencies: None
- Validation status: evidence_found
- Providers: None
- Source artifacts: data/registry/capabilities.json, A:\AI\Tools\FFmpeg, observations/ai_environment_2026-06-29_23-47-42.json, estate_ledger/ledger.md, development/devlog.md, docs/service_catalog.md, runtime/validation/operational_validation_report.json

### Whisper (CAP-000006)
- Owning subsystem: Administration
- Implementation status: Pending Install
- Maturity: planned
- Dependencies: None
- Validation status: evidence_found
- Providers: Whisper Provider
- Source artifacts: data/registry/capabilities.json, A:\AI, estate_ledger/ledger.md, development/devlog.md, docs/service_catalog.md, observations/ai_environment_2026-06-29_23-47-42.json, runtime/validation/operational_validation_report.json

## Warnings
- provider_without_capability_record: Providers reference capabilities not present in data/registry/capabilities.json.
