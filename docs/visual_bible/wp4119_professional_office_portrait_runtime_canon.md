# WP-4119 Professional Office Portrait Runtime Canon

**Status:** Authoritative implementation canon. **Authority:** Steward. **Scope:** Campaign 02 office portraits.

## 1. Purpose, hierarchy, and authority

An office portrait is evidence of a commissioned resident's recognizable professional presence: identity first, a plausible lived action second, and office context third. It is not a hero portrait, credential, appointment instrument, or substitute for constitutional records. The authority hierarchy is: Steward decision; constitutional/appointment record; active resident registry; approved Visual Bible and wardrobe; approved environment record; this canon; generation prompt. Conflicts stop production. Never infer a promotion, credential, reporting line, tool, collection, award, or access right from visual plausibility.

The catalog permits `candidate`, `canonical`, `anchor`, `rejected`, `superseded`, and `pending` declarations. These describe an office asset's governed use; `anchor` is independent of hero canon. A canonical office portrait requires one matching asset hash and explicit Steward approval. An anchor additionally requires a narrative label, a truth rationale, and separate Steward approval. Rejected and superseded assets never resolve as canon or anchors. Rollback restores a previously approved hash and records the replaced asset, decision, reason, and revision; it never rewrites history.

## 2. Authentic office and environment provenance

Office and role labels must exactly match `data/registry/residents.json` unless a cited later constitutional appointment controls. The resident-to-office validator treats that registry as the commissioned-resident authority index. Evelyn's record explicitly grants no institutional authority; scenery must not imply otherwise. Props and actions may express only the recorded role boundary.

Every scene classifies its environment as:

* `canonical_architecture`: an approved, versioned architectural record with a resolvable source and hash;
* `approved_interpretation`: Steward-approved visual interpretation, linked to the controlling office sources and approval;
* `placeholder`: explicitly noncanonical staging used to test composition; it cannot be canonical or an anchor.

An environment needs an ID, classification, version, source references, provenance status, and approval state. Unsupported office details are omitted or labeled unresolved—never filled with generic executive décor. Generic luxury suites, skyline boardrooms, seals, diplomas, nameplates, military/legal insignia, unexplained screens, and ornamental books are prohibited unless sources authorize them.

## 3. Narrative action and lived professional moments

Each required scene records a concrete, role-bounded action, visible task evidence, relationship posture, and moment rationale. The core variants are seated desk, standing environmental, conversational, and candid work. Doorway/arrival and close environmental variants are optional; a close detail still must recognize the resident. Examples are not transferable defaults: reading a sourced file, listening across a desk, preparing a governed briefing, or using an approved operational display.

A static fashion pose, implausible pantomime, empty executive power pose, or stock handshake fails. Hands must have credible anatomy, grip, occlusion, and task contact. Tools, records, books, displays, drinks, and office materials must be source-supported, legible only where approved, privacy-safe, and functionally used. No fabricated record text or confidential content may be rendered.

## 4. Recognition, emotion, composition, and physical fidelity

Hidden-caption review removes names, title cards, nameplates, logos, and filenames. Reviewers must recognize the resident from canonical facial geometry, visual fingerprint, body language, approved wardrobe, and authentic relationship posture—not stereotypes. Cross-resident convergence, a shared executive face, generic corporate styling, and office-as-caption fail.

An emotional anchor captures a resident-specific defining presence. Promotion workflow: candidate validation; completed hidden-caption test; completed review sheet; Steward `approved` decision tied to asset ID/hash; narrative label; truth rationale; catalog update. Office canon and emotional-anchor approval are separate decisions. Evelyn's forward-seated coffee conversation is a pending concept, not a generated or approved anchor and not a universal pose.

Composition review covers scene/action, eye line, camera, framing, resident recognition, environment hierarchy, prop function, hand integrity, and derivative safety. Body proportions and adult presentation remain canonical. Record seated/standing posture, support/contact, footwear and heel height, furniture/door/desk/chair dimensions or an approved scale-reference ID, camera height, and perspective. Furniture must fit the body rather than silently resizing the resident; footwear, hip tilt, leg line, reach, and seated compression must remain coherent.

## 5. Metadata, catalog, revision, and diagnostics

Every actual image has a sidecar containing resident/office/role IDs, scene and action, lifecycle state, paths, SHA-256, technical master/derivative data, prompts, workflow/model/seed/settings, generation time, source references, environment and wardrobe versions, physical cues, review, hidden-caption result, canon/anchor declarations, and lineage. High-resolution masters and UI derivatives are required before acceptance. Pending manifests contain no invented file or hash.

Hashes address exact bytes. Any byte change creates a new revision and review. Supersession preserves predecessor/successor IDs and reason. Rejection preserves reason and Steward notes. Diagnostics name the resident, asset, rule, and corrective action; never auto-repair authority, provenance, approval, or hashes. Catalog lookup must expose lifecycle without treating pending metadata as an image.

## 6. Steward review and validation gates

The review sheet must verify: office/role against authority sources; architecture class and provenance; lived action; identity without captions; adult/body/scale/posture/footwear; furniture contact; hands; prop and material correctness; wardrobe reference; privacy; master/derivatives; hash and reproduction metadata; anchor rationale; rejection/supersession history. Only the Steward approves canon or anchors. A reviewer may recommend, reject, or request revision but cannot promote.

Validation rejects missing authority, role/office mismatches, absent environment provenance, placeholders promoted to canon/anchor, duplicate canonical office declarations, unapproved canon or anchor promotion, terminal-state promotion, stale hashes, missing scene coverage, and registry/catalog coverage drift. Unit tests exercise each rule; integration tests validate all commissioned manifests against the resident registry and asset catalog.

## 7. Anti-patterns and completion criteria

Reject generic corporate stock convergence; invented authority or credentials; unsupported architecture/props; caption-dependent identity; static fashion posing; decorative tool clutter; malformed hands; false screen text; scale drift; infantilization; wardrobe outside approval; silent hash replacement; approval inferred from filenames; and placeholders masquerading as images.

Implementation is complete when schemas, templates, catalog links, validator, all commissioned-resident manifests, focused tests, traceability, and honest queues exist. Portrait production is complete only after real assets, provenance, hidden-caption testing, Steward decisions, and hashes exist. WP-4119 implementation completion must never be reported as image or Steward-review completion.
