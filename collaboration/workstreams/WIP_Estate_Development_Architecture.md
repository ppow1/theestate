# Estate Development Architecture

**Status:** Work in Progress  
**Date:** 2026-07-28  
**Purpose:** Preserve the current design discussion so it can be resumed and converted into an authorized work package as soon as possible.

---

## 1. Why This Exists

The immediate trigger for this work-in-progress design was the difficulty involved in rolling out and validating the Grace runtime integration through Open WebUI, the Residential Gateway, and the Grace runtime bridge.

The Grace effort demonstrated that the Estate needs a clearer separation between:

- the live institutional Estate;
- development work;
- acceptance testing;
- validation;
- deployment preparation;
- promotion into live operation;
- temporary worktrees and historical artifacts.

The goal is not to redesign the Estate from first principles, move the live system, or launch a long migration project.

The goal is to change the default for future development so that new work happens in a controlled developmental stack and reaches the live Estate only through an explicit promotion process.

---

## 2. Governing Terminology

The preferred distinction is:

- **The Live Estate**
- **Estate Development**

This wording is preferred over treating the Estate merely as a conventional production environment.

The Estate is not only software. It is a continuously operating institution. The word **Live** better reflects its role.

### The Live Estate

```text
A:\theestate
```

`A:\theestate` is the Estate.

It is the sacred live institutional asset.

It remains where it is.

It is not moved into a new parent hierarchy.

It is not demoted into being one environment inside a broader development directory.

It is not used as an experimental workspace.

It is not reorganized as part of establishing Estate Development.

### Estate Development

```text
A:\EstateDevelopment
```

Estate Development is a separate developmental stack located beside the Live Estate.

It is the place where engineering, experimentation, acceptance, validation, release preparation, worktrees, deployment bundles, and rollback preparation occur.

The developmental stack exists in support of the Live Estate. It does not contain or replace the Live Estate.

---

## 3. Core Governing Principle

> **The Live Estate is never a development environment. It is the institutional runtime. All engineering, experimentation, validation, and deployment preparation occur within Estate Development. The only authorized flow into the Live Estate is through an approved promotion process.**

The Live Estate is the destination.

It is not one more environment within the developmental hierarchy.

---

## 4. Correct Architectural Relationship

The intended relationship is:

```text
A:\
|
+-- theestate
|   +-- The Live Estate
|   +-- The institutional home
|   +-- Continues operating in place
|   +-- Never used for experimentation
|   +-- Updated only through approved promotion
|
+-- EstateDevelopment
|   +-- Developmental stack
|   +-- Development source and worktrees
|   +-- Acceptance environments
|   +-- Validation and reports
|   +-- Deployment preparation
|   +-- Release and rollback materials
|
+-- AI
    +-- Existing AI tooling and supporting infrastructure
```

The Live Estate remains independent from the organizational structure beneath `A:\EstateDevelopment`.

---

## 5. Proposed Estate Development Structure

The exact names remain subject to refinement, but the preferred conceptual structure is:

```text
A:\EstateDevelopment\
|
+-- Source\
|   +-- Development\
|   +-- Acceptance\
|   +-- Worktrees\
|   +-- Archive\
|   +-- LiveReference\
|
+-- Runtime\
|   +-- Development\
|   +-- Acceptance\
|   +-- Integration\
|
+-- Validation\
|   +-- TestSuites\
|   +-- Reports\
|   +-- Benchmarks\
|
+-- Deployments\
    +-- Bundles\
    +-- Releases\
    +-- Rollback\
```

### Live Reference

Any copy or mirror representing the current state of the Live Estate should be treated as a read-only reference.

It must not become another writable source of truth.

Changes should originate in Development, advance through Acceptance, and be promoted into the Live Estate.

---

## 6. Development Lifecycle

The intended lifecycle is:

```text
Development
    |
    v
Acceptance
    |
    v
Promotion
    |
    v
Live Estate
```

This changes the operating mindset from:

> "I am updating the Estate."

To:

> "I am preparing a promotion candidate for the Estate."

That distinction is both technical and institutional.

---

## 7. This Is Not a Migration Project

This effort must not be framed as a full migration, machine-wide reorganization, or week-long blocking initiative.

Nothing in the Live Estate is moved.

The Grace runtime, Residential Gateway, Open WebUI, validation resources, Stream Deck launchers, and other live services are not relocated merely to establish this architecture.

