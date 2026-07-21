# WP-4114 Visual Prompt Engineering Runtime Canon

**Status:** Canonical implementation contract, version 1.0<br>
**Classification:** Estate Internal<br>
**Authority:** Supports WP-4114; predecessor canon and Steward decisions remain superior.<br>
**Effective baseline:** merge `a17dfd4`, which contains merged WP-4113 and the WP-4108—WP-4112 foundations.

## 1. Purpose and boundaries

This canon defines one model-neutral, resident-owned and auditable prompt system. It governs semantic prompt records, deterministic composition and receipts; it does not generate images, approve a visual, install a model, infer missing resident facts, or define WP-4115's final negative-prompt taxonomy. An exclusion fragment is an interface only. Stable identity is data, never model syntax or scene decoration.

## 2. Authority and invariants

Authority order is Steward decision, constitutional/governance rules, merged WP-4108—WP-4113 artifacts, this canon, adapters, requests. All residents are unambiguously adults. A prompt must preserve the active physical specification, facial fingerprint, scale profile and resident-owned wardrobe binding. Evelyn is calibration, never a house default. Restricted/private data stays in its matching repository scope, is deny-by-default, and remains visible to authorized governance/audit.

The **stable identity boundary** contains resident ID/name, adult-age presentation, canonical height/build/measurements/proportions, facial geometry/fingerprint, hair identity, eyes, skin and distinguishing features. It cannot contain scene, wardrobe, pose, activity, environment, camera, rendering style, exclusions, sampler or adapter settings. Those may reference identity bindings but cannot rewrite them. An intentional identity variant is a new `review_required` fragment and cannot overwrite approved data.

## 3. Canonical architecture and ordered layers

Composition order is fixed:

1. `identity`: stable resident identity only.
2. `presence`: posture tendency, expression, gaze, energy, emotional anchor and role presence.
3. `wardrobe`: approved resident-owned look, grooming and presentation effects; never physique mutation.
4. `pose`: activity, hand placement, weight, head angle and motion.
5. `environment`: location, scale cues, relationships, spacing and Estate context.
6. `camera`: shot, lens intent, height/distance, aspect, depth, light, framing and alignment.
7. `rendering`: approved medium/style, resolution intent, format/background and color notes.
8. `exclusion`: references or bounded clauses needed by composition; WP-4115 owns its final taxonomy.
9. `model adapter`: serializes the already-composed semantics and supplies pinned runtime parameters. It is not positive identity text.

The first seven layers form the positive prompt; exclusion forms the negative channel. Adapters remain separately recorded. Within a layer fragments sort by immutable fragment ID. Layers never reorder for a model: an adapter that needs different token serialization documents it but preserves canonical ordered IDs and semantic digest.

## 4. Fragment and repository contract

Each JSON-compatible YAML/JSON fragment records schema version, globally stable fragment ID, resident owner (or `_shared` for genuinely nonresident controls), audience scope, layer, integer version, lifecycle state, semantic text, immutable dependency bindings and provenance (`source_ids`, UTC creation, creator, superseded ID). Allowed states are `draft`, `review_required`, `approved`, `superseded`, `retired`. Approved revisions are immutable.

The established WP-4108 audience roots contain:

```text
<resident>/<scope>/prompts/
  fragments/                 # identity, presence, wardrobe, pose, environment, camera, rendering, exclusion
  model_adapters/
  generated_prompt_receipts/
```

Neutral templates live only under `_template`; they contain no Evelyn values. No fragment may reference another resident as its owner. Public resolution cannot load internal/restricted/private material; internal cannot load restricted/private; private activation requires existing authorization outside this package. Diagnostics expose IDs/codes, not protected text.

## 5. Deterministic composition

