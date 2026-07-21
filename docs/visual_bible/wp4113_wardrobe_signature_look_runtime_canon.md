# WP-4113 Wardrobe and Signature-Look Library

## Supporting Runtime Canon and Design Specification

**Status:** implementation-ready supporting canon; WP-4113 remains pending  
**Authority:** WP-4113, subject to the Estate Constitution and Steward decisions  
**Scope:** runtime contract only; this document creates no schemas, records, directories, assets, approvals, or canonical locks  
**Depends on:** WP-4108, WP-4109, WP-4110, WP-4111, and WP-4112

---

## 1. Mission and purpose

The wardrobe runtime shall give each commissioned adult resident a distinct, reproducible, governed clothing language without treating clothing as a substitute for identity or as a way to mutate physical canon. It shall describe office, daily, casual, formal, seasonal, activity, swim, and explicitly authorized private-audience presentation; connect every approved look to reproducible prompt material and review evidence; and preserve a complete decision trail.

This canon removes implementation discretion about storage, schemas, lifecycle, authorization, validation, promotion, revision, and rollback. It does not select final looks for residents, generate images, approve Evelyn's provisional example, or implement WP-4113.

## 2. Authority and inherited constraints

1. The Steward is final approval authority. Automation, an operator, a reviewer, or repository merge cannot impersonate Steward approval.
2. WP-4108 owns the resident Visual Bible, its four visibility layers (`public`, `internal`, `restricted`, `private`), provenance conventions, asset-state separation, and canonical lock boundary. This canon extends rather than replaces them.
3. WP-4109 owns adult status, true height, measurements, physique, silhouette, posture, and versioned physical-specification authority. Wardrobe records reference those records by immutable ID and digest; they never copy a value as a new authority.
4. WP-4110 owns facial geometry and visual fingerprint. Hair and makeup coordination in a look may constrain styling but may not overwrite the resident's stable identity.
5. WP-4111 owns true/apparent/presentation height, scale and camera profiles, posture baseline, and footwear-adjusted presentation. Heel metadata references that model and must never add heel height to canonical standing height.
6. WP-4112 owns measurement-variant comparison and promotion. A WP-4113 look may be the locked comparison wardrobe, but cannot select or promote a measurement variant.
7. Every resident is an adult. Age-appropriate means faithful adult presentation, not infantilization or an unreviewed change of apparent age.
8. Restricted or private material is governed content, not hidden content. Its existence and safe audit metadata remain discoverable to authorized governance surfaces while its sensitive payload remains access-controlled.

On conflict, the Constitution and explicit Steward decisions prevail, followed by the predecessor contracts above, then WP-4113, then this canon. A conflict is a blocking diagnostic, not permission to invent a reconciliation.

## 3. Governing principles and policy

- **Resident ownership:** every record has exactly one `resident_id`. Cross-resident inheritance of measurements, aesthetic defaults, prompt fragments, signature status, or approvals is forbidden.
- **Identity before fashion:** a look supports role, personality, and visual fingerprint; wardrobe alone must not be the only recognition cue.
- **Physique/presentation separation:** fit, tailoring, padding, structured cups, foundation garments, pose, camera, and footwear are declared presentation effects. They never rewrite body data.
- **Explicit applicability:** taxonomy categories exist for every library, but character-inappropriate categories may be `not_applicable` with rationale and Steward review. Empty required-looking stubs are not compliance.
- **Least visibility and no scope escalation:** a record is stored in one audience layer and may reference only equally or less sensitive dependencies. Derived prompts, crops, and metadata may not be published above their source authorization.
- **Evidence before promotion:** schema validity is necessary but insufficient. Canonical promotion requires approved review evidence and, for a signature look, approved full-body and portrait-crop asset records.
- **Append-only decisions:** corrections create revisions and audit events. Approval, rejection, retirement, and rollback history is never edited away.
- **Reproducibility without provider lock-in:** semantic prompt fragments are model-neutral; optional model notes are isolated overlays.
- **Safe, contextual presentation:** revealing content is never implied by a category. Swim, private-audience, or fitted presentation still requires resident-appropriate adult context and authorization.

## 4. Terminology

| Term | Meaning |
|---|---|
| wardrobe entry | One resident-owned outfit specification for a declared category and context. |
| look | A wardrobe entry plus coordinated footwear, accessories, hair, makeup, prompt fragments, pose/camera guidance, and evidence references. |
| signature look | A look proposed or approved as strongly and uniquely associated with one resident. |
| library | The audience-layer collection of manifests and referenced wardrobe records for one resident. |
| physical binding | Immutable references to the WP-4109 specification version and WP-4111 scale/posture profiles against which fit was reviewed. |
| presentation effect | A reversible visual effect caused by garments, construction, footwear, pose, styling, or camera, not a body change. |
| audience scope | Exactly one of `public`, `internal`, `restricted`, or `private`. |
| lifecycle state | Editorial state of a record: `draft`, `in_review`, `revision_requested`, `approved`, `rejected`, or `retired`. |
| canon class | Evidentiary standing of a look: `experimental`, `provisional`, `canonical`, `rejected`, or `retired`. |
| canonical | Explicitly Steward-approved and promoted under the active physical/identity bindings. |
| provisional | Coherent preferred direction still awaiting final canonical approval or required evidence. |
| experimental | Exploratory material with no approval implication. |
| rejected | Preserved, unusable direction with reason and decision reference. |
| retired | Formerly approved material removed from active use without deleting history. |
| approved | Workflow state meaning the Steward approved the reviewed revision; canonical status additionally requires a successful promotion record. |
| prompt fragment | Structured, composable semantic instructions for a look; not a complete generation prompt. |
| negative fragment | Structured preventions tied to known identity, garment, fit, anatomy, and model risks. |

`canonical`, `provisional`, `experimental`, `rejected`, and `retired` are mutually exclusive canon classes. Workflow and canon class are separate fields and only the transition pairs in section 15 are legal.

## 5. Required repository organization