The correct approach is:

> **Build a scaffold, change the default, and allow adoption to occur incrementally.**

Historical directories do not have to be reorganized before the new method can begin.

The current live launchers remain in place.

The current live services continue running.

The Estate remains operational while the developmental stack is introduced.

---

## 8. Initial Rollout

The first rollout should be deliberately small.

During one focused working session:

1. Create `A:\EstateDevelopment`.
2. Establish the agreed directory scaffold.
3. Define the standard location for new worktrees.
4. Define an initial environment manifest convention.
5. Define a basic promotion procedure.
6. Apply the method to the next appropriate work package.

No historical migration is required to begin.

No live service must be moved.

No production shutdown is required.

No complete cleanup of the A: drive is required before adoption.

---

## 9. New Default for Work Packages

Under the current pattern, a work package may create a worktree directly under `A:\`, for example:

```text
A:\theestate-wp4233
```

Under the new default, new worktrees should be created beneath Estate Development, for example:

```text
A:\EstateDevelopment\Source\Worktrees\WP-4234
```

The exact naming convention may be finalized later, but the governing rule is immediate:

> **From adoption forward, no new developmental worktree should be created directly under `A:\` when it belongs within Estate Development.**

Existing worktrees may remain where they are until they are retired, naturally revisited, or intentionally cleaned up.

---

## 10. Copy, Do Not Move

When a development or acceptance instance is required, the Live Estate is not moved or broken apart.

Instead, the appropriate source state is copied, cloned, or materialized into Estate Development.

For example:

```text
A:\theestate
    Live Estate
    remains in place
    continues operating

A:\EstateDevelopment
    duplicated or cloned source
    development runtime
    acceptance runtime
    validation
    deployment preparation
