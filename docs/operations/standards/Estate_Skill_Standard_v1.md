# Estate Skill Standard v1

An Estate Skill is a versioned, governed procedure that coordinates existing capabilities, providers, tools, authority, evidence, and lifecycle steps. It is not a capability, provider, resident, work package, automation, or unrestricted script. Registration is descriptive and never grants authority; institutional acceptance is always separate.

Every Skill has a closed manifest in `schemas/skills/skill_manifest_v1.schema.json`, a unique formal identity and aliases, owner and maintainer, purpose/outcomes, trigger class, capability and dependency requirements, classification and exact bounded scope, ordered stages, stop/escalation/timeout/partial behavior, replay/conflict behavior, evidence contracts, rollback/deprecation, maturity, availability, and institutional-acceptance state.

Maturity is Concept (0), Registered (1), Dependencies Available (2), Governed (3), Operational (4), and Institutionally Accepted (5). Historical maturity does not imply current dispatchability: unavailable, stale, blocked, missing-authority, and missing-capability states remain truthful.

Discovery is read-only. Grace preserves the Steward's exact words, explains boundaries, and suggests without executing. Explicit execution follows the existing Grace → Helen → PTM/owner authorization → Operations → Dispatch → provider/tool → receipt → validation → reconciliation → terminal-result surfaces. Diagnostic Skills may use the documented reduced path while retaining owner authorization, provenance, receipt, validation, reconciliation, and truthful terminal state. Helen reports capability maturity, qualified worker, provider/tool freshness, bootstrap dependencies, authority, dispatchability, gaps, and enabling projects.

The first operational Skill, Repository Health, is Level 4 candidate only, read-only, and may write only its declared report and receipt. It cannot commit, push, reset, switch, clean, prune, delete, create/drop stashes, modify content, widen scope, expose secrets, or grant acceptance.
