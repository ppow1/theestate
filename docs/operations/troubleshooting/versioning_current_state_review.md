# Living Diagnostics Pre-flight and Versioning Current-State Review

Date: 2026-08-08. Worktree: `/workspace/theestate`. Branch/base: `work` at
`00ee3d2`. No Git remote or `origin/main` exists in this supplied checkout; the
only listed worktree was the clean canonical checkout. A second worktree could
not provide isolation from an absent integration ref, so the accepted docs,
schema, diagnostics-module, tool, and focused-test scope was used in place.
Grace/CME/Comms8/execution runtime sources were read only.

| Artifact class | State | Current identity/authority | Semantic/interface version | Lineage/query/reproduction weakness |
|---|---|---|---|---|
| Python source | GIT_ONLY | path, Git commit/blob | occasional constants/contracts | installed state not universal |
| PowerShell | GIT_ONLY | path, Git | uncommon | deployment copies may diverge |
| JavaScript/HTML/CSS | GIT_ONLY | path, Git | uncommon | generated/source distinction varies |
| JSON/YAML | PARTIAL | Git plus document fields | schema/version where declared | inconsistent lineage |
| JSON schemas | STRONG | `$id`, Git blob | schema ID/version | consumers not universally recorded |
| SQL/migrations | PARTIAL | ordered migration file + Git | migration identity | installed DB state separate |
| Governance/operations docs | GIT_ONLY | canonical path + Git | document versions vary | applicability was not machine checked |
| Work packages/receipts | PARTIAL | WP ID, branch/commit evidence | contract-specific | historical receipts vary |
| Provider adapters | PARTIAL | Git + provider contracts | adapter/schema versions vary | actual provider state is runtime evidence |
| Resident surfaces | PARTIAL | Git + About inventory | available component versions | WP-0055 was display, not universal provenance |
| Diagnostic tools | GIT_ONLY | path + Git | generally absent | no shared applicability index before this slice |
| Generated artifacts | PARTIAL | generator + source revision | format version | volatile snapshots must be regenerated |

The Estate ledger, development log, migrations, schemas, package metadata,
service/component inventory, PTM contracts, completion receipts, About/version
surface, and Git conventions establish several useful identities but no prior
universal manifest, dependency-based document applicability, or searchable
living-diagnostics authority. WP-0055 remains accurately credited only for
displaying versions where available.

The stable component map is deliberately bounded to major subsystems in
`estate.diagnostics.living.COMPONENTS`; it is not a helper registry. Unknown
semantic versions remain `NOT_DECLARED` while source identity stays exact.
Exclusions cover VCS/venvs/caches/runtime/browser profiles/evidence/generated
outputs, secrets/credentials, sensitive names, lock/PID/database/key material.