Implementation shall extend each resident's existing WP-4108 layer root:

```text
data/visual_bibles/residents/<resident_id>/<audience_scope>/
  wardrobe/
    wardrobe_manifest.yaml
    signature_looks.yaml
    fit_rules.yaml
    accessories.yaml
    footwear.yaml
    prompt_fragments/
      <fragment_id>.yaml
    reference_images/
      <asset metadata or references>
    rejected_variants/
      <immutable rejected record or reference>
    steward_notes.md
    revisions/
      <record_id>/<revision>.yaml
    reviews/
      <review_id>.yaml
    audit/
      <yyyy>/<mm>/<event_id>.json
```

The literal required WP-4113 paths therefore live under each audience layer rather than in an unscoped resident-global directory. A resident may have multiple scoped libraries; records must not be duplicated between layers merely to make them discoverable. The existing `assets/candidates`, `assets/canonical`, `assets/rejected`, and `assets/superseded` directories remain authoritative binary-asset locations. `reference_images/` contains metadata files or relative references to those assets, never a second unmanaged copy.

Schema files shall be versioned under:

```text
data/schemas/visual_bible/wardrobe/
  wardrobe_manifest_v1.schema.json
  signature_looks_v1.schema.json
  fit_rules_v1.schema.json
  footwear_v1.schema.json
  accessories_v1.schema.json
  wardrobe_prompt_fragment_v1.schema.json
  wardrobe_review_v1.schema.json
  wardrobe_audit_event_v1.schema.json
```

Runtime validation belongs in the existing `src/estate/visual_bible/` package; neutral templates belong under `templates/visual_bible/`; fixtures under `tests/fixtures/visual_bible/`; tests under `tests/`. Implementation must not modify the pending WP merely to signal progress.

### 5.1 Naming and identity

- IDs use lowercase ASCII kebab case and are immutable: `wd-<resident>-<semantic-name>-v<n>`, `sl-...`, `fit-...`, `fw-...`, `acc-...`, `pf-...`, `wr-...`, `wae-...`.
- `resident_id`, `audience_scope`, and record ID must agree with the enclosing path.
- File paths are repository-relative, use `/`, contain no `..`, and cannot escape the owning layer.
- Semantic revisions are positive integers. A changed approved payload receives a new revision and SHA-256 digest, never an in-place overwrite.
- Human display names are labels, never keys or authorization identifiers.

## 6. Persistent record envelope

Every YAML record except `steward_notes.md` shall use this envelope. JSON Schemas validate YAML after safe parsing.

```yaml
schema_version: estate.visual_bible.wardrobe.<record_type>.v1
record_id: wd-evelyn-white-linen-professional-v1
revision: 1
resident_id: evelyn
audience_scope: internal
lifecycle_state: draft
canon_class: provisional
active: true
created_at: 2026-07-21T00:00:00Z
created_by: <authenticated-principal-id>
updated_at: 2026-07-21T00:00:00Z
provenance:
  source_refs: [<repository-relative authoritative reference>]
  parent_record_ids: []
  replacement_for: null
  content_digest: sha256:<64-lowercase-hex>
  schema_digest: sha256:<64-lowercase-hex>
steward_decision_id: null
```

Timestamps are RFC 3339 UTC. Digests are computed from canonicalized parsed content excluding `provenance.content_digest`; the implementation must document and test canonicalization. Unknown properties fail validation unless a schema explicitly permits a namespaced extension. Null is accepted only where specified.

## 7. Wardrobe taxonomy and manifest schema

Each `wardrobe_manifest.yaml` contains the envelope plus:

```yaml
library_id: wardrobe-<resident>-<scope>-v1
physical_specification_ref: {id: <wp4109-id>, revision: 1, digest: sha256:...}
facial_fingerprint_ref: {id: <wp4110-id>, revision: 1, digest: sha256:...}
scale_profile_ref: {id: <wp4111-id>, revision: 1, digest: sha256:...}
category_coverage:
  - category: office-authoritative
    applicability: required     # required | optional | not_applicable
    rationale: <resident-specific reason>
    entry_ids: [wd-...]
entries: [wd-...]
signature_look_ids: [sl-...]
fit_rule_ids: [fit-...]
footwear_ids: [fw-...]
accessory_ids: [acc-...]
prompt_fragment_ids: [pf-...]
review_ids: [wr-...]
```

The closed v1 taxonomy is:

`office-authoritative`, `office-approachable`, `business-casual`, `casual-day`, `casual-evening`, `home-relaxed`, `formal-day`, `cocktail`, `formal-evening`, `ceremony`, `seasonal-summer`, `seasonal-winter`, `rain-travel`, `fitness`, `dance`, `hobby-specific`, `swim`, `signature-look`, and `private-audience`.

All categories must appear once in `category_coverage`. `private-audience` is never automatically applicable and can be populated only in the `private` layer with explicit authorization. `swim`, `dance`, `hobby-specific`, and the seasonal categories may be `not_applicable`; the other ordinary categories may also be `not_applicable` where character or role makes that honest, but require a rationale and Steward disposition during library review. Implementation may map the foundation schema's broad categories (`office`, `casual`, `formal`, `activity`, `seasonal`, `restricted`) to this taxonomy but may not alter that schema's meaning.

Each referenced wardrobe entry declares:

```yaml
category: office-authoritative
title: <human label>
contexts: [office]
garments:
  - garment_id: <local immutable id>
    garment_type: dress
    fabric: {name: linen, weight: light, weave: plain, finish: matte, behavior: <drape/wrinkle/movement>}
    construction: {cut: tailored, color: white, pattern: solid, hemline: mid-knee, neckline: <value>, sleeve: <value>, closure: <value>, lining: <value>}
    fit_rule_ids: [fit-...]
footwear_id: fw-...
accessory_ids: [acc-...]
hair_coordination: <instruction consistent with WP-4110>
makeup_coordination: <adult, role-appropriate instruction or none>
pose_guidance: <instruction>
camera_guidance: {scale_profile_id: <id>, camera_profile_id: <id>, framing: full-body}
positive_prompt_fragment_id: pf-...-positive
negative_prompt_fragment_id: pf-...-negative
known_generation_risks: [{code: <closed diagnostic code>, mitigation: <text>}]
```

