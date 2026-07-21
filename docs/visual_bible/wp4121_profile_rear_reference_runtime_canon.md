# WP-4121 Profile and Rear Reference Runtime Canon

**Status:** Canonical runtime standard v1.0. **Authority:** Steward. **Scope:** all active commissioned adult residents.

## 1. Purpose and governing principles

This standard proves that the same resident survives non-frontal views and supplies continuity evidence for later turnaround, wardrobe, animation, and group-scene work. Identity evidence, not attractiveness, governs. It extends WP-4108–WP-4116 and WP-4120 without redesigning them; it is not the Campaign 03 360-degree workflow and does not select measurement variants. Every resident is an adult. Rear references are neutral artist references: never sexualize, fetishize, or overemphasize anatomy. Restricted/private sources and wardrobe remain in their governed layer.

A record is evidence only when a real image has a hash-bound sidecar, validation, and review record. No generated image or Steward review means `pending_generation`/`pending`, never a placeholder presented as complete.

## 2. Classifications, slots, and repository convention

A **true profile** is nominally 90° yaw with the face/body side named from the resident's side; deviations must be recorded. A **rear** is nominally 180°. An applicable **intermediate angle** is rear three-quarter left/right, nominally 135°/225° (or signed equivalent), recorded rather than inferred. Do not flip an image to create its opposite side.

Each manifest requires independently reviewable slots: left/right facial profile; left/right full-body profile; rear head-and-shoulders; rear full-body; rear three-quarter left/right; rear hair/silhouette; and rear posture/shoulders. Matched sheets include the first eight with identical normalization and labels. `rear_hair_silhouette` and `rear_posture_shoulders` may share a source image only through separate category review records.

Use `data/portraits/residents/<resident-key>/profile_rear/{candidates,canonical,rejected,superseded,comparison_sheets,metadata,reviews,validation,generation_queue}`. Filename: `{resident_id}__profile-rear__{category}__{crop}__v{revision:03d}__{asset_id}.{ext}`; the sidecar uses the same stem plus `.json`. Asset IDs and revisions are immutable. Candidate and canonical paths are separate; folder names alone never confer state.

## 3. Identity, geometry, height, and silhouette

Bind each prompt/receipt to that resident's Visual Bible, facial fingerprint, approved hero/office evidence when it exists, WP-4120 full-body record, and wardrobe source. Both sides must be independently generated and reviewed. Preserve intentional asymmetry and document unknown asymmetry as pending; symmetry normalization, mirroring, generic faces, and cross-resident inheritance fail.

For applicable profile/rear crops record observations for nose projection/bridge/tip, lips and occlusion, chin projection, jaw angle, brow/forehead, visible ear shape/placement, hairline/temple, neck length/angle, shoulder line, spinal/back contour, habitual posture, whole silhouette, and every canonical distinguishing feature. A hidden feature is `not_visible`, not invented. Rear views preserve hair length, density, texture, part, fall, movement, grooming, and how hair occludes ears, neck, clothing, or accessories.

Whole-body references preserve barefoot canonical height, head-to-body ratio, shoulder/waist/hip relationship, torso/leg and limb proportions, stance, center of gravity, and floor contact. Portrait crops must include crown/hair, the required facial or rear-head geometry, neck, and complete shoulders with breathing room. Whole-body crops include crown/hair through both complete feet/footwear with at least 5% top/bottom clearance. Do not infer cropped anatomy.

## 4. Wardrobe, grooming, accessories, posture

Select opaque, role-appropriate, source-bound wardrobe. Record garments, seams, hems, closures, fit and material behavior; footwear type/heel and resulting posture; grooming; jewelry, eyewear and other accessories; visible/occluded state; and access tier. All matched views use the same approved selection. Unresolved choices remain `pending_steward`, never invented. Clothing discontinuity, impossible closures, changed footwear, accessory side swaps, hair discontinuity, sexualized posing, exaggerated spinal curve, or anatomy emphasis fails.

## 5. Camera and scene normalization

Target 85 mm full-frame equivalent, permitted 70–105 mm, at a matched recorded distance. Record sensor/crop factor or equivalent, focal length, distance, eye/camera height, exact yaw/pitch/roll, aspect ratio, resolution, lens correction, and crop. Keep pitch and roll level; align eye level to crop center for portraits and mid-torso for whole body. Use a level visible floor for whole-body work, matte neutral mid-gray background, soft neutral 5000–5600 K light, restrained fill, neutral expression, and matched camera/light/background/pose for comparison.

