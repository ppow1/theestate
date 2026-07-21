# WP-4113 Wardrobe and Signature-Look Library implementation

## Authority and boundaries

This implementation is governed by `docs/visual_bible/wp4113_wardrobe_signature_look_runtime_canon.md` and extends WP-4108 through WP-4112. Physical specification, facial fingerprint, scale/camera data, and measurement-variant promotion remain predecessor authority. Wardrobe records bind immutable IDs, revisions, and digests; fit, construction, footwear, pose, and camera are presentation effects and cannot rewrite physique.

The implementation produces no images and claims no Steward approval. Evelyn's white linen direction is a provisional, internal calibration record with null full-body and portrait evidence and a blocked promotion flag. It is never a neutral template.

## Repository standard

Every resident and template has a `wardrobe/` tree inside each `public`, `internal`, `restricted`, and `private` WP-4108 layer. It contains the five governed library files when content exists, prompt fragments, governed reference metadata, immutable rejected variants, revisions, reviews, monthly audit storage, and Steward notes. Binary images remain in WP-4108 asset buckets; reference directories contain metadata or relative references only.

Records use JSON-compatible YAML. This deliberately constrained safe subset is parsed with duplicate-key detection, rejects tags and aliases, and avoids an executable YAML dependency. IDs are immutable kebab-case resident-owned identifiers. `canonical_digest` serializes sorted UTF-8 JSON with compact separators after omitting only `provenance.content_digest`; numbers and strings are retained as parsed. A semantic revision increments `revision`, stores the prior revision, and records replacement lineage rather than overwriting it.

## Runtime behavior

`estate.visual_bible.wardrobe` provides safe loading, deterministic hashing, envelope/taxonomy/manifest, fit, footwear, accessory, prompt, signature-promotion, reference, audience, transition, private-activation, scaffold, and hash-chain audit behavior. Errors are stable WP-4113 diagnostic codes and JSON-pointer-like paths. Public/internal records cannot resolve restricted/private data; private activation is deny-by-default and time-bounded. Rejected and retired dependencies remain auditable but unavailable to active runtime selection.

Canonical promotion is fail-closed: it requires an approved/canonical state, a Steward decision ID, and both governed full-body and portrait evidence. The example intentionally cannot pass that gate. Actual authorization/authentication and durable transaction storage are host integrations; the validators require their honest records and never impersonate them.

## Schema and record inventory

Eight Draft 2020-12 schemas cover manifest, signature look, fit, footwear, accessory, prompt fragments, reviews/decisions (approval, rejection, supersession, retirement), and audit events. Review and audit envelopes support Steward notes, attestations, replacement lineage, approval/rejection events, retirement and rollback. Templates are resident-neutral and include an honest reproducibility receipt with null asset/adapter/authorization fields.

## Campaign 05 compatibility

A later asset generator consumes immutable look, physical, fingerprint, scale, fit, footwear, accessory, and prompt digests and writes an asset ID into a new receipt. It must not edit the semantic record, lower audience scope, infer approval, or promote an image automatically. WP-4114 and WP-4115 may compose/translate the positive and negative interfaces but may not alter resident identity or stored semantics.

## Operator validation scenarios

| Scenario | Result |
|---|---|
| complete resident-owned provisional look | authoring validation passes |
| missing fit, scope, or either prompt side | blocked with required diagnostic |
| physique mutation or heel-adjusted true height | blocked as canon contradiction/mutation |
| another resident's record or a higher-sensitivity reference | blocked |
| private record without explicit expiring authorization | denied safely |
| invalid lifecycle pair/transition | blocked; history retained |
| canonical request without two assets and Steward decision | blocked |
| rejected/retired dependency selected for active use | blocked |
| unsafe YAML or duplicate mapping key | blocked before semantic validation |
| dependency digest changes | manifest binding fails/stales; no automatic rebind |

## Unresolved Steward decisions

All resident-specific category applicability, wardrobe preferences, sizes, aesthetics, safety constraints, heel exemptions, signature selections, private authorization, approvals, rejections, retirement, declassification, and actual assets remain Steward decisions. Evelyn's neckline, sleeve, accessories, hair/makeup details, evidence, and canonical disposition remain pending.
