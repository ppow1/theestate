# WP-4124 Headshot and Thumbnail Runtime Canon

## Authority and hierarchy

The identity hierarchy is: accepted Visual Bible and facial fingerprint → approved high-resolution portrait source → review-only headshot master candidate → explicitly Steward-accepted canonical master → deterministic derivatives. A derivative is never an independent identity source. A new file, better render, path overwrite, or catalog edit **must not silently replace canon**; replacement requires a new asset ID, hashes, lineage, comparison review, Steward decision, and supersession link.

`headshot` is a close or shoulders-up identity portrait. `avatar` is a person-facing compact identity representation; `icon_source` is the master crop used to produce it. `model_card` identifies a resident/model in a picker, `dashboard` supports operational panels, `dossier` supports identity records, and `thumbnail` is the generic small representation. These uses do not grant canonical status.

## Masters, derivatives, sizes, and naming

Masters are lossless or highest-quality 4:5 sources of at least 2048 × 2560 when generated; the approved 512 × 512 master crop is a derivative crop, not an independently regenerated face. Supported square outputs are exactly 32, 64, 128, 256, and 512 pixels (1:1). A 4:5 master and 1:1 square/circle-safe derivatives are supported. Names use `{resident_id}__{slot_id}__{variant}__{width}x{height}__v{revision:03d}.{ext}`; IDs and revisions are immutable.

Every resident has canonical-neutral, shoulders-up professional, warm/conversational, and WP-4123 role-specific slots. Square, circle-preview, light-interface, dark-interface, monochrome, and transparent-cutout plans are explicit. Missing media stays `pending_generation`; a plan is not evidence.

## Crop, safe area, and recognition

Use normalized crop coordinates. Preserve crown/hair silhouette, both eyes, jawline, role-relevant wardrobe cues, and breathing room below the chin. The face must remain inside a circle-safe radius no larger than 0.5 of frame width. Eye line, face scale, camera height, and a 70–105 mm equivalent perspective remain consistent. Never upscale a small derivative or chain derivative-to-derivative.

Review at native size against every resident with captions hidden. At 32 px, facial geometry, eye mass/contrast (not invented color), hair silhouette, age impression, expression, and visual fingerprint must remain distinguishable. Reject identity/expression drift, smoothing, haloing, collapsed hair/jaw, duplicate-looking residents, or reduction artifacts. Light and dark UI previews must independently pass.

## Background, color, and processing

Use simple, provenance-recorded backgrounds. Light UI requires sufficient edge separation from light surfaces; dark UI requires separation without halos. Alpha is allowed only for approved PNG/WebP cutouts and must preserve hair edges; do not fake transparency with a checkerboard or matte. Retain canonical sRGB color and approved eye/skin/hair values. Monochrome is a labeled derivative, never the color canonical source, and must preserve tonal separation.

Generate each derivative directly from the canonical higher-resolution source: apply the approved crop, convert to sRGB, resize once with deterministic Lanczos (or a version-pinned equivalent), apply conservative size-specific output sharpening, then encode with pinned settings. No beauty retouching, generative fill, expression alteration, or identity-changing sharpening is permitted.

## Metadata, lineage, scopes, and lifecycle

Each existing asset records source URI, source SHA-256, its own SHA-256, dimensions, aspect ratio, crop/safe area, generation recipe/version/settings, timestamps/operator, predecessor/successor, and for derivatives the source asset ID/hash and recipe ID. Validators recompute hashes, detect stale records, duplicate asset IDs/content, unsupported sizes, and orphan lineage.

Lifecycle states are `pending`, `candidate`, `canonical`, `rejected`, and `superseded`. Access scopes are `public`, `internal`, `restricted`, `private`, `review_only`, `rejected`, and `canonical`. Lifecycle and access are separate: a candidate is normally review-only; rejected media uses rejected scope; canonical scope requires acceptance. Public release remains a separate authorization.

## Review, diagnostics, validation, and acceptance

Candidate review records include native-size results, hidden-caption confusion notes, light/dark UI results, crop, expression and identity checks, reviewer, time, and disposition. Only the Steward may accept canon; approval binds asset ID and hash. Any changed byte invalidates that approval. Rejected and superseded files cannot become canonical.

Validation must cover schemas, resident coverage, deterministic naming/dimensions, honest pending slots, hashes/lineage, stale and duplicate derivatives, safe area, native-size recognizability records, canonical approval, directory separation, and catalog traceability. Anti-patterns include fabricated assets/reviews, independent thumbnail regeneration, chained resizing, unversioned overwrites, missing hashes, candidate-as-canon, labels-only recognition testing, one preview theme, and cross-resident template inheritance.

Runtime implementation is complete when schemas, manifests, templates, validator, fixtures, documentation, and all commissioned-resident pending slots validate. Visual completion additionally requires real masters and every derivative, group preview sheets, 32 px distinctness, light/dark passes, provenance, and hash-bound Steward selections. Until then the exact asset status is honestly pending generation and review.