Perspective, floor, shadow, crop, or lighting changes must be diagnosed. A documented non-normalized creative view can be a candidate but cannot satisfy a normalized required slot.

## 6. Prompts, references, provenance, and reproducibility

Compose positive prompts in governed order: resident/source bindings; adult status; exact angle/pose; applicable visible geometry and asymmetry; height/proportions; wardrobe/footwear/grooming/accessories; camera/crop; light/floor/background; reference-image roles; reproducibility settings. Compose negatives as WP-4115 global + profile/rear base + category adapter + resident extension. Required failure terms cover wrong side/frontality, mirroring/text, identity/geometry/hair drift, malformed ears/hands/anatomy, duplicate/missing limbs, crop, height/proportion/posture drift, clothing/footwear/accessory discontinuity, distortion, sexualization, and false canon. Extensions never remove global terms.

Reference images must be access-authorized and recorded by asset ID, SHA-256, lifecycle state, crop/category, influence/weight, preprocessing, and exact purpose. A candidate is not silently treated as canonical truth. Receipts record generator, model/version/checkpoint hash, adapters and hashes, seed, sampler/scheduler, steps, guidance, dimensions, denoise, software/hardware, prompt-template versions and resolved prompts, source hashes, operator, UTC time, and output hash. Unknown legacy values are explicit; missing required generation provenance blocks promotion.

## 7. Lifecycle and Steward workflow

States are `pending_generation`, `candidate`, `pending_review`, `approved`, `canonical`, `rejected`, and `superseded`. `approved` is not canonical. Rejection needs reason/finding links. Supersession preserves predecessor/successor/hash lineage. Only a hash/category/resident-matched Steward `approve` decision with no blocking findings may promote exactly one asset per slot. Each angle is approved independently.

Workflow: generate into `candidates`; run schema/hash/objective checks; assemble normalized comparison sheet; conduct geometry, continuity, identity and hidden-caption review; Steward approves, rejects, or requests revision per angle; revise as a new immutable asset/version; promote approved hash to `canonical` with decision receipt; retain rejected/superseded lineage. Hidden-caption testing supplies the candidate without resident caption and records reviewer guess, confidence, comparison references, outcome and date; it is pending until a human actually performs it.

## 8. Persistent records, diagnostics, and validation

The manifest schema defines slots, paths, sources, normalization, comparison state, candidates, canonical resolution and review history. The asset schema binds image, prompt, camera/pose, crop, geometry, identity, physical continuity, wardrobe/grooming, provenance, lineage, hidden-caption result, validation and review. Review records bind resident/category/asset/hash. Validation reports never replace these records.

Diagnostics name resident/category/asset, rule code, severity (`info`, `warning`, `error`), observed/expected value, authority/tolerance, blocking status, and remediation. Validate schema; deterministic names/paths; hashes; all slots; side/category/yaw; crop; camera/light/floor/background matching; identity/facial geometry; height/proportion/posture; hair/wardrobe/footwear/grooming/accessories; reference authorization; generation receipt; hidden-caption state; lifecycle separation; lineage; and Steward decision binding.

## 9. Tests, scenarios, and anti-patterns

Unit tests cover category completeness, pending honesty, resident binding, geometry fields, camera angles, crops, hashes/provenance, continuity diagnostics, lifecycle and category-bound Steward approval. Integration tests load all active residents through the Estate portrait catalog. Validation scenarios include independently distinct left/right profiles, rear hair continuity, whole-body height/crop continuity, matched comparison settings, hidden-caption recognition, rejection/revision/supersession, and valid promotion.

Anti-patterns: mirrored opposite sides; generic beauty templates; invented invisible features; false or text placeholders; filename canon; candidate/canonical co-location; approval without hash/category; one blanket approval; unrecorded reference images; missing seed/settings; fashion crops; wide-angle views; inconsistent hair/seams/shoes/accessories; sexualized rear pose; hidden-caption results claimed without testing; and treating WP-4121 as the 360/measurement-lock workflow.

## 10. Acceptance mapping and completion

All active residents must have all ten slots represented or honestly pending. Identity-recognition, asymmetry, hair, posture, stature, wardrobe and proportion acceptance requires real imagery and Steward review; until then its status is pending, not failed or complete visual evidence. The implementation is complete when canon, schemas, deterministic repositories/manifests, templates, validator, fixtures, tests, report, receipt, catalog/index links and traceability pass. **Reference-library completion remains pending** until every required category has real reproducible evidence, passes hidden-caption/continuity review, and receives independent Steward decisions. This distinction is mandatory.
