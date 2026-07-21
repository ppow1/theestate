# WP-4120 Full-Body Reference Library Runtime Canon

**Status:** Canonical runtime standard v1.0  
**Scope:** Campaign 02, all active commissioned adult residents.  
**Authority:** Steward approval is required for every canonical promotion.

## 1. Purpose and boundary

The library is the reproducible whole-person identity baseline: it preserves resident-specific height, silhouette, posture, limb proportion, scale, wardrobe behavior, footwear, and facial identity across later generation. It is not a beauty gallery and no resident may inherit another resident's body template. It does **not** run Campaign 03's three-nearby-measurement, 360-degree comparison, turnaround, or physical-lock exercise. A single WP-4120 category may show a canonical specification; it must not present A/B/C measurement variants.

All subjects are adults. Silhouette-readable, normally fitted role-appropriate clothing is required; explicit, transparent, fetishized, underwear-only, or clinically nude reference imagery is forbidden. Review-only material is Estate Internal or more restrictive. Public release is a separate approval; Evelyn's ordinary records retain her restricted registry classification. Prompts and metadata must not disclose restricted/private identity material to a broader audience.

## 2. Required categories and slots

Each resident manifest contains distinct `candidates/` and `canonical/` slots for:

1. `neutral_front`: balanced, neutral standing front view;
2. `relaxed_front`: natural relaxed front stance, with changed weight distribution recorded;
3. `three_quarter`: standing front three-quarter view;
4. `side`: true full side profile;
5. `rear`: true rear standing view;
6. `walking`: natural mid-stride pose, with gait phase recorded;
7. `seated`: role-appropriate seated pose with feet and support visible;
8. `signature_pose`: resident-specific and source-grounded, never a shared default;
9. `scale_reference`: neutral pose beside approved fixed dimensional cues; and
10. `footwear_variant`: standardized comparison pose with footwear and heel height recorded.

Evidence means a real image with a complete, hash-bound sidecar and review record. Otherwise the category state is honestly `pending_generation`; an empty slot is not evidence. Candidate records can never resolve through the canonical slot.

## 3. Capture normalization and whole-body crop

Use a full-frame-equivalent 70–105 mm portrait intent (85 mm target), camera far enough to contain the figure without wide-angle elongation, sensor parallel to the resident's coronal plane for normalized views, and camera eye level at the subject's mid-torso/waist height rather than tilted up or down. Record actual or equivalent focal length, camera distance, camera height, pitch, yaw, roll, aspect ratio, and whether lens correction was applied. Perspective compression must not conceal limb relationships.

The floor is level, continuous, visible beneath both feet, and intersects the declared scale cue consistently. Use a matte neutral mid-gray background, soft neutral 5000–5600 K illumination, restrained fill, no dramatic rim light, and no shadows that merge limbs. Camera, floor, background, and light remain fixed across normalized categories unless the pose requires documented deviation.

Every frame must include the complete crown and all hair, face, neck, torso, both arms/hands (unless anatomically occluded and documented), pelvis, both legs, ankles, and the entirety of both shoes/feet. Maintain at least 5% frame-height clearance above crown/hair and below the lowest footwear/floor contact; target 8%. Do not repair a failed crop with inferred or outpainted anatomy without declaring a newly generated candidate and provenance.

## 4. Fidelity, posture, wardrobe, footwear, and scale

The manifest links authoritative physical, face/fingerprint, height/scale, and wardrobe sources. Preserve documented standing height, head-to-body relationship, shoulder/hip silhouette, torso-to-leg and upper/lower-limb relationships, habitual posture, and adult presentation. Unresolved values stay unresolved and go to Steward review; prompts must not invent them.

Wardrobe must be individually sourced, opaque, role-appropriate, fitted enough to assess silhouette without changing canonical anatomy, and recorded by wardrobe reference, garment set, fit, material behavior, and access tier. Each shoe is recorded by type, sole/heel form, exact or pending heel height, and source. A heel changes effective standing height, pelvic tilt, knee behavior, center of gravity, leg line, and stance: metadata must separate barefoot canonical height from footwear-added height and document observed/intended posture effects. Silent shoe substitutions or heel changes fail validation. At least one applicable adult female resident category uses a documented heel of 3 inches or greater; applicability and execution require source-grounded Steward review and remain pending rather than invented.