## 8. Fit and proportion rules

`fit_rules.yaml` is a collection of resident-owned rules. Every rule requires:

```yaml
fit_rule_id: fit-<resident>-<name>-v1
measurement_profile_ref: {id: <wp4109-id>, revision: 1, digest: sha256:...}
height_profile_ref: {id: <wp4111-id>, revision: 1, digest: sha256:...}
tailoring_assumptions:
  size_system: US
  nominal_size: <string or null>
  custom_tailored: true
  alteration_notes: <text>
fit_class: fitted              # fitted | relaxed | structured | draped | athletic
ease: {bust_chest: <text>, waist: <text>, hip: <text>, mobility: <text>}
apparent_proportion_effects:
  torso: neutral
  legs: lengthened
  shoulders: neutral
  waist: visually-defined
presentation_effects:
  shapewear: {used: false, effect: none}
  push_up_construction: {used: false, effect: none}
  structured_cups: {used: false, effect: none}
  padding: {used: false, locations: [], effect: none}
  tailoring: {used: true, effect: <visual effect>}
body_proportion_preservation: <positive instruction>
mobility_and_safety: <context-specific constraint>
known_generation_risks: [{code: FIT-..., mitigation: <text>}]
```

Every named presentation effect must be declared, even when false. Effects describe appearance only. A validator compares the referenced immutable physical and height bindings with the active authoritative records and blocks stale or contradictory claims. Free-text size is an assumption, never a conversion back into measurements. Clothing cannot narrow, enlarge, lengthen, shorten, or otherwise update the physical record.

## 9. Footwear rules

Every `footwear.yaml` item requires `footwear_id`, style, heel height, platform height, toe shape, material, color, posture effect, activity suitability, resident preference, safety constraints, and WP-4111 footwear-presentation reference:

```yaml
footwear_id: fw-<resident>-white-pump-v1
style: pump
heel_height: {value: 3.0, unit: in}
platform_height: {value: 0.0, unit: in}
toe_shape: <closed value or explicitly documented other>
material: <text>
color: <text>
posture_effect: <presentation-only description>
apparent_height_effect: <description; never true-height mutation>
activity_suitability: [standing, office, short-walk]
resident_preference: preferred
safety: {character_appropriate: true, mobility_reviewed: true, constraints: <text>}
scale_footwear_profile_ref: <wp4111 footwear record>
```

Lengths use an object with numeric `value` and `unit` (`in` or `cm`), are nonnegative, and normalize for comparisons without rounding away the source. Platform height cannot exceed heel height unless the declared footwear geometry and reviewer note explain the measurement convention.

For each resident, the manifest records `heel_comparison` as `required`, `satisfied`, or `exempt`. Where character-appropriate and safe, at least one canonical or in-review set must use a heel of 3.0 inches or more. `exempt` requires role, preference, mobility, safety, or canon rationale plus Steward decision. This is a visual-proportion review, not a daily mandate. Heel/posture effects bind to WP-4111 and are held identical across WP-4112 variants.

## 10. Accessory rules

Each `accessories.yaml` item requires:

```yaml
accessory_id: acc-<resident>-<name>-v1
type: jewelry             # jewelry | eyewear | hosiery | bag | belt | scarf | headwear | other
description: <material, color, scale, construction>
placement: <text>
contexts: [office]
coordination_rules: <hair/garment/footwear relationship>
identity_role: supporting # signature | supporting | neutral
visual_fingerprint_effect: <preserve/reinforce/neutral explanation>
scale_and_fit: <resident-specific size/placement>
safety_and_activity: <constraints>
optional: false
known_generation_risks: [{code: ACC-..., mitigation: <text>}]
```

Accessories cannot be used to encode an undisclosed audience mode, infer a sensitive trait, obscure identity-validation landmarks, or create a cross-resident template. Eyewear records distinguish prescription/identity relevance only when an authoritative source permits it; otherwise they describe presentation, not medical fact.

## 11. Signature-look schema and lifecycle

Each `signature_looks.yaml` entry requires all ordinary look fields plus:

```yaml
signature_look_id: sl-<resident>-<name>-v1
distinctiveness:
  resident_association: <why this resident>
  office_role_reinforcement: <text>
  personality_reinforcement: <text>
  visual_fingerprint_reinforcement: <text>
  cross_resident_collision_check: {checked_resident_ids: [...], result: pass, notes: <text>}
design:
  garments: [<complete references>]
  fabric: <complete summary>
  cut: <text>
  colors: [<values>]
  hemline: <text>
  neckline: <text>
  sleeve: <text>
  footwear_id: fw-...
  accessory_ids: [acc-...]
  hair: <coordination>
  makeup: <coordination>
  pose: <guidance>
prompt_refs: {positive: pf-..., negative: pf-...}
evidence:
  full_body_asset: {asset_id: <id>, digest: sha256:..., review_state: approved}
  portrait_crop_asset: {asset_id: <id>, digest: sha256:..., derived_from: <full or separately approved source>, review_state: approved}
approval: {review_id: <id or null>, steward_decision_id: <id or null>, approved_revision: <integer or null>}
```

Lifecycle:

1. Author as `draft/experimental` or `draft/provisional` against current bindings.
2. Technical validation moves it to `in_review`; no status changes implicitly.
3. Identity, fit, audience, prompt, evidence, and cross-resident collision review occurs.
4. Steward may request revision, reject, provisionally approve the direction, or approve it for promotion.
5. Only a separate successful promotion event produces `approved/canonical`. It records the exact record revision and digests.
6. A changed canonical look becomes a new revision and begins review again. Until promoted, the previous canonical revision remains active.
7. A canonical look may become `retired/retired`; its assets move or link to `superseded`, references resolve historically, and it is excluded from new prompt assembly.
8. `rejected/rejected` is terminal for that revision. A new proposal must use a new revision or ID and link `replacement_for`.

