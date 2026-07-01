dependencies: []

# Capability Registry Metadata Cleanup

Status: Implementation Documentation  
Classification: Estate Internal

## Purpose

This note records the metadata cleanup applied to `data/registry/capabilities.json` so existing lifecycle, dependency, and operational validation reports can produce more useful advisory output.

The cleanup is data hygiene only. It does not redefine lifecycle states, promotion authority, governance meaning, offices, or audit authority.

## Field Meanings Used

- `lifecycle_state`: one of the official Estate lifecycle states from `docs/governance/Capability_Lifecycle_States_v1.md`.
- `implementation_references`: repository evidence or preserved implementation context showing where the capability is implemented or recorded.
- `evidence_references`: repository-relative artifacts that support the capability entry and assigned lifecycle state.
- `operational_evidence_references`: evidence that would support an `Operationally Validated` claim. This cleanup leaves the field empty where no clear operational validation evidence exists.
- `institutionalization_references`: evidence that would support an `Institutionalized` claim. This cleanup leaves the field empty where no governance adoption evidence exists.
- `dependencies`: explicit capability dependencies only. Empty arrays mean no explicit dependency was found or asserted.
- `related_services`: explicit service relationships only. Empty arrays mean no service registry identifier was defensibly linked.

## Lifecycle Assignment Rules

The cleanup uses only these official lifecycle states:

- `Designed`
- `Implemented`
- `Operationally Validated`
- `Institutionalized`

Existing local tools or installed capabilities with repository evidence were assigned `Implemented` when no clear operational validation evidence was present.

Whisper remains `Designed` because the registry records it as `Pending Install` and the service catalog describes direct transcription execution as future work.

No capability was promoted to `Operationally Validated` or `Institutionalized` because that would require stronger operational or governance evidence than this data cleanup found.

## Evidence Rules

Evidence references were limited to existing repository artifacts, including:

- the capability registry history in `estate_ledger/ledger.md` and `development/devlog.md`
- service catalog documentation in `docs/service_catalog.md`
- local environment observation artifacts under `observations/`
- root context where applicable

Local absolute paths already present in the registry were preserved as implementation context, not treated as repository evidence.

## Limitations

- Dependencies remain empty because the dependency graph should stay explicit-only and this cleanup did not find defensible registry identifiers to connect.
- `related_services` remains empty because the existing service registry contains institutional services rather than direct image, speech, compute, or media service IDs.
- Operational validation evidence remains empty pending separate review or workflow evidence.
