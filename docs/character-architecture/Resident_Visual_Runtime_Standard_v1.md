# Resident Visual Runtime Standard v1

Status: Active implementation standard  
Campaign: Resident Visual Runtime  
Work packages: WP-4073 through WP-4082

## Purpose

The Estate visual runtime preserves resident visual identity without creating a duplicate asset system. It stores canonical manifests for identity, wardrobe, locations, presentation poses, continuity, gallery entries, portrait selection, archive records, scene generation contracts, and timeline events under `data/visuals/`.

## Runtime Rules

1. Resident visual identity records must resolve to the canonical resident registry.
2. Wardrobe, location, and pose identifiers are reusable references, not generated assets.
3. Gallery entries must reference canonical residents, wardrobe items, locations, poses, and repository or runtime asset paths.
4. Portrait records are management records that point back to gallery entries.
5. Historical visual changes require archive and timeline evidence.
6. Restricted residents may have index records, but private material must not be exposed as public gallery content.
7. Dynamic scene generation uses prompt contracts and reference identifiers; it does not approve final images by itself.

## Validation

The runtime validator is `estate.core.visual_runtime.validate_visual_runtime`. It fails closed when required manifests are missing, when references cannot be resolved, or when gallery asset references do not use Estate-controlled path prefixes.
