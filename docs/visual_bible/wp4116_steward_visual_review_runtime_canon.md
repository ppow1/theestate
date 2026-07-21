# WP-4116 Steward Visual Review and Revision Runtime Canon

**Status:** Runtime canon v1  
**Authority:** The Steward is the sole final visual acceptance authority.  
**Scope:** Visual Bible assets, comparison sets, anchors, group imagery, review evidence, revisions, approvals, supersession, and rollback.

## 1. Authority and non-automation boundary

Every generated or imported asset begins `draft`; submission makes it `pending_steward_review`, never approved. Tools may check completeness, provenance, layout, or diagnostics, but scores, similarity models, votes, artists, and operators cannot approve, reject, canonize, or reinterpret Steward intent. Only an explicit Steward disposition may produce `provisionally_approved`, `canonical`, or `rejected`. “Technically valid,” queue completion, or an emotional match is not canonical approval.

## 2. Assets, comparison sets, and queues

Assets and comparison sets share the states `draft`, `pending_steward_review`, `revision_requested`, `provisionally_approved`, `canonical`, `rejected`, and `superseded`. Legal transitions are draft→pending; pending→revision/provisional/canonical/rejected; revision→pending/rejected; provisional→pending/revision/canonical/rejected; canonical→superseded. Rejected and superseded records are terminal retained evidence. A new attempt gets a new identifier and lineage.

A review queue is a scoped, provenance-bearing snapshot of pending subjects, priority, submission time, and its controlled review manifest. Queues do not confer authority. Restricted and private items must use separately loadable queues unavailable by default; their manifests and notes inherit the most restrictive source scope. Public output may not reveal internal, restricted, or private review records.

## 3. Steward Notes ledger

Steward Notes are append-only, timestamped records with Steward identity, exact text, target references (asset, comparison, variant, angle, prompt, revision), technical/emotional/both dimension, provenance, and optional clearly subordinate normalized summary. Exact text is immutable: correction or clarification appends a new note that supersedes or relates to the old note without erasing it. Search tags and summaries must never replace, soften, generalize, or claim to quote the exact note.

## 4. Controlled comparison manifests

A manifest places labeled variants in vertical rows and aligns columns in this order: front, front three-quarter (45°), side, rear three-quarter (rear-45°), rear. Labels remain outside image pixels and original-resolution sources are zoomable from one review surface. Three-variant reviews contain exactly three variants. A 360 review contains every aligned angle for every variant. Applicable footwear cycles include at least one heel set of 3 inches or higher; inapplicability requires an explicit rationale under WP-4112.

The manifest lists the only intended variables, all fixed variables, and a plain difference summary. Identity, facial fingerprint, pose, expression, crop, camera position/profile/focal length, lighting, background, wardrobe, generation settings, and seed stay fixed unless explicitly named as intended variables. An indistinguishable difference or unintended change fails review eligibility and produces diagnostics, not a guessed decision.

Technical review records anatomy, artifacts, face consistency, body/proportion, scale, camera, lighting, alignment, and reproducibility. Emotional review independently records presence, warmth, expression, posture, chemistry, and whether the image feels like the resident. Neither dimension overwrites the other.

## 5. Anchor roles

Each resident can independently reference: a technical anchor; facial anchor; body/proportion anchor; signature-look anchor; and one or more emotional-presence anchors. One asset may fill multiple explicitly approved roles, but approval for one role does not imply another. An emotionally correct but technically imperfect image can be an emotional anchor while a different asset remains the technical anchor.

## 6. Group and recognition review

Pair/group manifests additionally preserve an identity map, relative height/scale, face and body separation, distinct posture/expression, interpersonal spacing and chemistry, role behavior, wardrobe differentiation, and absence of identity blending. A hidden-caption recognition test displays the unchanged group image without names or positional hints, records expected residents and the Steward's responses verbatim, then records pass/fail/partial/pending. Automation may calculate completeness only; recognition judgment belongs to the Steward. A failed test returns the group asset to revision rather than silently relabeling it.

## 7. Revision packets

Every revision request links source assets and exact Steward Notes and gives a human artist or generation workflow: approved elements to preserve; defects; exact requested changes; variables to change; variables held fixed; positive fragments; negative fragments; layout requirements; and concrete next-pass tests whose pass authority is the Steward. Change and fixed sets cannot overlap. Packets inherit source access boundaries and capture versions/hashes of all referenced prompts and assets. They never convert a note into generic scoring or permit collateral changes.

## 8. Canonical approvals, supersession, and rollback

A canonical approval is a separately versioned record naming subjects, approved version/time, explicit approval, Steward identity/authority, linked notes, preserved elements, scope, and provenance. Canonical transition requires its approval ID. Replacement first creates a new explicit approval, then transitions the former canonical record to `superseded` with replacement links; files and rejected evidence remain intact.

Rollback is a new Steward-requested audit record that names current and restored approval IDs, reason, time, superseded/restored subjects, and affirms history preservation/no automatic deletion. It creates forward history: validate the target approval, issue new transitions, and never edit an old approval to make it current. Rollback cannot cross audience boundaries or restore revoked access.

## 9. Provenance, audit, and diagnostics

Every durable record carries creator/time, source IDs, SHA-256 content reference, lineage, and revision. Asset evidence additionally retains asset hash/path, model/version, seed, prompts and negative prompts, settings, parent assets, and generation or artist identity when applicable. Every transition records date, reviewer, authority, reason, source IDs, and replacement/approval relationships. Audit is append-only.

Diagnostics distinguish missing metadata, hash/reference failure, unauthorized transition, scope leak, intended/fixed overlap, angle/layout mismatch, non-zoomable source, comparison drift, identity blending, insufficient distinction, and incomplete action packet. A diagnostic blocks eligibility but is not a Steward judgment.

## 10. Validation and tests

Schema validation checks record shape; runtime validation checks provenance, exact-note preservation, state authority, state graph, controlled layout, three-variant/360 behavior, dimensions, scopes, anchors, hidden captions, actionable packets, and approvals. Unit tests must cover every invalid boundary. Integration tests must connect queue→manifest→note→revision→resubmission→explicit approval→canonical→supersession/rollback and confirm unreviewed data cannot become canonical.

## 11. Anti-patterns

Forbidden: automated acceptance scores; interpreting silence as approval; marking generated fixtures canonical; overwriting exact notes; flattening technical and emotional assessment; opening unrelated windows for comparison; changing undeclared controls; deleting rejection/supersession evidence; editing approvals in place; leaking restricted/private layers; using Evelyn's calibration as a universal template; and claiming that schema validity proves visual acceptance.

## 12. Completion criteria

Completion requires versioned schemas and validators for states, notes, queues/manifests, revisions, approvals, anchors and recognition; nonbinding Evelyn examples; provenance/access/audit enforcement; transition and rollback behavior; unit and integration evidence; documentation; and a deliverable-to-evidence report. Remaining actual visual selections are unresolved Steward decisions and must be stated as such.