Exactly one active canonical revision may exist for a given `signature_look_id`; a resident may have multiple distinct signature looks. No minimum number becomes canonical without Steward approval.

## 12. Prompt-fragment and negative-fragment schemas

Positive and negative fragments are separate records. Every approved look references one of each in the same resident and audience scope.

```yaml
schema_version: estate.visual_bible.wardrobe.prompt_fragment.v1
fragment_id: pf-<resident>-<look>-positive-v1
fragment_kind: positive
resident_id: <resident>
look_id: <look>
audience_scope: internal
semantic_order:
  - identity_binding
  - adult_presentation
  - garment
  - fabric_behavior
  - fit_behavior
  - proportion_preservation
  - footwear_and_posture
  - accessories_and_styling
  - camera_and_pose
clauses:
  identity_binding: {text: <resident and fingerprint preservation>, source_refs: [<wp4110>]}
  adult_presentation: {text: <explicit adult, context-appropriate presentation>}
  garment: {text: <complete reproducible garment description>}
  fabric_behavior: {text: <drape, weight, wrinkle, sheen, movement>}
  fit_behavior: {text: <fit/ease/tailoring>}
  proportion_preservation: {text: <do not change canonical height/measurements>, source_refs: [<wp4109>, <wp4111>]}
  footwear_and_posture: {text: <effect and true-height separation>}
  accessories_and_styling: {text: <coordination>}
  camera_and_pose: {text: <profile references and considerations>}
model_overlays:
  - provider: <provider>
    model: <model and version>
    instruction: <bounded compatibility note>
    tested: false
```

Negative fragments use the same envelope and bindings with `fragment_kind: negative` and:

```yaml
prohibitions:
  identity_drift: [<resident-specific forbidden changes>]
  proportion_drift: [<height, measurement, silhouette, posture drift>]
  garment_failures: [<wrong hem/neckline/sleeve/fabric/color/closure>]
  fit_failures: [<unintended reshaping, sizing, clipping, painted-on fabric>]
  footwear_failures: [<wrong heel/platform, fused feet, unsafe pose>]
  accessory_failures: [<missing/duplicated/misplaced/scale errors>]
  anatomy_and_artifact: [<hands, limbs, eyes, cloth intersections>]
  age_and_context: [<non-adult presentation, decontextualization>]
  audience_leakage: [<private/restricted details forbidden outside scope>]
model_overlays: []
```

Negative fragments state observable failures rather than using protected traits as shorthand. They complement, and later must compose with, WP-4115 rather than redefining its global failure taxonomy. Positive fragments similarly compose with the later WP-4114 canon. Model overlays never change semantic intent, audience, identity, or canon.

## 13. Image metadata

No image is required or generated by this canon. Future reference assets must remain in WP-4108 asset directories and include:

- `asset_id`, repository-relative path, media type, dimensions, byte size, SHA-256 digest;
- resident ID, adult-status source, audience scope, asset lifecycle/canonical state;
- look ID/revision/digest, garment/fit/footwear/accessory IDs and revisions;
- physical, facial-fingerprint, scale, camera, and posture profile IDs/digests;
- positive and negative fragment IDs/revisions/digests;
- provider, model/checkpoint/version, workflow and settings digest, seed or deterministic-equivalent, sampler/scheduler where applicable;
- source/reference asset IDs and derivation/crop lineage;
- generated/imported time and authenticated actor;
- review IDs, Steward decision, rejection codes, replacement/supersession links;
- visibility and authorization policy reference without copying restricted payload into a broadly visible index.

Metadata and file digest mismatch blocks all review and use. A crop inherits the source's audience scope unless an authorized declassification decision explicitly permits a less restrictive derivative. Full-body and portrait evidence must show the same approved revision; a portrait crop cannot conceal a known full-body failure.

## 14. Audience scoping and access control

| Scope | Default availability | Minimum authorization |
|---|---|---|
| public | explicitly approved public surfaces | authenticated publisher plus Steward-approved public promotion |
| internal | Estate internal runtime | authenticated resident/office role with internal visual permission |
| restricted | deny by default | explicit policy entitlement and purpose binding |
| private | unavailable by default | explicit person, audience, activation context, purpose, and time-bounded authorization |

Authorization is evaluated at read, composition, generation, review, export, and logging boundaries. Listing endpoints may reveal only safe metadata (`record_id`, owning resident, scope, lifecycle, timestamps, decision reference, digest) to governance roles; they must not reveal private prompt clauses, garment details, thumbnails, or paths usable as a bypass. Cache keys include principal, audience scope, authorization context, record revision, and digest. Revocation invalidates derived caches.

Cross-scope references may point from a more restrictive record to a less restrictive dependency. A less restrictive record cannot reference a more restrictive dependency. Moving material between scopes is a reviewed revision with a declassification/promotion decision, not a filesystem move. Private-mode activation states inherited from the initiative (`unavailable`, `available`, `active`, `deactivated`) are orthogonal to record lifecycle; `active` requires explicit session authorization and creates access events. No ordinary session loads private content by default.

## 15. Review and Steward approval workflow

### 15.1 Lifecycle matrix

| From | Allowed to | Authority and condition |
|---|---|---|
| `draft/experimental` | `draft/provisional`, `in_review/experimental`, `rejected/rejected` | author may propose; reviewer rejects only with record |
| `draft/provisional` | `in_review/provisional`, `rejected/rejected` | technical validation passes or rejection recorded |
| `in_review/*` | `revision_requested/*`, `approved/provisional`, `rejected/rejected` | reviewer; approval field requires Steward decision |
| `revision_requested/*` | new revision in `draft/*` | author; prior revision preserved |
| `approved/provisional` | `approved/canonical`, `revision_requested/provisional`, `rejected/rejected` | canonical only through Steward-approved promotion |
| `approved/canonical` | `retired/retired` | Steward retirement or successful replacement promotion |

