# Worker Runtime Contract v1

Status: Version 1 Standard
Owner: Chief Architect
Operational Coordinator: Alfred / Chief of Staff
Boundary Authority: Privacy and Boundary Office
Classification: Estate Internal

## Purpose

The Worker Runtime Contract defines the operating environment for Estate workers.

It prevents workers from assuming GitHub, network access, browser authentication, or remote synchronization are available or authorized.

The contract exists because the Estate is local-first. GitHub is a transport adapter, not the execution authority.

## Runtime Authority

When a worker is executing locally inside the Estate, the authoritative workspace is:

    A:\theestate

The local repository state is the worker's source of truth for the current task.

GitHub may exist as a later synchronization transport, but it is not part of the worker's default runtime.

## Default Assumptions

Every local worker must assume:

- Required files already exist locally.
- Repository state has already been synchronized by Pat, Alfred, Helen, or another authorized coordinator.
- Work packages are read from the local collaboration directory.
- Results are written to the local collaboration directory.
- The worker can operate without internet access.
- The worker must not open a browser authentication flow.

## Forbidden Operations

Unless the current work package explicitly authorizes synchronization, a worker must not run or recommend:

- git fetch
- git pull
- git push
- git clone
- git remote
- GitHub login
- GitHub authentication
- Browser authentication
- Network synchronization

These are protocol violations for local-only worker execution.

## Allowed Git Inspection

Workers may inspect repository state using non-mutating commands such as:

    git status
    git rev-parse HEAD
    git rev-parse --abbrev-ref HEAD
    git log --oneline -5

Workers may not synchronize repository state unless explicitly authorized.

## Collaboration Authority

Workers communicate through local files under:

    collaboration/

The Collaboration Layer may later be synchronized to GitHub by an authorized operator or adapter.

The worker should treat the local collaboration directory as the active communication surface.

## Completion Rule

When finished, a local worker shall:

1. Produce requested artifacts locally.
2. Produce the requested status report locally.
3. Run local validation when assigned.
4. Stop and report completion.

The worker must not automatically push, pull, fetch, authenticate, or open GitHub.

## History Rule

Workers must not directly edit:

- estate_ledger/ledger.md
- development/devlog.md

History updates must use the approved history queue and drain workflow.

## Boundary Rule

Workers must not publish Local Only or private material to shared transports.

Local artifacts remain local unless explicitly classified and promoted.

## Contract Acknowledgement

Before writing code, a worker should summarize this contract.

If the summary includes GitHub synchronization, authentication, pull, push, fetch, clone, or browser login, the worker has misunderstood the runtime and must correct itself before proceeding.

## Engineering Principle

Repository transport is not execution authority.

The Estate should distinguish:

- local workspace authority
- communication transport
- synchronization mechanism
- publication boundary

Confusing these layers creates operational errors and unnecessary burden for the Steward.
