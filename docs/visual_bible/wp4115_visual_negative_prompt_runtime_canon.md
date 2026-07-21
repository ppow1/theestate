# WP-4115 Visual Negative Prompt Runtime Canon

**Status:** Canonical implementation contract, version 1.0  
**Classification:** Estate Internal  
**Authority:** WP-4115, subordinate to Steward decisions and merged WP-4108—WP-4114 canon.  
**Effective baseline:** `847ad40`, merge PR #445 completing WP-4114 and all declared predecessors.

## 1. Purpose, invariant, and authority

This canon prevents recurring generation defects through auditable, model-neutral rules. **Negative prompts supplement rather than replace positive identity instructions.** Every resident request must bind approved positive identity instructions; exclusions only protect those affirmatively stated facts. Absence or ambiguity never becomes permission to infer identity.

Authority is: Steward decision; governance; active resident physical, facial, scale, measurement and wardrobe canon; WP-4114 positive prompt canon; this canon; active rules; adapters; requests. A lower layer cannot weaken a higher one. The runtime validates records and composes text; it does not generate or approve images.

## 2. Layer architecture and asset coverage

Composition combines in order: global rules, asset template, resident extensions, wardrobe binding, request-specific reviewed rules, then syntax-only adapter. Global rules cover anatomy, identity/age/scale/proportion/appearance drift, rendering, artifacts, framing, and professional presentation. Templates exist for portrait, full-body, turnaround, icon, group, movement, environment, wardrobe, and comparison. `all` rules always apply. More specific rules add protection and cannot subtract global rules.

Resident extensions protect face shape; adult age range; height; build/measurements; facial visual fingerprint; posture; signature expression; hair length/texture/color; eye shape/color; distinguishing features; and explicitly governed forbidden resemblance to other residents. They contain positive identity binding IDs and resident ownership. Never encode an unsupported fact merely as a negative.

Wardrobe controls prohibit garment, fit, color, footwear, heel and signature-accessory drift. Clothing cannot mutate physique or standing height. Restricted adult presentation or grooming data belongs only in restricted/private scoped records with explicit authorization and provenance—not public/internal rules or unrelated documents.

## 3. Comparison, turnaround, and group controls

Comparison locks camera angle, pose, expression, wardrobe, heel height, lighting, focal length, orientation, framing, scale and visible waist/hips/shoulders/legs. Exactly one declared comparison variable may change; perspective cannot mask it. Turnaround permits only declared orientation across the governed views and locks identity, grooming, expression, wardrobe, camera distance, lens, lighting, background and scale. An intended difference that the Steward cannot reliably see fails and regenerates; schema validity is not visual acceptance.

Groups require two or more independently bound identities, resident-specific extensions, placement and relative-height maps. Protections prohibit blending/swapping/repeated faces, duplicate bodies, inherited hair/build/height/wardrobe, pose/expression homogenization and lost posture/interpersonal behavior. Shared scene text cannot replace any resident identity.

## 4. Schema, provenance, scopes, and adapters

A rule records immutable ID, category, semantic text, applicable assets, audience, lifecycle, severity, positive bindings, supersession link and provenance source IDs/UTC creator/time. A prompt set records residents, asset, positive identity bindings, rule IDs, adapter and provenance. Observations bind the generation receipt, evidence reference, defect category, implicated rules, observer/time/scope, state and remediation.

Scopes are monotonic `public < internal < restricted < private`; composition may consume only equal or less restrictive data. Diagnostics expose IDs/codes, never protected text. Restricted metadata remains discoverable to authorized audit and is deny-by-default to broader audiences.

Adapters translate validated semantics into an engine's separate negative channel, inline exclusion syntax, token weights, API fields, or control graph. They pin an engine family/channel/separator and unsupported behavior. They preserve order, IDs, meaning, scope and digest; `semantic_overrides` must be empty. An engine lacking an equivalent control returns `review_required` or error—never silently drops a rule.

## 5. Defect taxonomy and remediation lifecycle

