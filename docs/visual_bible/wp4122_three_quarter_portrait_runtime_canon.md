# WP-4122 Three-Quarter Portrait Runtime Canon

Status: Governing runtime standard, implementation complete; imagery and Steward decisions pending.  
Authority: Steward. Version: 1.0 (2026-07-21).

## 1. Scope and angle language

A three-quarter view is an oblique identity reference, not a loose aesthetic label. Body yaw is measured from the camera-facing frontal axis: front-left **-45°**, front-right **+45°**, rear-left **-135°**, and rear-right **+135°**. Each permits ±5°; pitch and roll are 0° unless a recorded diagnostic exception is under review. “Left/right” names the resident's visible/near side, never the viewer's. Front views expose facial depth and normally at least one complete eye; rear views prioritize rear skull/hair, ear edge, neck, shoulders, back, waist, hips, and silhouette and must not be replaced by a turned frontal glamour pose.

True frontal (0°), left/right profile (-90°/+90°), rear (180°), and these obliques form one linked turnaround. Three-quarter evidence must link the exact frontal, both profile, and rear source records used. It may interpolate geometry; it may not contradict, silently mirror, or overwrite those authorities. Conflicts are diagnostics requiring revision or Steward resolution.

## 2. Identity and anatomy invariants

Every view preserves the resident's adult identity, facial geometry, visual fingerprint, eye spacing/color, brow, nose, lips, chin, jaw, ears and asymmetries. Preserve hairline, part, length, color, texture, density, volume, fall and face overlap; never invent a hidden ear or normalize asymmetry. Preserve neck length/girth, shoulder width/slope, back/spinal line, torso, waist, hips, limb length/girth, hands/feet when visible, posture and characteristic silhouette. Rear references receive the same identity scrutiny as faces.

Canonical standing height, head-to-body ratio, measurements, apparent scale and footwear effects remain source-bound. Petite adults remain adults. The technical set uses a neutral stance, level pelvis, anatomically plausible spine, relaxed limbs, and balanced weight. A natural asymmetry is allowed only when sourced and recorded. The optional conversational set follows only after technical candidates and records resident-specific head tilt, gesture, stance and weight distribution; it may express character but cannot alter anatomy, height, scale or identity.

For front obliques record body yaw, head yaw, head pitch/roll, and eye direction separately. Eyes normally engage the camera while head/body relationships stay anatomically plausible. Rear obliques normally look away; a head turn that converts the image into a front oblique fails its angle. Hair occlusion is acceptable only when remaining signals sustain recognition.

## 3. Normalized capture

A matched four-view technical set uses one identity source revision, wardrobe, footwear, grooming, accessories, image dimensions, color treatment, background, lighting rig, camera height/distance, crop family, and focal length/equivalent field of view. Standard lens is 85mm equivalent (permitted 70–105mm), level camera, zero roll/pitch, recorded metric distance and height, matte neutral mid-gray background, soft neutral 5000–5600K lighting, and consistent exposure/white balance. Portrait and whole-body crops may be separate matched sets; do not mix them on one comparison sheet. Whole-body crops include crown and footwear. No perspective correction may alter proportions without a reproducible receipt.

Wardrobe items, garment fit, seams, hems and occlusion behavior must resolve to WP-4113 identifiers. Accessories retain side, size, placement and visibility; unresolved selections remain `pending`, never improvised. Camera, pose, orientation, crop, light/background, prompt revision, model/version, seed, sampler/settings, operator, time, source hashes, output hash and transformations are mandatory reproducibility data for generated evidence.

## 4. Prompt contract

The positive prompt follows the repository template order: resident/adult binding; authoritative source references; exact angle/tolerance; face/fingerprint; hair/ears/jaw/neck; shoulders/back/waist/hips/limbs; height/scale/silhouette; pose/weight; head/eyes; wardrobe/accessories; capture normalization; provenance request. Every resident-specific statement names its authority. Unknowns are explicit and generation-blocking where identity-critical.

The negative prompt must include the shared WP-4115 resident negatives plus the three-quarter template: wrong/generic identity, angle substitution, mirror/asymmetry, face/hair/body drift, anatomy defects, undocumented weight or pose, camera/crop/light/background drift, wardrobe/accessory drift, infantilization, sexualized posing, labels/watermarks and over-stylization. Negatives never establish positive identity.

