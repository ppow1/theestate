# Multi-Seat Adversarial AI Engineering Method

Status: canonical provider-neutral engineering method  
Use: governed Estate software packages, architecture, persistence, and
operational changes

This method was developed while building and validating Campaign Runner and
Grace cognition. It is not Codex-specific. It can be used with Codex, Hermes,
local models, mixed providers, or a human/AI engineering team.

## 1. The original manual model

The working setup used three independent AI seats and three command windows:

- C1 / command window 1;
- C2 / command window 2;
- C3 / command window 3.

Each seat had separate conversational and execution context. Work was
round-robined so the context that produced an implementation did not
automatically certify it.

A representative package flow was:

```text
C1 primary writer
  -> C2 independent validator
       PASS -> package advances
       FAIL -> structured defects returned
  -> C3 or C1 repair writer
  -> different eligible seat independently revalidates
```

The roles rotate. C1 does not permanently mean writer, C2 does not permanently
mean validator, and C3 does not permanently mean repairer. Seats are
independent execution/context pools. Availability, collision avoidance, prior
involvement, independence, and workload determine assignment.

For example, Package A may use C1 writer, C2 validator, and C3 repairer; the
next package may use C2 writer, C3 validator, and C1 repairer. The invariant is
independence, not seat numbering.

## 2. Why independent adversarial review worked

AI coding agents can produce code that appears correct to the context that
wrote it while retaining incomplete correspondence checks, optimistic
assumptions, insufficient adversarial tests, persistence/restart defects,
concurrency defects, authority/provenance defects, or false-positive PASS
conditions.

The Campaign Runner and Grace sequence exposed examples involving arbitrary
PASS acceptance, provenance correspondence, empty current-state acceptance,
packet/classification substitution, structured defect persistence, bounded
rename reconciliation, duplicate acceptance after restart, pending-acceptance
redispatch, and concurrent validator invocation. These are evidence for
independent review of AI-generated code, not failures unique to one provider.

The key principle is:

> AI self-review is not the same as independent review.

A model reviewing its own code retains its original assumptions, abstraction,
requirement interpretation, and immediate reasoning context. A fresh seat is
more likely to challenge those assumptions. Writer confidence is not
independent evidence, and passing writer-authored tests is not independent
acceptance.

## 3. What an adversarial validator does

The validator's task is to try to disprove the implementation, not merely to
repeat “the tests pass.” It should:

1. read the canonical contract and acceptance criteria;
2. inspect the actual commit, source, migrations, tests, and affected consumers;
3. construct independent adversarial probes;
4. substitute wrong identities, requests, sessions, packets, and results;
5. test missing, empty, malformed, stale, expired, and contradictory state;
6. exercise persistence, restart/readback, idempotency, and concurrency;
7. attempt authority widening and provider/resource substitution;
8. check whether durable evidence actually corresponds to the implementation.

Typical questions are: Can a forged result cross the persistence boundary? Can
a stale worker advance state? Can a restart duplicate work? Can a caller
replace identity with transcript prose? Can two processes both win? Can an
empty object satisfy a meaningful-state requirement?

The goal is a reproducible counterexample when one exists, not confirmation of
the writer's story.

## 4. Structured defect handoff

Validator findings must be actionable. Every defect should state:

- violated acceptance criterion or contract;
- expected behavior;
- observed behavior;
- reproducible steps and evidence;
- severity;
- minimum required repair boundary;
- required revalidation.

“Needs work” and “might be unsafe” are not sufficient. The repair seat must be
able to reproduce the same failure and know what must remain unchanged.

The durable handoff should also identify the package, role, implementation SHA,
report path, tests run, verdict, and next action. Chat or terminal scrollback
is not institutional memory.

## 5. The cost of too much seat-hopping

The original method was effective but expensive. The early pattern often became
writer -> validator -> repairer -> validator, repeated for each finding. That
caused context reconstruction, repeated reproduction, latency, token/credit
consumption, extra worktrees, and operator handoffs.

The method therefore evolved rather than being discarded. The strongest part—
fresh adversarial review—was retained while routine internal repair was moved
back into one package-engineering context.

## 6. Current preferred refinement

The preferred normal model is:

```text
one package-engineering context:
  run -> diagnose -> repair -> verify -> continue
  collect reachable defects -> full package rerun -> candidate

one independent adversarial context:
  inspect the complete candidate -> PASS or complete structured FAIL
```