```

The developmental copy is then separated into the organization required for development, acceptance, runtime testing, validation, and deployment preparation.

The existing Live Estate remains untouched until an approved promotion occurs.

---

## 11. Environment Isolation

Development and Acceptance must not accidentally share mutable state with Live.

Where parallel runtime instances are required, they should receive distinct:

- runtime directories;
- databases;
- ports;
- secrets;
- logs;
- generated artifacts;
- caches where sharing would create risk;
- environment identifiers.

The Live Estate must not depend on temporary worktree paths.

Development and acceptance launchers must not silently target live databases or live runtime state.

---

## 12. Explicit Environment Identity

Every new capability should answer this question before implementation begins:

> **What environment am I running in?**

The answer must be explicit:

- Live
- Acceptance
- Development
- Integration, where separately needed

The environment must not be guessed from an incidental path, an operator's memory, or an unverified default.

Startup scripts should evolve from asking:

> "Where is the Estate?"

To asking:

> "Which environment am I starting?"

An environment manifest may eventually express values such as:

```yaml
environment: acceptance
source_root: A:\EstateDevelopment\Source\Acceptance
runtime_root: A:\EstateDevelopment\Runtime\Acceptance
gateway_port: 11445
webui_port: 8090
database: A:\EstateDevelopment\Runtime\Acceptance\OpenWebUI\webui.db
secret_reference: acceptance-secret-reference
```

This is an example of the concept, not a finalized schema or an authorization to adopt those exact ports or paths.

---

## 13. Stream Deck and Launchers

Existing Stream Deck buttons and startup launchers that operate the Live Estate should remain untouched during initial rollout.

New buttons or launchers may be created for Development and Acceptance.

The distinction must be visible and difficult to confuse.

The initial rule is:

- existing Live launchers continue to start Live;
- new Development launchers start Development;
- new Acceptance launchers start Acceptance;
- Live launchers are not repointed merely to establish the developmental stack.

---

## 14. Promotion Process

The promotion process is the controlled boundary between Estate Development and the Live Estate.

A future mature promotion pipeline may:

1. assemble a candidate;
2. deploy it into Acceptance;
3. run validation;
4. produce reports;
5. create a deployment bundle;
6. record the exact source state;
7. prepare rollback material;
8. obtain the required authorization;
9. promote the approved candidate into the Live Estate;
10. validate the resulting Live state.

The first version does not need to automate every step.

A documented, repeatable manual process is acceptable as the initial scaffold, provided it preserves the boundary and does not pretend that unvalidated changes are approved for Live.

---

## 15. Cleanup Strategy

Cleanup is important, but it is not a prerequisite for changing the default.

The current A: drive contains multiple historical, temporary, validation, campaign, and worktree directories. These should eventually be inventoried and rationalized.

However:

- no directory is deleted merely because the new scaffold exists;
- dependencies must be identified before removal;
- live services must not depend on disposable worktree paths;
- old directories may remain until their purpose and dependency status are known;
- cleanup should occur as systems are naturally touched or where there is a clear operational benefit.

The preferred principle is:

> **Existing assets are migrated or retired only as they are naturally touched or when there is a clear operational benefit.**

This prevents the architecture effort from becoming an open-ended cleanup campaign.

---

## 16. Completion Standard for the Initial Work Package

The initial foundational work package should not define success as moving every historical artifact.

It should be considered successful when:

1. `A:\EstateDevelopment` exists.
2. The directory standard is documented.
3. A standard method exists for creating a new worktree.
4. A standard method exists for launching a developmental environment.
5. A standard method exists for establishing or launching Acceptance where required.
6. A standard promotion procedure into the Live Estate is documented.
7. The next appropriate work package uses the method from beginning to end.
8. No write occurs to the Live Estate before the promotion point, except where explicitly authorized for emergency repair or another separately governed exception.

Everything beyond that is incremental adoption and cleanup.

---

## 17. First Practical Milestone

The first milestone should be achievable in one working session:

> **A new work package can be created, developed, validated, and prepared for promotion entirely within Estate Development, with no writes to the Live Estate until the authorized promotion step.**

That milestone accomplishes the architectural shift without requiring the Estate to stop, move, or be comprehensively reorganized.

---

## 18. Lessons from the Grace Rollout

The Grace rollout exposed several conditions this architecture is intended to prevent:

- development artifacts influenced live behavior;
- runtime state existed in or depended on a work-package worktree;
- deployment tooling and the running service targeted different Open WebUI databases;
- the deployment boundary was not explicit enough;
- validation of runtime communication did not guarantee validated operational behavior;
- the absence of an isolated acceptance target increased the cost of diagnosis;
- manual recovery required reconstructing which environment, database, runtime, and function state were actually active.

The remaining Grace presentation defect also illustrates the value of acceptance testing: the bridge and grounding behavior worked, but the user-facing result was raw runtime JSON rather than a synthesized conversational response.

A developmental and acceptance stack should allow that class of defect to be discovered before promotion into Live.

---

## 19. Scope Boundaries

This work-in-progress proposal does not authorize:

- moving `A:\theestate`;
- renaming the Live Estate;
- nesting the Live Estate under `A:\EstateDevelopment`;
- shutting down the Estate for a migration;
- moving every existing runtime into a new directory;
- repointing current Live launchers without explicit need;
- deleting historical worktrees or temporary folders without inventory;
- requiring a complete blue/green implementation before the first new work package uses the scaffold;
- turning the initial rollout into a week-long or multi-week blocking project.

---

## 20. Longer-Term Direction

Once the scaffold proves itself through real use, Estate Development may mature to include:

- stronger automated environment manifests;
- standard worktree creation scripts;
- isolated runtime launchers;
- acceptance deployment automation;
- validation suites;
- deployment bundle generation;
- release records;
- rollback bundles;
- promotion receipts;
- explicit blue/green or equivalent live rollout mechanisms where justified;
- automated detection of live dependencies on development paths;
- gradual cleanup of historical directory sprawl.

These are directions for controlled evolution, not prerequisites for starting.

---

## 21. Final Working Principle

The essence of this design is:

> **Do not reorganize history before improving the future. Build the scaffold, change the default, validate the next real work package through it, and let the Estate converge on the better method over time.**

The Estate remains Live.

Estate Development becomes the developmental stack.

Development creates candidates.

Acceptance validates them.

Promotion is the only normal path into the Live Estate.

---

## 22. Next Action When Resumed

When this work is resumed, convert this work-in-progress document into a bounded foundational work package that:

- confirms the final directory names;
- establishes the minimum scaffold;
- defines the first environment manifest format;
- defines the standard worktree creation method;
- defines the initial manual promotion procedure;
- selects the first real work package to use the process;
- preserves all scope boundaries stated above;
- avoids expanding into a full migration or machine-wide cleanup campaign.
