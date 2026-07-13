# WP-4126 — Portrait Metadata and Asset Catalog

## Status
Pending

## Series
Visual Estate Initiative — Campaign 02: Canonical Portrait Library

## Objective
Establish a complete, machine-readable and human-auditable catalog for every canonical resident portrait asset.

## Scope
Implement the metadata and cataloging standard for all portrait outputs produced under WP-4118 through WP-4125.

Each asset record must include:

- resident identifier
- resident display name
- asset identifier
- asset category
- portrait type
- camera angle
- crop and framing
- wardrobe reference
- expression reference
- pose reference
- environment reference
- lighting reference
- source prompt reference
- negative prompt reference
- generation model and version
- seed or reproducibility data when available
- source image references when used
- dimensions and file format
- checksum
- creation timestamp
- revision number
- review status
- canonical status
- access classification
- Steward notes reference
- supersedes and superseded-by relationships

## Asset Categories
The catalog must support at minimum:

- hero portrait
- professional office portrait
- full-body reference
- front profile
- side profile
- rear reference
- three-quarter reference
- expression sheet
- headshot
- thumbnail
- black-and-white reference
- photorealistic reference
- review comparison
- rejected or superseded reference

## Repository Requirements
Create a predictable catalog location and schema that can be consumed by later automation, galleries, Open WebUI surfaces, and validation tooling.

The implementation must:

1. Keep metadata adjacent to or reliably linked to the corresponding visual asset.
2. Preserve provenance and revision history.
3. Distinguish review assets from canonical assets.
4. Distinguish public, internal, restricted, and private visual layers.
5. Prevent a superseded asset from being treated as canonical.
6. Support resident-level and Estate-wide asset indexes.
7. Support deterministic lookup by resident, category, angle, and canonical status.
8. Avoid embedding binary image data directly in metadata files.

## Deliverables

- portrait metadata schema
- per-asset metadata template
- resident portrait catalog template
- Estate-wide portrait index template
- validation rules
- example catalog records
- migration guidance for existing images
- documentation for adding, revising, superseding, and locking assets

## Validation
Provide automated or scriptable validation that checks:

- required fields are present
- referenced assets exist
- checksums are valid where configured
- canonical assets are unique per required slot
- superseded assets are not canonical
- access classifications are valid
- resident identifiers resolve correctly
- prompt and negative-prompt references resolve
- revision chains are not broken

## Acceptance Criteria

- Every portrait asset can be uniquely identified and traced.
- A reviewer can determine exactly which asset is canonical and why.
- Later systems can enumerate all canonical portraits for a resident without inspecting filenames manually.
- Review, rejected, superseded, restricted, and canonical assets cannot be confused.
- The catalog supports all portrait types defined in Campaign 02.
- Documentation is sufficient for future residents and future image-generation models.

## Dependencies

- WP-4108
- WP-4116
- WP-4117
- WP-4118 through WP-4125

## Out of Scope

- generating final resident images
- selecting canonical portraits
- group-photo cataloging beyond extension hooks
- motion or video asset metadata beyond forward-compatible fields