On FAIL, the complete defect set returns to package repair ownership. The
engineer repairs, fully reruns the package, creates an updated candidate, and
the independent boundary is reached again. This is the current Campaign Runner
package-level self-repair model; it reduces unnecessary seat hopping without
weakening independent acceptance.

See the [Campaign Runner Operational and Recovery Guide](Campaign_Runner_Operational_and_Recovery_Guide.md)
for the durable implementation, state machine, fencing, and operator commands.

## 7. When a third seat is valuable

A third independent context remains useful when:

1. the independent validator rejects the package;
2. the package engineer repeatedly fails the same root defect;
3. there is an architectural disagreement;
4. persistence, concurrency, security, or authority risk is high;
5. writer and validator disagree about the canonical contract;
6. a fresh repair implementation is preferable to another attempt by the
   original engineer.

The third seat may act as an external repair engineer, a second adversarial
reviewer, or a fresh implementation context. Final acceptance must remain
independent of the final repair author.

## 8. Practical three-seat manual pattern

For an available pool C1, C2, C3:

1. Assign one seat as package engineer and another as independent validator;
   reserve the third as a fresh repair context.
2. If validation PASSes, advance the package.
3. If validation FAILs, return the complete structured defect set to the
   package engineer first.
4. If the engineer repairs successfully, the independent validator
   revalidates.
5. If the engineer cannot repair or repeats the same bounded failure, assign
   the third seat as repair engineer.
6. Have a different eligible context validate that repair.
7. Rotate assignments on the next package according to availability and prior
   involvement.

The same context must not be both the final repair author and the accepting
validator. A seat that was involved in an earlier phase may be ineligible for
the relevant independent check even if its numeric label differs.

## 9. Collision avoidance

Multiple seats may work concurrently only when their work is non-colliding.
Before parallel work, verify repository, branch/worktree, package scope,
files/symbols, database objective/stage ownership, and whether either task
mutates shared infrastructure.

Independent validation may use a detached temporary worktree. Do not let two
seats edit the same authoritative worktree or stage the other seat's files.
Preserve unrelated dirty work and never use broad cleanup to make a collision
appear resolved.

## 10. Durable handoffs and evidence

Each role transition should leave durable evidence containing at least:

- package/objective and role;
- implementation or repair SHA;
- report location;
- acceptance basis and evidence references;
- defects, severity, and repair boundary;
- tests and environment limitations;
- validation verdict and next action.

The database owns lifecycle truth where Campaign Runner is used. Reports make
the reasoning and evidence discoverable; they do not replace PostgreSQL state.
This separation allows three command windows to continue after one context is
lost or a process restarts.

## 11. Applying the method beyond Codex

### Local AI

A provider-neutral local arrangement could use Local Model A as package
engineer, Local Model B as independent adversarial validator, and Local Model C
or a stronger model for hard repairs or escalation. The identity of the model
is not the identity of the role; durable role and acceptance rules still apply.

### Hermes

Hermes may later orchestrate context persistence, role assignment, candidate
review, adversarial validation, repair routing, model diversity, durable
memory, and automatic role rotation. This document does not design that
integration. Any Hermes integration must preserve existing package history,
acceptance boundaries, and authoritative state rather than silently discarding
or reinterpreting it.

### Model diversity

A future pattern may use provider/model A to write, a different provider/model
B to validate, and provider/model C to repair hard failures. Diversity may
reduce correlated assumptions compared with multiple sessions of one model;
that is a hypothesis and future engineering opportunity, not a proven result
of this method.

## 12. Benefits and tradeoffs

Benefits observed in this work include better defect discovery, stronger
contract compliance, adversarial coverage, fewer false acceptances, better
restart/concurrency/persistence quality, and more trustworthy evidence.

Costs include additional tokens or credits, elapsed time, worktrees, operator
coordination, context reconstruction, and duplicate testing. Package-level
self-repair plus one final independent acceptance became the preferred
compromise: it preserves adversarial evidence while avoiding a validator
handoff after every internal repair.

## 13. Relationship to Campaign Runner and Grace

This method is the general engineering pattern. Campaign Runner is the current
governed implementation of much of it: durable package repair, structured
ledger, restart/resume, fenced attempts, and one independent acceptance
boundary. Keep this methodology separate from the [Campaign Runner guide](Campaign_Runner_Operational_and_Recovery_Guide.md),
which documents current operational behavior and commands.

Grace F/P/E implementation was materially produced using this method. Future
Grace operational checkpoint documentation should link here for the rationale
and manual fallback, without treating this method as a Grace architecture.

