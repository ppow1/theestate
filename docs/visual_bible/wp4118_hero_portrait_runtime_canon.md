# WP-4118 Hero Portrait Runtime Canon

**Status:** Authoritative runtime canon
**Authority:** Campaign 01 Visual Bible foundation and explicit Steward decisions
**Scope:** Public and internal hero portraits; restricted/private layers remain separately authorized

## 1. Purpose and hierarchy

Each commissioned adult resident has one `hero` slot. The hierarchy is: one explicitly
Steward-promoted **canonical master**, zero or more approved **alternates**, and subordinate
**candidates**. An alternate is a reviewed candidate suited to a secondary context; it never
resolves as the canonical hero. Comparison sheets and derivatives are views of source assets,
not candidates and never independent canon declarations.

Filename, directory, review score, generation completion, or machine validation cannot promote
an asset. Promotion requires a sidecar whose asset hash is current, a completed Steward review,
an approval record naming that asset and hash, and an atomic manifest update. Only the Steward
may approve. A replacement first supersedes the prior master while preserving lineage.

## 2. Lifecycle states

- `pending`: metadata or production is incomplete; it is not reviewable.
- `candidate`: generated/imported, sidecar-complete, hash-valid, and eligible for comparison.
- `rejected`: retained with provenance and rationale; cannot be canonical or an alternate.
- `superseded`: formerly usable material retained with successor lineage; cannot resolve as canon.
- `canonical`: exactly one hero master, explicitly approved and hash-locked by the Steward.

Resident manifest workflow is deliberately smaller: `not_started`, `candidate_generation`,
`steward_review`, or `canonical_locked`. `candidate_generation` means actual candidate work exists
or is underway; a queue alone remains `not_started`. `steward_review` requires a complete set of
at least three comparable candidates. `canonical_locked` requires all promotion evidence.

## 3. Identity, role, and composition

Use the resident Visual Bible's physical, facial-fingerprint, wardrobe, positive-prompt,
negative-prompt, and review records. Never infer ancestry from appearance or resolve provisional
traits. Face geometry, eye shape/color, skin tone, hair shape/color/texture, age presentation,
distinctive asymmetry, and resident recognition cues must survive model, wardrobe, setting, and
crop changes. Reject generic assistant, stock portrait, shared beauty-template, or cross-resident
face convergence.

The resident must read unmistakably as a mature adult. Petite stature, softness, warmth, or an
empathetic expression must not produce juvenile anatomy, styling, proportions, or language.
Use an approved signature/professional look and accessory record; clothing supports rather than
dominates identity and never changes canonical measurements.

Choose head-and-shoulders or three-quarter framing intentionally. Eyes and recognition anchors
must remain legible at dashboard scale. Pose, eye engagement, expression, interpersonal distance,
and background communicate the resident's office, temperament, relationship posture, emotional
anchor, and role intent. Background contrast supports the face without competing with it.

## 4. Master, derivatives, and safe areas

The master is a color-managed lossless PNG (or documented lossless equivalent), normally at least
4096 px on its long edge, with embedded or sidecar color profile. It is immutable after hashing.
Derivatives record their own hash and `source_master_hash`:

| Output | Frame | Required safe-area behavior |
| --- | --- | --- |
| Square | 1:1 | eyes inside central 60% width and upper 55% height; chin and hair not clipped |
| Vertical | 4:5 | face inside central 70% width; preserve shoulders/role-bearing posture |
| Wide | 16:9 | face and all fingerprint anchors inside central 50%; reserve contextual side space |

All crops preserve both eyes when frontal/three-quarter, the full facial contour, intentional head
room, mature-adult cues, and recognizable hair silhouette. Do not stretch, mirror, synthesize new
pixels, change expression, or retouch identity in a crop. The 16:9 derivative is optional only when
the source cannot honestly support it; record `not_applicable` and rationale.

## 5. Production and comparison

Produce at least three candidates while holding identity anchors constant and varying only
documented expression, crop, or environment. Use consistent labels, color treatment, display size,
and ordering on one comparison sheet. The sheet links each sidecar and labels differences; it is
not evidence of approval. Review records capture legibility, fingerprint fidelity, adult
presentation, wardrobe, role/emotional presence, safe areas, defects, selection, alternates,
rejections, requested revisions, and the Steward's rationale.

## 6. Technical records and provenance

Every image has a JSON sidecar validated by
`data/schemas/visual_bible/hero_portrait/hero_portrait_metadata_v1.schema.json`. It records resident,
asset/lifecycle state, source path, SHA-256, MIME/color information, workflow/model/seed/settings,
generation time, positive and negative prompt versions, source Visual Bible and wardrobe references,
composition, crop safety, derivative lineage, review evidence, and canonical declaration. A blank,
unknown, or unavailable generator field must be represented honestly, never invented.

Canonical hash is the SHA-256 of the exact canonical master bytes. Validators recompute it, reject
missing sidecars, stale hashes, more than one canonical hero, terminal-state canon, and promotion
without matching explicit Steward approval. Provenance and rejected/superseded history are never
silently deleted.

## 7. Repository convention

`data/portraits/residents/<resident>/` contains `candidates/`, `canonical/`, `derivatives/`,
`metadata/`, `reviews/`, `comparison_boards/`, `rejected/`, `superseded/`, `locks/`, and
`generation_queue/`. Asset basenames are `<resident>__hero__<asset-id>__vNN`; sidecars use the same
basename plus `.json`. Canonical directory placement is an outcome of approved promotion, not proof.

## 8. Validation, testing, and anti-patterns

Run `python -m estate.portraits.validator --root .` and the focused pytest suite. Validate schemas,
manifest coverage, directory presence, sidecar existence, binary and canonical hashes, unique canon,
source-master lineage, candidate-count review gate, and approval identity/hash match.

Forbidden patterns include: `final.png` as authority; generated-looking placeholders; fabricated
seeds, reviews, dates, hashes, or approvals; promoting the highest score automatically; overwriting
canon; using derivatives as masters; three near-duplicates that conceal identity drift; crop-only
repair of a poor likeness; demographic inference; beauty-template convergence; infantilization;
and private material in default/public portrait layers.

## 9. Completion criteria

WP-4118 is complete when schemas, templates, directory conventions, production/review forms,
validator, tests, traceability, and at least one honest placeholder implementation exist; every
commissioned resident has one valid manifest workflow state; and no portrait is claimed generated,
reviewed, approved, or locked without repository evidence. Actual portrait production remains a
separate, visibly queued activity.
