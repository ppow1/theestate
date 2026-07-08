# Provider Registration and Capability Discovery

Status: Implemented  
Classification: Estate Internal

## Purpose

The provider catalog is the shared Estate registry for provider identity and capability discovery. It describes what a provider can do without implementing execution, scheduling, live network calls, or Office UI behavior.

## Provider Descriptor Model

Descriptors live in `config/providers/catalog.json` and include required identity, type, implementation kind, lifecycle status, classification ceiling, and capability IDs. Optional fields describe context classes, boundary review, event/artifact/validation support, offline/network behavior, cost model, routing notes, limitations, and metadata.

Allowed provider types are `planning`, `execution`, `validation`, `documentation`, `research`, `classification`, `media`, `infrastructure`, and `mixed`. Allowed implementation kinds are `chatgpt`, `codex`, `local_llm`, `python`, `powershell`, `github_actions`, `manual`, `future`, `stub`, and `other`.

## Capability Model

Capabilities define `capability_id`, `display_name`, and `category`, with optional descriptions, input/output artifact lists, approval/validation/offline flags, and metadata. Capability IDs are extensible; new capabilities must still satisfy required fields.

## Catalog Path

The static catalog path is:

```text
config/providers/catalog.json
```

The Python loader is `estate.core.provider_catalog.load_provider_catalog()`.

## CLI Examples

```powershell
Clear-Host
cd A:\theestate
.\estate.bat providers-list
.\estate.bat providers-show --provider-id chatgpt.planning.external
.\estate.bat providers-find --capability work_package_draft
```

Each command supports `--json`.

## Office Export Path

The Office-readable status artifact is written to:

```text
runtime/providers/catalog_status.json
```

It contains provider counts, providers by type/status, available capabilities, and safe provider descriptors with routing notes and limitations omitted.

## Planning Provider Integration Notes

WP-0600's planning provider registry can use the catalog as its descriptor source. The existing local stub provider is represented by `stub.planning.echo`; execution remains in the planning provider framework.

## Orchestrator Intake Integration Notes

WP-0603 intake requests can use `requested_provider_type`, `requested_provider_id`, and `required_capabilities` values from this catalog. Future scheduling should call catalog lookup/filter helpers rather than duplicating provider lists.

## Boundary Notes

Unknown provider types, implementation kinds, statuses, classification ceilings, missing provider IDs, and malformed capability objects fail validation. The catalog rejects descriptors containing common secret markers and must not contain credentials, tokens, private prompts, or live service secrets.

## Adding Future Providers

1. Add capability objects if new capability IDs are needed.
2. Add a provider descriptor referencing existing or newly added capability IDs.
3. Run the provider catalog tests and CLI list/show/find commands.
4. Regenerate `runtime/providers/catalog_status.json`.