Any other pair or transition fails. `active: true` is forbidden for rejected or retired revisions. Experimental records never enter canonical asset/prompt resolution.

### 15.2 Review gates

1. **Intake:** authenticate actor; bind resident, scope, intent, category, and current predecessor records.
2. **Structural validation:** safe YAML, schema, IDs, enums, references, paths, digests, and lifecycle.
3. **Governance validation:** adult assertion, authorization, scope monotonicity, private activation, and no concealed content.
4. **Identity and fit review:** WP-4109/4110/4111 bindings, fit effects, footwear posture, and cross-resident distinction.
5. **Prompt review:** positive/negative completeness, semantic consistency, leakage, and model overlay isolation.
6. **Evidence review:** when imagery exists, provenance, full-body/portrait agreement, anatomy, garment, identity, proportions, and artifact checks.
7. **Steward review:** display the exact revision/digests, safe comparison surface, all prior notes, failed checks, scope, and proposed action.
8. **Decision:** `approve_provisional`, `approve_canonical_promotion`, `request_revision`, `reject`, `retire`, or `defer`. Record rationale; absence or silence is `defer`, never approval.
9. **Promotion:** transactionally verify unchanged digests and active dependencies, append promotion/audit records, then update active indexes. Failure leaves previous canon active.

### 15.3 Review record

`wardrobe_review_v1` requires review ID, subject ID/revision/digest, resident, scope, requester, reviewers, opened/closed times, gate results and evidence references, automated diagnostics, Steward decision (`decision`, `rationale`, `conditions`, `decided_by`, `decided_at`, `signature_or_attestation_ref`), superseded decision ID, and promotion record ID. Only the authenticated Steward identity may populate a Steward approval. Notes in `steward_notes.md` are authoritative input but are not machine authorization unless linked by a signed/attested decision record.

## 16. Audit records and governance

Every create, validate, submit, read of restricted/private payload, activation/deactivation, review, note attachment, decision, promotion, rejection, revision, retirement, rollback, export, denial, and digest failure appends an audit event:

```yaml
event_id: wae-<uuid>
event_type: wardrobe.review.submitted
occurred_at: <RFC3339 UTC>
actor: {principal_id: <id>, role: <role>, authenticated: true}
subject: {resident_id: <id>, record_id: <id>, revision: 1, digest: sha256:..., audience_scope: internal}
authorization: {decision: allow, policy_ref: <id>, purpose: <text>, context_id: <id>}
correlation_id: <id>
prior_event_digest: sha256:...
outcome: success
diagnostic_codes: []
safe_summary: <non-sensitive text>
payload_ref: <same-scope protected record or null>
event_digest: sha256:...
```

Events are append-only, hash-linked within a subject stream, UTC ordered, and retained according to existing Estate policy. Safe summaries cannot contain restricted/private prompt or visual content. Audit failure is fail-closed for promotion, private access, export, and destructive state changes. Governance may inspect safe metadata without receiving the payload; authorized audit access is itself logged.

## 17. Runtime behavior and integration points

### 17.1 Resolution

Given authenticated principal, resident, context, category, and requested scope, runtime shall:

1. authorize scope and private activation before reading payload;
2. select only `active` entries whose lifecycle/canon class is eligible for the requested mode;
3. require exact resident ownership and current, digest-valid WP-4109/4110/4111 dependencies;
4. choose canonical material by default; provisional only in explicit review mode; experimental only in explicit experimentation mode; never rejected/retired for generation;
5. compose positive and negative fragments with later WP-4114/WP-4115 surfaces without changing their stored records;
6. emit a reproducibility receipt listing every revision/digest and authorization context;
7. log safe use metadata.

No eligible look returns `WARDROBE-NO-ELIGIBLE-LOOK`; runtime never falls back to another resident, another audience scope, or an invented generic outfit. If a current physical or fingerprint binding differs from the approved binding, return `WARDROBE-STALE-BINDING` and require re-review.

### 17.2 Predecessor integrations

- **WP-4108:** manifest registration, audience directories, provenance, canonical/candidate/rejected/superseded assets, lock eligibility.
- **WP-4109:** immutable measurement/height/build/silhouette reference and stale-binding checks.
- **WP-4110:** identity, hair range, visual fingerprint, recognition and forbidden drift.
- **WP-4111:** scale/camera/posture/footwear profiles and heel presentation.
- **WP-4112:** a comparison wardrobe snapshot can reference a look revision, but must freeze garments, fit, footwear, prompts, and hashes across A/B/C.
- **WP-4114/4115:** future composition of positive and global/resident negative canon; WP-4113 retains wardrobe-specific fragments.
- **WP-4116:** later Steward review/version framework may consume these records without weakening approval or audit requirements.
- **WP-4117:** completeness and canonical-lock validation consumes category, evidence, review, and active-canon status.
- **Campaign 05:** generation consumes approved library records and writes candidate assets; no schema redesign or implicit promotion is permitted.

## 18. Revision and rollback

Editing an approved or submitted revision in place is prohibited. A revision copies the prior record, increments `revision`, updates parent/replacement lineage and digest, resets workflow to `draft`, and records a bounded change summary. Dependent looks become stale until reviewed if a changed dependency affects their semantics.

Rollback is a new promotion event that reactivates an earlier immutable revision after validating its schema, authorization, dependencies, digests, and current safety. It never deletes intervening revisions or rewrites history. The event records trigger, initiator, Steward authorization, source and target revisions, affected assets/prompts/caches, dependency compatibility, and outcome. Promotion is atomic: if index update, audit append, cache invalidation, or dependency validation fails, the prior active canonical revision remains active. Emergency disable may make a look unavailable under existing authority but cannot silently declare another canonical.

## 19. Validation rules

Implementation must provide schema and semantic validation that accumulates deterministic, path-addressed diagnostics and exits nonzero on errors.

