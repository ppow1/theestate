# WP-4117 Visual Bible Acceptance and Canonical Lock Runtime Canon

**Status:** Runtime canon v1 · **Authority:** Steward · **Scope:** every resident Visual Bible and downstream visual asset.

## 1. State model and authority boundary

`exploratory` is unreviewed investigation; `candidate` is submitted evidence; `preferred` is the Steward's current comparison preference; `provisional` is explicitly usable only within its recorded limits; `canonical` is an explicitly locked version; `superseded` is retained former canon; and `rejected` is retained, unusable evidence. Rejected and superseded are terminal. Every promotion through preferred, provisional, canonical, rejected, supersession, or rollback requires an attributable Steward disposition. Automation may report `eligible_for_steward_review`; it **never** grants canonical status. Silence, use in production, a score, schema validity, or file placement is not approval.

## 2. Formal acceptance evidence

A lock binds versioned, SHA-256-addressed physical, facial, wardrobe, asset, positive-prompt, and negative-prompt specifications. The human checklist and machine record must agree. Evidence proves the same adult resident across hero, headshot, profile, full-body, expression, monochrome, icon and five turnaround angles. Hidden-caption review must recognize the resident from stable face geometry, eyes/hair, posture, expression and behavioral cues rather than clothes alone. Height, frame, measurements, proportions, anatomy, posture and footwear-adjusted presentation must agree; facial age, geometry, fingerprint and subtle artistic intent may not drift or become a demographic claim. Wardrobe must fit the resident specification and cannot modify anatomy.

Prompt evidence records provider/generator, model family and version, checkpoint, seed, adapters/LoRAs, reference hashes, controls, positive/negative prompt hashes and known failures. Test two supported workflows/model families when available; if only one exists, the limitation is blocking unless the Steward explicitly records a narrowly tolerated limitation. A tolerance states impact, boundary, mitigation, revalidation trigger, expiry/review date and explicit Steward acceptance; it never waives identity, adult status, authority, provenance, access, or hash integrity.

## 3. Completeness and group readiness

The asset gate requires hero, headshot, profile, full-body, front/front-three-quarter/side/rear-three-quarter/rear turnarounds, expressions, black-and-white, thumbnail, icon, prompt records, Steward Notes and revision history, plus a comparison sheet when required. A reserved path describes future work and cannot satisfy a canonical lock. Present entries require IDs, paths and verified content hashes; `not_applicable` needs rationale and Steward evidence.

Group readiness is `ready` only after relative height/scale, distinct face/silhouette, posture, spacing, wardrobe differentiation, identity-map integrity, no blending/swapping, and hidden-caption pair, small-group and all-resident plans have evidence. Campaign-level all-resident recognition remains the final initiative test. A resident may remain `awaiting_group_evidence` without misrepresenting readiness.

## 4. Lock records, versions, and downstream use

The JSON record is authoritative structured evidence; its colocated Markdown rendering is the human review surface. Both identify each other and their hashes once finalized. Versions use semantic `major.minor.patch`: major for identity/physical/facial fingerprint changes; minor for approved wardrobe, anchor, prompt-model, or asset-set changes requiring affected revalidation; patch for non-semantic metadata corrections. Every downstream asset records resident ID, exact canonical version, lock-record ID/hash and the specification/asset hashes it consumed. `latest` and silent replacement are forbidden.

Major changes revalidate all portraits, turnarounds, expressions, icons, prompt reproducibility and group compatibility. Minor changes revalidate affected roles plus recognition and group impact; changed generator/model/checkpoint, prompt controls, asset bytes, accepted specification, privacy classification, discovered drift, expired tolerance, failed hidden-caption test, or revoked evidence also triggers revalidation.

## 5. Change control, rollback, and supersession

A replacement is a new candidate and version with fresh evidence and explicit approval. Only after it locks may the old record transition to superseded with reciprocal links; history and bytes remain traceable. Rollback is forward history: an explicit Steward request names current and restored approvals, reason and a **new** version, revalidates current hashes/access and affected gates, supersedes the current version, and never edits an old record into being current. Revoked or inaccessible evidence cannot be restored. Rejected/superseded assets never move into canonical directories by copying.

## 6. Privacy and restricted governance

Records inherit the most restrictive referenced evidence class (`public`, `internal`, `restricted`, `private`). Restricted/private manifests, reviews and hashes are separately loadable, denied by default, auditable, and redacted only through an explicit derivative record. Public registries may expose an opaque ID/status but not sensitive paths, notes, hashes or attributes. Access cannot be widened by lock, rollback or downstream use. Adult-only layers require adult status, audience scope and authorization. No hidden repository or private-mode activation is authorized by this canon.

## 7. Review plans and diagnostics

The hidden-caption plan freezes pixels, randomizes display order, removes names/captions/positional hints, defines expected identity independently, captures each Steward answer verbatim, and reports pass/partial/fail/pending with confused identities and remediation. Do not train reviewers with wardrobe-only clues. The prompt checklist verifies every generation input, hash, reproducibility run, identity/face/body/wardrobe result and failure mode. The human lock checklist covers authority, hashes, completeness, recognition, consistency, prompts, group readiness, visibility, tolerances, version links and downstream references.

Validators diagnose missing role/path/hash, hash mismatch, invented approval, illegal transition, reserved evidence, stale version, missing reciprocal link, recognition/group/prompt failure, wardrobe/anatomy drift, scope leakage and expired tolerance. They fail closed and never infer an artistic judgment.

## 8. Tests, anti-patterns, and completion

Tests cover every state and illegal transition, non-Steward/implicit canonical attempts, required assets and real hashes, recognition/group/prompt gates, version links, rollback history, visibility, and honest pending examples. Integration runs schema → asset manifest → eligibility → explicit approval → lock → downstream pin → supersession/rollback.

Forbidden: fabricated images, decisions or hashes; automation-as-approver; attractiveness scores; wardrobe-only identity; placeholder/reserved assets as complete; unpinned downstream references; overwriting canon; deleting rejected history; loosening privacy; converting Evelyn into a universal template; or reporting readiness when evidence is pending.

WP-4117 implementation is complete when schema, runtime validator, human template/checklists, example, tests, registry/report integration and deliverable mapping pass. This does **not** mean any resident is canonical. Resident canonical status remains pending until all real evidence and an explicit Steward decision exist.