A request identifies purpose, ordered-independent resident roster, audience, fragment IDs for every named layer, adapter ID and purpose controls. The engine validates the request, adapter, ownership, scope, adult identity, layer placement and referenced existence. It then iterates the canonical layer order, sorts IDs lexically within each layer, normalizes only surrounding whitespace, joins clauses with `; `, and computes SHA-256 over UTF-8 canonical JSON (sorted keys, compact separators, Unicode preserved). It never fills missing facts, selects random fragments, calls a model, mutates inputs, or silently falls back.

Identical request, fragments and adapter produce identical prompt strings, ordered IDs, fragment digests and composition digest. Any revision, parameter or binding change changes the digest. Missing identity is a failure. Missing optional content is permissible only as an explicitly empty list when the purpose permits it; provenance and scope never are.

## 6. Adapter boundary

An adapter declares adapter ID/scope, exact model and version, parameters, optional syntax mapping and known quirks. Runtime receipts pin model hash when available, workflow version, seed/equivalent, sampler, scheduler, steps, guidance, denoise, dimensions, LoRA/embedding/IP-Adapter/ControlNet/reference IDs and weights as applicable. `identity_overrides` must be empty. Compensations may affect syntax/weighting only; semantic identity drift blocks execution and requires adapter revision/review. Cross-model qualification compares receipt-bound outputs later; WP-4114 promises reproducible inputs, not identical pixels.

## 7. Specialized controls

### Turnaround and measurement comparison

Turnaround requires front, front three-quarter, side, rear three-quarter and rear. Identity, grooming, neutral expression, wardrobe, camera, focal-length intent, distance, lighting, background and scale are locked; only angle varies. Measurement A/B/C comparison additionally locks face, pose, footwear, model, seed/equivalent and prompts. Only the declared top/middle/bottom dimension may vary. Bands stack vertically with matching angles aligned and without independent rescaling. One applicable complete set uses heels at least three inches, or cites a governed exemption. Heel presentation never changes standing height. Any uncontrolled digest/control difference fails rather than warns.

### Pair and group

A pair is a two-person group. Every group request records resident roster, identity fragment per resident, relative height map, placement, posture/body language, resident-owned wardrobe IDs, face/hair locks, interaction intent, and hidden-caption recognition metadata. Composition retains each identity independently and supplies exclusion interfaces for face merging and body homogenization. Shared environment/camera/style fragments cannot replace resident fragments. Resident ordering and placement must be explicit; ambiguity is `review_required`.

### Emotional anchor

An anchor binds stable identity to resident-specific presence, posture, expression, gaze, energy and environment. It expresses who the resident is, not only clothing. It must not be copied across residents. Evelyn's listening warmth and Ingrid's boundary-aware composure demonstrate deliberately different anchors.

## 8. Reproducibility receipt

Every generated asset, including rejected output, records receipt/request IDs, residents, audience, prompt version, fully composed positive and negative prompts, every fragment digest, model/version/hash when available, workflow version, seed/equivalent, dimensions, parameters, references, adapters/weights, UTC generation time, review state and asset status (`provisional`, `canonical`, `rejected`, `retired`). A canonical asset requires an approved receipt and later governing promotion; receipt existence is not approval. Receipts are append-only evidence and follow the asset's audience boundary.

## 9. Lifecycle, revision and rollback

Changes create a new version with `supersedes`; old revisions remain addressable and approved records are never edited. Supersession requires review and atomically updates the resolver only after validation/audit succeeds. Retirement excludes normal resolution without deletion. Rollback creates a new revision referencing the compatible earlier semantics and a new decision; it never rewinds history. Stale predecessor bindings yield `review_required` and block canonical generation. Failed transactions retain the previous resolver and receipt history.

## 10. Diagnostics and review states

Failures are deterministic, coded and redact protected payload:

- `PROMPT-MISSING-IDENTITY`, `PROMPT-AGE-AMBIGUOUS`: block.
- `PROMPT-MISSING-METADATA`, `PROMPT-MISSING-FRAGMENT`, `PROMPT-LAYER-MISMATCH`: block.
- `PROMPT-CROSS-RESIDENT`, `PROMPT-AUDIENCE-LEAK`: security/governance block and review.
- `PROMPT-IDENTITY-OVERRIDE`, `PROMPT-ADAPTER-MISMATCH`: block adapter.
- `PROMPT-RECEIPT-INCOMPLETE`, `PROMPT-CANONICAL-RECEIPT-INVALID`: quarantine output/block promotion.
- stale provenance, ambiguous group placement, an adapter quirk without semantic drift: `review_required` until resolved.
- nonessential model-hash unavailability may warn, but the receipt must say unavailable; it cannot invent a hash.

Malformed/duplicate-key/non-JSON-compatible YAML fails closed. Validation must never print private text, auto-promote, fabricate approval, or delete evidence.

## 11. Complete examples

### Evelyn

The implemented internal example composes: Evelyn's unambiguously adult, Evelyn-specific facial and petite stable identity; reassuring soft attention; the provisional white linen resident-owned look with heel/height invariant; neutral full-body pose/studio/camera; model-neutral photoreal rendering; and bounded exclusions. The request is marked example-only and `asset_generated: false`. Its adapter is a pinned-at-execution placeholder with no identity override. It is implementation evidence, not an approved image, measurement lock or wardrobe promotion.

### Contrasting Ingrid

Ingrid's example uses her own adult identity/fingerprint binding, grounded silhouette, cool attentive gaze, upright boundary-aware composure, structured charcoal professional look and practical low footwear. It uses the same schema/engine but no Evelyn height, measurements, dress, heels, expression or emotional anchor. Different composition digests and tests prove the system is resident-neutral rather than Evelyn-specific.

## 12. Validation and tests

Unit tests must prove canonical ordering and input-order independence; required adult identity; schema validity; adapter identity immutability; resident/scope isolation; complete receipts and canonical approval gate; duplicate/unsafe parse rejection; stable digests; and nonmutation. Integration tests compose Evelyn and a contrasting resident, load repository records, validate all templates/schemas, reject cross-resident/private leakage, and preserve predecessor tests.

Required scenarios include: same inputs/same receipt inputs; changed identity/changed digest; absent identity/block; minor ambiguity/block; private fragment in internal request/block; model identity override/block; only declared measurement varies/pass; camera drift across A/B/C/block; complete group roster/pass; missing height/placement/review required; provisional receipt/pass but canonical promotion/block.

## 13. Anti-patterns

Never concatenate arbitrary free text; mix stable identity with wardrobe/camera/style; copy Evelyn into templates; let an adapter alter physical/facial facts; load private fragments by default; use scope to evade review; treat seeds as universal pixel determinism; conceal missing metadata; mutate receipts or approved fragments; promote by schema validity alone; implement WP-4115 taxonomy here; infer ancestry/sensitive traits from appearance; generate or claim assets merely to complete this package.

## 14. Evidence and completion criteria

WP-4114 is implementation-complete when versioned schemas, deterministic engine, repositories, adapter and receipt contracts, four specialized templates, Evelyn/Ingrid examples, validation/tests, report/receipt and acceptance mapping exist; focused and applicable regression tests pass; no final asset or approval is claimed; and unresolved aesthetic/authorization decisions remain explicit.

Acceptance evidence: cross-model identity is protected by immutable identity plus empty adapter overrides; stable separation is schema/layer enforced; measurement differences are template-locked; groups have per-resident identity/height/placement controls; canonical assets require complete approved receipts; provenance/version fields trace fragments; scopes are monotonic; missing identity/adult/scope/receipt metadata fail validation.

## 15. Unresolved Steward decisions

Final resident identity/wardrobe approvals, private authorization/content, resident emotional anchors, approved model inventory and hashes, adapter weights, exemptions, generated visual quality, negative taxonomy, and canonical asset promotion remain unresolved. They are not implementation defaults.