### 19.1 Structural and reference validation

- reject unsafe YAML tags, duplicate keys, aliases exceeding configured safe limits, unknown fields, malformed IDs/timestamps/digests, path traversal, symlinks escaping the root, and resident/scope/path mismatch;
- require all taxonomy entries exactly once, unique IDs, valid references, matching revision/digest, and no dependency cycles;
- require all look components, prompt pairs, fit rules, and risks; require signature design fields and evidence before canonical promotion;
- reject references to rejected/retired dependencies for active use and references from a less restrictive to a more restrictive scope.

### 19.2 Canon and physique validation

- exactly one active WP-4109 canonical physical specification is resolved; provisional bindings are permitted only for provisional/experimental wardrobe review;
- no wardrobe field may claim to update height, measurements, build, or facial fingerprint;
- fit and apparent-proportion claims must be described as presentation effects and agree across entry, fit, footwear, and prompt records;
- standing height remains unchanged by heel/platform metadata; unit conversion is tolerance-aware and never changes source values;
- resident IDs must match throughout; cloned content or identical signature semantics across residents triggers collision review rather than automatic acceptance.

### 19.3 Audience and workflow validation

- private-audience entries exist only under `private`, deny by default, and require explicit authorization/activation;
- lifecycle/canon pairs and transitions follow section 15; approval actor and attestation must authenticate as Steward;
- canonical promotion requires zero errors, current bindings, approved prompt pair, fit/footwear/accessory completeness, audience authorization, approved full-body and portrait evidence, decision record, and successful audit append;
- rejected and retired records are excluded from runtime selection but remain resolvable by audit/history tools;
- stale, missing, changed, or hash-invalid evidence blocks promotion and runtime canonical use.

### 19.4 Required diagnostic codes

| Code | Meaning |
|---|---|
| `WARDROBE-SCHEMA-INVALID` | structural/schema failure |
| `WARDROBE-ID-SCOPE-MISMATCH` | resident or layer disagrees with path/content |
| `WARDROBE-MISSING-FIT` | entry lacks complete fit rules |
| `WARDROBE-MISSING-SCOPE` | audience scope absent or invalid |
| `WARDROBE-MISSING-PROMPT` | positive or negative fragment absent/incomplete |
| `WARDROBE-CANON-CONTRADICTION` | wardrobe conflicts with physical/identity canon |
| `WARDROBE-STALE-BINDING` | referenced predecessor revision/digest is no longer active |
| `WARDROBE-HEEL-HEIGHT-MUTATION` | heel changes canonical height or is inconsistent |
| `WARDROBE-HEEL-REVIEW-MISSING` | required 3-inch comparison absent and not exempt |
| `WARDROBE-AUDIENCE-LEAK` | scope escalation or unauthorized content/reference |
| `WARDROBE-SIGNATURE-INCOMPLETE` | signature metadata/evidence/distinctiveness incomplete |
| `WARDROBE-CROSS-RESIDENT-COLLISION` | another resident's data/aesthetic is inherited or indistinguishable |
| `WARDROBE-ILLEGAL-TRANSITION` | lifecycle/canon transition invalid |
| `WARDROBE-UNAUTHORIZED-APPROVAL` | non-Steward or invalid approval attempt |
| `WARDROBE-HASH-MISMATCH` | persisted content/asset digest mismatch |
| `WARDROBE-AUDIT-FAILED` | required event could not be durably appended |
| `WARDROBE-NO-ELIGIBLE-LOOK` | no authorized active look; no fallback occurred |

Diagnostics contain code, severity, JSON/YAML pointer, record ID/revision, safe message, remediation, and correlation ID. Restricted payload values are redacted from broadly visible logs.

## 20. Complete Evelyn calibration example

> **Evelyn-specific example only — not a reusable template, default body, default aesthetic, or approval.** The following is a single provisional calibration direction exactly preserving WP-4113's authoritative physical specification. It does not make the measurements or look canonical and is subject to Steward confirmation.