Taxonomy: anatomy; identity; age; scale; proportion; appearance; rendering; artifact; framing; comparison; wardrobe; group separation; movement; environment. Anatomy explicitly includes extra, duplicated, fused, missing or malformed limbs, hands, fingers, feet, toes, joints, heads, faces, teeth, ears, eyes and hairlines.

Lifecycle is `observed → triaged → candidate_rule → validated → promoted → closed`, with `rejected` terminal when unsupported. Record the original receipt and audience-matched evidence; reproduce where safe; determine whether positive identity, rule, adapter or workflow failed; propose the narrowest rule; test against the triggering case and non-regression corpus; obtain required review; then publish a new immutable rule revision. Promotion requires candidate rule ID, provenance, tests and resolver update. Never edit history or turn one unexplained artifact into global policy.

## 6. Contradictions, diagnostics, and validation

Higher authority wins. Equal-authority contradiction blocks composition as `NEG-CONTRADICTORY-RULE` pending human review; specificity may add but not negate. A negative contradicting positive canon is an error, not an adapter concern. Stale provenance or unsupported engine syntax is `review_required`. Nonessential advisory coverage may warn. Missing anatomy/category/asset/template/positive identity/resident protection, scope leakage, cross-resident binding, semantic adapter override, missing rule and incomplete promoted observation are errors. Errors fail closed; warnings are recorded; review-required output cannot become canonical.

Validation checks schemas, duplicate IDs, all nine asset templates, global categories, every named anatomy term, resident protections and positive bindings, scope, ownership, adapter immutability, specialized controls, provenance and lifecycle. Composition is deterministic and produces ordered IDs, per-rule SHA-256 digests and a composition digest.

## 7. Revision, supersession, rollback, retirement

Approved rules and observations are append-only. Revision creates a new ID/version with `supersedes`; validation and review precede atomic resolver activation. Superseded records remain reproducible. Rollback creates another revision restoring compatible earlier semantics and cites the rollback decision; it never deletes or rewinds evidence. Retirement removes a rule from ordinary resolution after impact review, while receipts keep resolving the historical version. Failed activation retains the prior resolver.

## 8. Tests and validation scenarios

Unit tests prove schemas, complete global taxonomy/anatomy language, nine templates, resident protection keys, mandatory positive identity, semantic adapter immutability, deterministic digesting and promotion evidence. Integration tests load the global library/templates/adapter, compose two independently protected residents in a group, reject missing positive identity and scope/cross-resident violations, and run the existing WP-4108—WP-4114 suites.

Scenarios: valid portrait/pass; anatomy term removed/error; comparison with declared variable and locks/pass; missing lock/error; turnaround orientation-only/pass; group with two identity/height/placement maps/pass; blended or missing identity/error; restricted extension in internal request/security error; unsupported adapter/review; defect observed/triaged/pass; promotion without candidate/provenance/error; retired rule requested/error; contradictory active rules/review-block; unchanged inputs/stable digest/pass.

## 9. Anti-patterns

Do not use negatives instead of positive identity; concatenate unvalidated free text; copy one resident's extension to another; bury restricted metadata; weaken anatomy for token limits; use “not X” to invent X; encode scene preferences as identity; silently drop unsupported syntax; let adapters alter semantics; edit approved rules/receipts; globally promote a one-off defect; accept comparisons with uncontrolled variables; treat validation as Steward approval; delete rejected evidence.

## 10. Acceptance mapping and completion

1. Global plus resident extensions and positive bindings cover every live resident through the neutral extension contract.
2. Nine templates cover every requested asset class.
3. Comparison/turnaround templates declare variable and locks.
4. Group template and runtime require separate identities and separation protection.
5. Canon and adapter interface are engine-neutral and fail on semantic override.
6. Observation schema/lifecycle promotes defects durably with provenance.
7. Audience fields, scoped paths and fail-closed checks prevent covert burial.

WP-4115 is complete when canon, three schemas, global library, nine templates, resident extension, adapter, observation example, validator/composer, tests, report and receipt exist; focused and applicable regressions pass; and no image, Steward approval, resident-specific restricted fact or model capability is fabricated.
