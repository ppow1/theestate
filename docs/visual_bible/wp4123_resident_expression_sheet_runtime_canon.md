# WP-4123 Resident Expression Sheet Runtime Canon

## 1. Authority, scope, and truth boundary
This canon governs comparison sheets for every active Estate resident and composes WP-4108 through WP-4116 identity, prompt, negative-prompt, review, and lock authority with WP-4118, WP-4119, and WP-4122 portrait sources. Character Bibles, resident profiles, office roles, and resident-presence authority remain primary; this system never infers private emotion, diagnoses state, or grants operational authority. An expression label is a production direction supported by cited canon, not a claim about what a resident feels.

No image or Steward approval is fabricated by this package. Every supplied manifest is `pending_generation`; an emotional anchor is a resident-specific provisional hypothesis until the Steward approves a hash-bound candidate. Evelyn's forward attentive coffee-conversation posture—warm eyes, relaxed shoulders, subtle listening tilt—is provisional and must not become a universal template.

## 2. Vocabulary and resident differentiation
The mandatory twelve are neutral resting, warm greeting, attentive listening, quiet smile, genuine laugh, thoughtful reflection, concern, encouragement, confidence, determination, mild amusement, and celebration/pride. Approved general directions may additionally use professional, warm, attentive, serious, concerned, amused, skeptical, reassuring, focused, or reflective only when translated into observable anatomy and supported by resident canon.

Resident extensions are: Alfred—formal attention, analytical skepticism, restrained approval; Ingrid—calm authority, precise correction, reserved warmth; Helen—compassionate HR conversation, professional interview, reassuring welcome; Eleanor—archival care, recollection, quiet satisfaction; Marie—curiosity, discovery, analytical concentration; Judy—skeptical counsel, careful consideration, measured agreement; Grace—operational briefing, decisive prioritization, leadership under pressure; Evelyn—coffee conversation, gentle encouragement, quiet reflection, warm welcome, proud smile. These vocabularies cannot be inherited across residents.

## 3. Facial performance and mature presentation
Each direction specifies eyes/lids/gaze, brows, mouth corners/lips/teeth, cheeks, jaw tension, head yaw/pitch/tilt, shoulders, and posture. Neutral uses relaxed lids and jaw; attention uses steady gaze and slight forward availability; warmth may soften eyes/cheeks with a restrained mouth rise; seriousness/focus limits brow and mouth movement; concern permits brief brow knitting without distress caricature; amusement begins in eyes/cheeks before a resident-calibrated smile; skepticism uses controlled brow/eye and head behavior; reassurance preserves relaxed jaw and open posture; reflection may move gaze modestly off camera. Head motion stays small and anatomy-preserving.

Micro-expressions are onset or low-amplitude changes—eye softening, slight brow lift, restrained grin, beginning laugh, looking up from work, brief pre-speech concern, subtle tilt, recognition, controlled skepticism, or private amusement. Metadata intensity is only `none` or `subtle`. Adults remain unmistakably mature: preserve age markers and skin texture; prohibit infantilization, sexualization, cosmetic smoothing, or age/demographic change. Grooming, wardrobe, posture, restraint/openness, and relationship distance must align with the Character Bible and office role.

## 4. Identity and comparison controls
Across cells preserve eye shape/spacing/color/lids; nose, mouth, cheek, jaw and ear geometry; skin tone/texture; age; hairline/part/length/color; visual fingerprint; and approved asymmetry. Reject caricature, stock smiles, personality substitution, demographic/age drift, changed identity, malformed anatomy, forced affect, contradiction of label, duplicated frames, or artifacts.

Lock an 85 mm-equivalent lens (permitted 70–105 only when consistently recorded), camera position/distance/height, square dimensions, head-and-shoulders crop and head scale, soft neutral 5000–5600K light, matte mid-gray background, hairstyle, grooming, wardrobe neckline and accessories. Only expression, a small natural head adjustment, and approved micro-gesture vary. Core layout is 4×3, role layout 3×1 or extended ordered grid, micro layout 5×2. Captions name resident and slot outside the image. Hidden-caption testing randomizes cells and requires resident plus intended-expression recognition without caption leakage; results remain pending until actually run.

## 5. Prompting, provenance, and lifecycle
Positive prompts compose resident binding, hashed canonical sources, facial fingerprint, mature adult/role presence, expression label, observable facial actions, restrained micro-action, head/posture, normalization, wardrobe/grooming, and rendering. Negative prompts compose identity/age/demographic/personality drift, generic or exaggerated expression, anatomy/artifact, professional-safety, and normalization exclusions. Never use another resident as a style template.

Every asset sidecar records source identities/hashes, prompt and negative revisions, model/version, seed, sampler/settings, operator/time, software/environment, asset hash, facial actions, claimed-vocabulary support, normalization, drift results, recognition result, and lineage. Reproduction must resolve all sources and replay recorded settings; nondeterminism is declared, not hidden.

Lifecycle is candidate → canonical, rejected, or superseded. Revision creates a new ID/hash with predecessor link; rejection is immutable evidence; supersession links both directions and never deletes history. Steward Notes bind reviewer, timestamp, asset/sheet hash, slot, observation, requested revision, and decision. Only explicit Steward approval bound to resident, asset hash, and expression can promote; automated validation never approves. Rejected/superseded, drift-flagged, unsupported-claim, failed hidden-caption, or unreviewed assets cannot be canonical.

## 6. Validation, diagnostics, and anti-patterns
Validators fail closed on missing core/role/anchor slots; cross-resident binding; absent or exaggerated micro metadata; unsupported emotional claims; missing facial channels; unlocked normalization; stale hashes; missing identity fields; terminal promotion; drift flags; failed/missing hidden-caption test; or absent/mismatched Steward approval. Diagnostics identify resident, asset, expression, rule, severity, and remediation. Anti-patterns include one smile scaled twelve ways, universal Evelyn pose, prose-only emotion, label leakage, best-effort canonical flags, approval by filename, mutable sidecars, crop changes that simulate emotion, beauty filtering, and treating a model seed as identity evidence.

## 7. Acceptance mapping and completion
| Acceptance | Persistent evidence |
|---|---|
| Every resident/core taxonomy | Eight `expressions/manifest.json` files and catalog links |
| Resident-specific roles/anchor | Per-resident vocabulary and pending anchor record |
| Restrained micro-expressions | Ten manifest micro records plus validator |
| Comparable presentation | Normalization and layout records/templates |
| Stable identity/no generic stock | Sidecar drift fields, negative template, fail-closed validator |
| Steward feedback/approval | Pending review ledgers and hash-bound promotion gate |

Runtime completion requires schemas, manifests, templates, repository lifecycle buckets, validators, fixtures/tests, traceability, and truthful pending states. Visual completion additionally requires generation of all sheets, reproducibility receipts, automated QA, hidden-caption testing, and independent Steward decisions. Until those occur, implementation is complete but expression imagery and canonical status are pending.