```yaml
schema_version: estate.visual_bible.wardrobe.signature_looks.v1
record_id: sl-evelyn-white-linen-professional-relational-v1
revision: 1
resident_id: evelyn
audience_scope: internal
lifecycle_state: draft
canon_class: provisional
active: true
title: White linen professional-relational look
category: signature-look
contexts: [office-approachable, professional-relational]
physical_binding:
  authority: WP-4109
  status: provisional
  canonical_height: {imperial: "4 ft 10 in", metric: "147 cm maximum"}
  adult_scale: extremely petite adult
  measurements: "33B-21-31 provisional canonical measurements"
  silhouette: subtle hourglass
  invariant: clothing and footwear do not change these values
design:
  garments:
    - garment_type: dress
      fabric: {name: linen, color: white, behavior: natural light linen drape and restrained wrinkling}
      cut: tailored for an extremely petite adult frame without reshaping canonical measurements
      hemline: mid-knee
      neckline: elegant, understated, professional-relational
      sleeve: elegant, understated, context-appropriate
  footwear:
    style: heel appropriate to the dress and professional context
    heel_height: {value: 3.0, unit: in}
    platform_height: {value: 0.0, unit: in}
    posture_effect: document the presentation effect without changing 4 ft 10 in canonical height
  accessories: understated and resident-specific; subject to Steward selection
  hair: soft brunette hair with natural movement, coordinated without changing the facial fingerprint
  makeup: elegant but understated adult professional presentation
  pose: warm, approachable posture with a gentle head tilt
fit:
  fit_class: fitted
  tailoring_assumptions: custom petite tailoring; mid-knee placement is relative to Evelyn
  expected_apparent_effect: preserves extremely petite scale and subtle hourglass silhouette
  presentation_effects:
    shapewear: {used: false, effect: none specified}
    push_up_construction: {used: false, effect: none specified}
    structured_cups: {used: false, effect: none specified}
    padding: {used: false, effect: none specified}
    tailoring: {used: true, effect: clean petite fit only; no canonical measurement change}
  known_generation_risks:
    - {code: FIT-PETITE-SCALE-LOSS, mitigation: preserve 4 ft 10 in / extremely petite adult scale with WP-4111 references}
    - {code: FIT-SILHOUETTE-EXAGGERATION, mitigation: preserve subtle rather than exaggerated hourglass}
    - {code: FABRIC-LINEN-FAILURE, mitigation: retain believable linen drape and understated construction}
positive_prompt_fragment:
  adult_presentation: adult Evelyn in a professional-relational context
  garment: approved-direction white linen mid-knee dress
  fabric_behavior: natural linen drape, light restrained wrinkling, non-plastic texture
  fit_behavior: petite custom tailoring, fitted without body reshaping
  proportion_preservation: preserve 4 ft 10 in canonical height, extremely petite adult scale, provisional 33B-21-31 measurements, and subtle hourglass silhouette
  footwear_and_posture: 3-inch heels; warm approachable posture and gentle head tilt; heel effect is presentation only
  styling: elegant but understated
  camera_and_pose: use the applicable WP-4111 scale/camera profile and show uncropped footwear for full-body review
negative_prompt_fragment:
  identity_drift: [generic fashion-model substitution, loss of Evelyn-specific identity]
  proportion_drift: [taller body, average-scale body, altered measurements, exaggerated hourglass, heel height added to canonical height]
  garment_failures: [non-white dress, non-linen appearance, wrong hemline, revealing-by-default styling, ornate or overstated presentation]
  fit_failures: [adult infantilization, oversized proportions, painted-on fabric, tailoring that silently changes physique]
  footwear_failures: [wrong heel height, cropped feet, implausible posture, unsafe foot geometry]
  age_and_context: [minor-coded presentation, non-professional decontextualization]
evidence:
  full_body_asset: null
  portrait_crop_asset: null
approval:
  steward_confirmation_required: true
  steward_decision_id: null
  canonical_promotion_allowed: false
example_boundary: Evelyn-specific calibration example; must not be copied as another resident's template
```

The example deliberately leaves asset evidence and approval null. Therefore it must fail canonical-promotion validation while passing provisional authoring validation. Implementers shall use a resident-neutral fixture for general tests and keep this example explicitly Evelyn-specific.

## 21. Diagnostics and operator remediation

- **Look changes body shape:** compare physical digest and fit/prompt wording; remove implied body mutation, declare construction effects, regenerate evidence, and re-review.
- **Resident appears too tall in heels:** verify WP-4111 camera/floor line, heel/platform values, posture, and true-height invariant. Never compensate by changing canonical height.
- **Fabric looks plastic or cut drifts:** strengthen fabric behavior and garment-negative clauses; preserve identity/camera controls and create a new candidate.
- **Signature look is generic:** run cross-resident collision review, strengthen resident/role/fingerprint rationale, or leave it ordinary/provisional.
- **Private detail appears internally/publicly:** deny output, invalidate caches, record `WARDROBE-AUDIENCE-LEAK`, preserve evidence under authorized scope, and escalate under existing incident authority.
- **Dependency changed:** mark stale, retain old canonical for audit but exclude unsafe runtime use, revise/re-review against the new dependency; do not auto-migrate values.
- **Digest mismatch:** quarantine the affected revision/asset, block promotion/use, audit, and restore only from verified lineage.

## 22. Prohibited behavior and anti-patterns

The implementation must never:

- generate wardrobe or resident imagery as part of implementing this foundation;
- treat Evelyn's height, measurements, white dress, heels, or aesthetic as a template;
- silently fall back to another resident's look, measurements, fragments, or generic fashion defaults;
- infer measurements from garment size or rewrite physique from fit, padding, shapewear, camera, pose, or heels;
- call merge, file placement, schema validity, reviewer preference, or image attractiveness Steward approval;
- store restricted/private payload in public/internal indexes, logs, thumbnails, filenames, test snapshots, errors, or caches;
- use private scope to evade HR, Security, audit, or constitutional review;
- make revealing content a category requirement or conflate private/swim with explicit content;
- mutate approved records, decisions, rejected variants, or audit history in place;
- make `rejected` or `retired` content available to normal prompt resolution;
- publish a crop at lower restriction without authorization or use cropping to hide a defect;
- accept missing prompt fragments, missing fit effects, undocumented heels, stale hashes, or contradictory canon;
- let model-specific syntax overwrite model-neutral semantics;
- fabricate missing Steward decisions, physical values, resident preferences, safety exemptions, or evidence;
- weaken WP-4108 through WP-4112 or preempt WP-4114 through WP-4117.

## 23. Required unit tests

Implementation shall include, at minimum, isolated tests that:

1. accept one complete neutral resident-owned manifest and every taxonomy applicability value;
2. reject missing fit rules, scope, positive fragment, negative fragment, fabric behavior, fit behavior, proportion instruction, or adult presentation;
3. reject duplicate categories/IDs, unknown fields, malformed digests, unsafe YAML, path traversal, and scope/path mismatch;
4. reject another resident's physical, fingerprint, look, fit, footwear, accessory, or prompt reference;
5. reject wardrobe text that changes canonical measurements/height and reject heel-adjusted true height;
6. convert heel units consistently and require a 3-inch comparison or approved exemption where applicable;
7. validate all presentation-effect fields whether used or false;
8. reject incomplete signature design, collision review, full-body evidence, portrait evidence, or prompt pair for promotion;
9. permit Evelyn's example only as provisional and reject canonical promotion with null evidence/decision;
10. enforce legal lifecycle/canon pairs and transitions, one active canonical revision per signature ID, and exclusion of rejected/retired records;
11. authenticate Steward approval and reject forged/non-Steward decisions;
12. enforce scope monotonicity and private deny-by-default activation;
13. detect stale dependency and asset/content hash mismatch;
14. produce deterministic, redacted diagnostics without restricted payload;
15. preserve audit hash chaining, revisions, replacement links, and rollback history;
16. verify model overlays cannot alter identity, scope, or semantic requirements.