## 5. Lifecycle, review, and recognition

Slots begin `pending_generation`; actual files may advance through `candidate`, `pending_review`, `approved`, and only then `canonical`. `rejected` and `superseded` are terminal noncanonical history (a revision creates a new candidate); `pending` directories hold unresolved work, not images presented as evidence. Candidate and canonical storage are physically separate. No placeholder, empty slot, review sheet, prompt, or validation report is an image.

Each angle receives automated/recorded diagnostics and independent Steward comparison against frontal, profile, rear, hero, full-body, facial-fingerprint, scale and wardrobe authorities. Review sheets use fixed scale/order and compare left/right pairs for identity drift, unintended asymmetry and capture mismatch. Revision notes state the defect, retained sources, predecessor, changed prompt/settings and expected correction. Canonical promotion requires all blocking checks pass, a matching asset/category/hash approval by the Steward, and manifest/catalog linkage. Rejection records retain reason and provenance; supersession links predecessor and successor.

A hidden-caption test presents shuffled assets without names, filenames, role, wardrobe-only clues or captions. The reviewer records expected/observed resident, confidence and rationale. A pass supports recognition; it does not itself approve canon. Failure or reliance only on clothing is blocking. The Steward may demand regeneration despite automated passes and is the sole canonical authority.

## 6. Records and repository organization

The manifest schema and asset sidecar schema live in `data/schemas/visual_bible/three_quarter/`. Templates live in `data/portraits/templates/`. Each active resident owns `data/portraits/residents/<key>/three_quarter/manifest.json` and separate `candidates`, `canonical`, `rejected`, `superseded`, `pending`, `metadata`, `reviews`, `comparison_sheets`, `generation_queue`, and `validation` paths. Naming is `{resident_id}__three-quarter__{set_type}__{angle}__v{revision:03d}__{asset_id}.{ext}`. Manifests are resident-bound; cross-resident template inheritance is forbidden.

Sidecars carry lifecycle, exact orientation, normalized camera/crop/pose, identity/anatomy/physical/wardrobe diagnostics, cross-angle links, prompts, generation settings, provenance, SHA-256, hidden-caption result, Steward review, canonical decision and lineage. Manifests carry four mandatory technical slots, optional conversational slots, source relations, normalization, lifecycle history and truthful unresolved state. Catalog links make the resident slot discoverable.

## 7. Validation, diagnostics, and tests

The validator rejects missing angles/sources, cross-resident binding, yaw outside tolerance, facing/side mismatch, invalid lifecycle, missing camera normalization, incomplete crops, absent geometry/continuity observations, missing assets, stale hashes, terminal canon, flagged canon and approval hash/angle mismatch. Diagnostics distinguish angle, identity, geometry/anatomy, scale/proportion, pose, gaze, crop/camera, light/background, wardrobe/accessory, provenance, recognition and approval failures. Failed or flagged blocking checks prevent promotion; machines do not infer aesthetic acceptance.

Unit tests exercise valid metadata and every major failure class. Integration tests validate all active-resident manifests, directory separation, four honest pending slots, catalog/portrait-slot linkage, schemas/templates and no canonical assets. Future generated fixtures must be small explicit test fixtures, never labeled resident canon.

## 8. Anti-patterns

Forbidden: calling 30° or 70° “45°”; viewer-relative side labels; mirroring a side; face-swapping onto an inconsistent body; changing lens/distance/crop between angles; using hair or clothing as the only identity signal; hiding anatomy with glamour posing; guessing measurements or occluded anatomy; conflating technical and conversational sets; promoting “approved” without Steward hash-bound approval; deleting rejection/supersession history; or treating generated filenames/placeholders as completed images.

## 9. Acceptance and completion

Runtime acceptance requires the canon, schemas, templates, four resident-bound slots, camera/pose/orientation records, source links, lifecycle storage, review artifacts, validator, fixtures/tests and traceability to pass. Visual acceptance for a resident additionally requires four generated technical candidates under matched conditions, passed identity/anatomy/normalization and hidden-caption checks, documented comparison/revision, and four independent Steward decisions. Conversational images are optional and never substitute.

WP-4122 repository/runtime implementation is complete when those mechanisms pass. The portrait-library visual completion condition remains pending until real assets are generated and independently accepted. This honest split satisfies the package without creating or labeling nonexistent final images.