Scale references use an approved, dimensioned cue (for example a calibrated height board, floor grid, or fixed architectural datum), recording cue ID, dimensions/units, resident-to-cue placement, floor contact, camera calibration, and source. Furniture without verified dimensions and doors/baseboards of assumed size are not measurement evidence. Apparent scale must agree across categories within the declared validation tolerance; unexplained drift is flagged.

## 5. Lifecycle, prompts, metadata, and provenance

States are: `pending_generation` (no image), `candidate` (noncanonical review asset), `pending_review` (complete candidate awaiting Steward), `approved` (approved for stated use but not necessarily canonical), `canonical` (hash-bound Steward promotion), `rejected`, and `superseded`. Rejection records a reason; supersession records predecessor/successor; neither may resolve as canon. Canon requires one approved asset per category, an image hash, matching sidecar and Steward decision, and no blocking validation findings.

Positive prompt template: `[resident_id and resident-specific identity sources]; adult; [category pose]; preserve documented height, silhouette, posture, limb proportions and facial fingerprint; [wardrobe source/garments]; [footwear type and heel height/effect]; complete body, crown/hair and both shoes visible with clearance; 85 mm full-frame-equivalent orthographic portrait intent; level camera at mid-torso; level visible floor; neutral mid-gray background; soft neutral standardized light; [dimensioned scale cue when applicable]; realistic anatomy and material behavior.` Never substitute prose from another resident.

Negative prompt template: `cropped feet, cropped shoes, cropped crown, cropped hair, missing body region, hidden limbs, malformed anatomy, extra or missing limbs/digits, incorrect footwear, undocumented heel, altered height, shortened or elongated limbs, generic shared body, cross-resident identity, childlike presentation, wide-angle distortion, foreshortening, dutch angle, camera tilt, floating feet, broken floor contact, false scale cue, dramatic light, busy background, explicit nudity, clinical nudity, transparent clothing, candidate presented as canonical, watermark, text.` Resident-specific negatives extend rather than replace the governed WP-4115 taxonomy.

Every asset sidecar records schema/version, resident/category/asset IDs, lifecycle and access, asset path and SHA-256, source references, prompt and negative-prompt template revisions, generator/model/version, seed/settings or an explicit unknown legacy value, creation time/operator, camera/lens, crop/body-region assessment, pose, canonical measurements used, wardrobe/footwear and heel effects, scale cue, lineage, validation report, and review record. Missing provenance is blocking. Generated imagery must never be fabricated; a pending manifest contains no fake path/hash/settings.

## 6. Steward review, validation, and diagnostics

The Steward may `approve`, `reject`, `request_revision`, or `supersede`; `pending` is the honest initial state. Each decision names resident, category, asset and hash, reviewer authority, date, notes, and blocking/nonblocking findings. Approval for access or candidacy is distinct from canonical promotion.

Validation checks schema, provenance, hash/path, resident isolation, all ten categories, lifecycle/canonical resolution, Steward state, camera and floor metadata, full crown/hair and body-region coverage, both full feet, wardrobe/footwear and heel effects, physical-source links, scale cues, perspective, identity, height, proportion, and posture. Objective metadata violations reject; visual judgments may be `pass`, `flag`, or `fail`, but blocking flags prevent canon. Diagnostics identify resident/category/asset, rule code, severity, observed value, authority/tolerance, and remediation. Reports cover height, proportion, posture, crop, scale, identity, footwear, provenance, and review.

## 7. Tests, anti-patterns, and completion

Tests must prove complete pending coverage and rejection/flagging of cropped feet or crown/hair, missing major regions, bad or undocumented footwear, unexplained heel/posture changes, scale drift, perspective distortion, false canon, cross-resident template inheritance, missing review state, and missing provenance. Also test valid hash-bound Steward promotion.

Anti-patterns include placeholders disguised as images, text-only concepts called evidence, generic body/pose inheritance, invented measurements, hidden feet, fashion crops, uncalibrated furniture scale, undocumented lens or footwear, canon by filename/folder, approval without hash, and Campaign 03 A/B/C comparison content.

WP-4120 runtime and repository implementation are complete when this canon, schemas, templates, per-active-resident directories/manifests, validator, reports, tests, and traceability pass. Image-production and canonical-reference completion remain pending until every category has real evidence, validation, and Steward review; implementation completion must not claim asset completion.