## 24. Required integration tests

1. Scaffold/validate a resident across all four existing WP-4108 layers without content leakage or unmanaged duplicate assets.
2. Resolve a canonical look through active WP-4109, WP-4110, and WP-4111 bindings and emit a complete reproducibility receipt.
3. Freeze one wardrobe revision across a WP-4112 A/B/C comparison and reject garment/footwear/prompt drift between variants.
4. Submit a provisional signature look, record revision request, approve a successor, atomically promote it, and retain the predecessor and events.
5. Fail a promotion mid-transaction and prove the previous canonical index and caches remain active and consistent.
6. Roll back to a compatible earlier revision through a new Steward decision and prove no history was deleted.
7. deny public/internal resolution of restricted/private material, authorize a time-bounded private activation, log safe metadata, deactivate, and invalidate cache access.
8. update a physical/fingerprint/scale dependency and prove the wardrobe becomes stale rather than silently rebinding.
9. compose wardrobe fragments with stubbed WP-4114/WP-4115 contracts without changing stored semantic content.
10. expose Campaign 05 consumption metadata for an approved candidate while proving no asset becomes canonical automatically.

Full-suite regression must also demonstrate that WP-4108 repository validation and WP-4112 focused tests continue to pass.

## 25. Validation scenarios

| Scenario | Expected result |
|---|---|
| Complete resident-specific office look | passes authoring validation; use depends on lifecycle/scope |
| Entry has garments but no fit rule | block with `WARDROBE-MISSING-FIT` |
| Positive exists, negative absent | block with `WARDROBE-MISSING-PROMPT` |
| Three-inch heel changes 4'10" to 5'1" in physical data | block with `WARDROBE-HEEL-HEIGHT-MUTATION` |
| Another resident references Evelyn's fit rule | block with cross-resident collision/reference error |
| Private look stored under internal | block with `WARDROBE-AUDIENCE-LEAK` |
| Valid private look in an ordinary session | deny without revealing payload |
| Steward likes a look but no signed decision exists | remain provisional; no promotion |
| Signature has portrait only | block canonical promotion as incomplete |
| Canonical dependency digest changes | mark stale; no automatic rebind |
| Rollback target is incompatible with current physical canon | block rollback and retain active revision |
| Evelyn example is copied into a neutral template | block cross-resident/default-template validation |
| Audit store is unavailable during promotion | fail closed with `WARDROBE-AUDIT-FAILED` |

## 26. Acceptance-criteria mapping

| WP-4113 acceptance criterion | Canon requirement and evidence |
|---|---|
| distinct library without inherited proportions/aesthetic | resident ownership, immutable bindings, collision checks, tests 4 and 16 |
| reproducible, identifiable signature looks | complete design and prompt schemas, evidence pair, reproducibility receipt, signature lifecycle |
| clothing cannot silently rewrite measurements | sections 2, 8, 19; contradiction and heel-mutation tests |
| heel height and posture documented | footwear schema, WP-4111 reference, comparison/exemption policy |
| four audience classes separated | layer-root layout, scope monotonicity, authorization and leakage integration test |
| Evelyn preserves petite white-linen direction | section 20 exact Evelyn-specific provisional example and promotion failure |
| supports Campaign 05 without redesign | stable manifests, schemas, evidence metadata, and explicit Campaign 05 integration |
| catches missing fit/scope/prompts/contradictory canon | required diagnostics, semantic rules, unit tests 2, 5, and validation scenarios |

## 27. Deliverable mapping

| WP deliverable | Implementation contract in this canon |
|---|---|
| wardrobe schema and taxonomy | sections 6-7 |
| repository directory standard | section 5 |
| signature-look schema | section 11 |
| fit/proportion schema | section 8 |
| footwear/accessory schemas | sections 9-10 |
| prompt and negative format | section 12 |
| Steward review/approval fields | sections 15-16 |
| completed Evelyn example | section 20, explicitly provisional and Evelyn-specific |
| validation tooling/tests | sections 19 and 23-25 |

## 28. Completion criteria for a later implementation

WP-4113 may be proposed complete only when a later implementation has:

1. created every versioned schema and documented canonicalization;
2. extended resident scaffolding with the scoped repository layout without migrating or exposing content incorrectly;
3. implemented safe parsing, structural/semantic validation, deterministic diagnostics, authorization, audit, resolution, promotion, revision, and rollback behavior;
4. supplied neutral templates and fixtures plus the Evelyn-specific provisional example without generated assets;
5. passed all required unit, integration, predecessor-regression, and applicable full-suite tests;
6. mapped each deliverable and acceptance criterion to files and test evidence;
7. demonstrated no physical, facial, scale, measurement-review, audience, or constitutional contract was weakened;
8. documented migration/compatibility and Campaign 05 consumption;
9. recorded all unresolved resident decisions as Steward decisions, not implementation defaults;
10. received required review and explicit Steward acceptance before any canonical lock or work-package completion claim.

Authoring this runtime canon satisfies none of those implementation completion conditions by itself.

## 29. Remaining Steward decisions

The implementation can proceed without inventing architecture, but the following content decisions remain intentionally unresolved and must not be defaulted:

- which categories are applicable and populated for each resident;
- each resident's actual wardrobe aesthetic, preferences, sizes/tailoring, safety constraints, accessories, and signature looks;
- exemptions from the 3-inch comparison requirement;
- approval, canonical promotion, rejection, retirement, or public declassification of any look or asset;
- whether Evelyn's white linen mid-knee dress direction becomes canonical, and its final neckline, sleeve, accessories, hair/makeup details, and evidence;
- authorization and substance for any private-audience wardrobe, including Evelyn private-mode content;
- retention periods or policy identifiers where existing Estate policy does not already specify them.

These are explicit review inputs, not placeholders in this specification.

---

**End of WP-4113 Supporting Runtime Canon and Design Specification**
