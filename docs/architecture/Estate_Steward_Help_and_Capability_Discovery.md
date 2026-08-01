# Estate Steward Help and Capability Discovery

The Steward help surface is a read-only projection of existing canonical registries, provider catalogs, resident/readiness evidence, the Skill registry, operational runtime status, and institutional-acceptance records. It does not replace or duplicate those sources.

Every generated snapshot records a timestamp and SHA-256 digest for its source references. Current availability is recomputed from current evidence and bounded loopback probes where configured. Installation, catalog registration, historical success, and passing tests cannot by themselves produce `operational_now`. Conflicting evidence is surfaced and the projection fails closed.

Grace answers ordinary help, capability, resident, department, outcome, and Skill questions in plain language first through `resident_interaction.process_chat`, the authenticated WebUI/Grace route, and the established `estate help`/`estate steward-help` CLI commands. Discovery is always `executed: false`; it cannot execute providers, Skills, work packages, repository mutation, merge, deletion, purchase, external messaging, or acceptance. Grace offers a bounded request phrase with scope and authority guidance when asked how to obtain an outcome.

Helen’s view is the same projection with emphasis on possession, qualified worker, current availability, freshness, dispatchability, gap reason, and enabling project. A registered capability with stale evidence remains unavailable or a capability gap, not operational. Every live answer binds the snapshot generation time, freshness state, source references, source digests, and conflicts; generated artifacts bind the same metadata and are not used as an unbounded cache.
