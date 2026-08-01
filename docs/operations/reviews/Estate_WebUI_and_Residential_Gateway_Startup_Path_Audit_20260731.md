# Estate WebUI and Residential Gateway Startup-Path Audit

Date: 2026-07-31  
Repository reviewed: `A:\theestate-wp4233`  
Audit branch: `audit/webui-gateway-startup-path-20260731`  
Audit base: `1d7a05c933e9019a18a7b29a1edf643be96b4ea8`

## Scope and safety boundary

This was a read-only investigation. No service was restarted, no database was
changed, no Stream Deck profile or launcher was modified, and no deployment or
promotion action was performed. The report is based on launcher/configuration
inspection, read-only process command lines, read-only HTTP probes, and
read-only SQLite metadata inspection.

## Executive findings

1. The current Estate Operations v0.4 Stream Deck profile launches the
   Resident Gateway and Open WebUI through these exact files:

   - `A:\AI\Tools\EstateStreamDeckMVP\08-Start-Resident-Gateway.cmd`
   - `A:\AI\Tools\EstateStreamDeckMVP\10-Start-OpenWebUI.cmd`

2. Those wrappers invoke PowerShell 7 and then call the legacy
   `Estate-Service-Control.ps1` dispatcher. They do not call the more
   defensive `Core\Start-*.ps1` service path.

3. The actual Stream Deck service controller starts both services by port
   availability. It does not validate application readiness, database
   identity, expected Estate objects, or a deployment slot before reporting
   success.

4. The Gateway is currently rooted at `A:\theestate`, not
   `A:\theestate-wp4233`. The live command line and the launcher’s embedded
   command both confirm this. `A:\theestate` is on branch
   `feature/evelyn-multimodel-tpose-pipeline` and has pre-existing local
   modifications; it is not the clean audit repository.

5. Open WebUI is launched from `A:\AI\OpenWebUI` using the requested
   `A:\AI\OpenWebUI\.venv\Scripts\open-webui.exe`, on `127.0.0.1:8080`.
   The launcher supplies no `DATA_DIR` or `DATABASE_URL`. Open WebUI’s package
   default therefore resolves to the installed package data database unless
   an externally inherited process environment overrides it.

6. Two competing Open WebUI databases exist under the installation, and a
   separate recovery database exists under `A:\AI\Backups`. The launcher does
   not select or validate one canonical database. This explains how startup
   can reach a first-run state even when a valid pre-redeploy database exists.

7. Grace is not started by a separate Stream Deck executable. It is a resident
   model served inside the Resident Gateway. The Gateway source defines the
   `estate/grace` model and Grace runtime bridges, and the live
   `/v1/models` endpoint returned the Estate resident catalog.

8. No WebUI/Gateway blue/green slot selector, promotion record, or active-slot
   source of truth was found in the actual startup chain. Stream Deck does have
   separate OperatorDeck window-slot buttons, including `select-active`,
   `slot`, and `cycle-slot`; those move desktop windows and write window
   placement state. They are not service deployment controls and are rooted at
   the old `A:\theestate` tree.

## Exact startup chains

### Open WebUI Stream Deck path

The current profile is the nested manifest in
`Estate Operations v0.4.streamDeckProfile`. Its action references the following
chain:

```text
Stream Deck action
  -> A:\AI\Tools\EstateStreamDeckMVP\10-Start-OpenWebUI.cmd
  -> C:\Program Files\PowerShell\7\pwsh.exe -NoLogo -NoProfile
       -ExecutionPolicy Bypass -File A:\AI\Tools\EstateStreamDeckMVP\10-Start-OpenWebUI.ps1
  -> Estate-Service-Control.ps1 -Action WebUI
  -> Start-WebUI
  -> Start-HiddenProcess
  -> A:\AI\OpenWebUI\.venv\Scripts\open-webui.exe
       serve --host 127.0.0.1 --port 8080
```

The process working directory is `A:\AI\OpenWebUI`. The direct legacy
controller does not set a service-specific environment dictionary. The
process inherits the launcher environment. No `.env` file was found below
`A:\AI\OpenWebUI`.

`Start-HiddenProcess` starts the executable with a hidden window, records PID,
port, and start time in
`A:\AI\Tools\EstateStreamDeckMVP\estate-service-pids.json`, and waits for a
TCP listener. The WebUI action then opens `http://127.0.0.1:8080/`.

The current process tree corroborates the executable and command:

```text
open-webui.exe PID 44392
  -> A:\AI\OpenWebUI\.venv\Scripts\python.exe PID 44848
     -> Python311 PID 45016
        ... serve --host 127.0.0.1 --port 8080
```

The extra Python process is an implementation detail of the Open WebUI
launcher/runtime. The authoritative requested executable and command are the
`open-webui.exe` command shown above.

### Resident Gateway Stream Deck path

The current profile references:

```text
Stream Deck action
  -> A:\AI\Tools\EstateStreamDeckMVP\08-Start-Resident-Gateway.cmd
  -> C:\Program Files\PowerShell\7\pwsh.exe -NoLogo -NoProfile
       -ExecutionPolicy Bypass -File A:\AI\Tools\EstateStreamDeckMVP\08-Start-Resident-Gateway.ps1
  -> Estate-Service-Control.ps1 -Action Gateway
  -> Start-Gateway
  -> Start-HiddenProcess
  -> C:\Python314\python.exe -c
       from estate.core.resident_gateway import serve;
       serve(host='127.0.0.1', port=11435, root=r'A:\theestate')
```

The working directory is `A:\theestate`. The direct command does not set an
explicit `PYTHONPATH`; import resolution is therefore based on that working
directory and the installed Python environment. The parallel Core service
configuration instead declares `PYTHONPATH=A:\theestate\src` and invokes:

```text
C:\Python314\python.exe -m estate.cli.main resident-gateway start
  --host 127.0.0.1 --port 11435
```

That Core configuration is not the path called by the current top-level
Stream Deck buttons.

The live listener is:

```text
PID 29864
  C:\Python314\python.exe -m estate.cli.main resident-gateway start
  --host 127.0.0.1 --port 11435
```

This confirms the running Gateway is also using the old `A:\theestate`
runtime root rather than `A:\theestate-wp4233`.

### Grace runtime path

No separate Grace service process, Stream Deck launcher, port, or executable
was found. Grace is registered within the Gateway resident model map as
`estate/grace`. The Gateway exposes the resident catalog at
`http://127.0.0.1:11435/v1/models` and the read-only probe returned the Estate
resident catalog, including Grace and the other resident identities.

The Gateway source also contains the Grace runtime bridge and Grace operations
request handling. Therefore the current startup chain for Grace is:

```text
Gateway startup at 127.0.0.1:11435
  -> resident_gateway.ACTIVE_RESIDENT_MODELS
  -> estate/grace resident route
  -> Grace runtime bridge when a matching operation is requested
```

There is no independent Grace DATA_DIR or Grace listener established by the
inspected Stream Deck startup path.

## State, database, and repository paths

### Open WebUI

The launcher explicitly establishes:

| Item | Observed value |
|---|---|
| Executable | `A:\AI\OpenWebUI\.venv\Scripts\open-webui.exe` |
| Working directory | `A:\AI\OpenWebUI` |
| Host/port | `127.0.0.1:8080` |
| DATA_DIR | Not set by the launcher |
| DATABASE_URL | Not set by the launcher |
| Package default | `A:\AI\OpenWebUI\.venv\Lib\site-packages\open_webui\data\webui.db` |
| Installation DB | `A:\AI\OpenWebUI\webui.db` |
| Recovery DB | `A:\AI\Backups\OpenWebUI\Before-Grace-Redeploy-2026-07-28_18-16-57\webui.db` |

The installed Open WebUI environment code computes `DATA_DIR` from the
`DATA_DIR` environment variable or, when absent, the package backend data
directory. It computes `DATABASE_URL` from `DATABASE_URL` or
`DATA_DIR/webui.db`. No launcher-side override was found.

Read-only SQLite inspection found:

| Database | Users | Models | Config rows | Interpretation |
|---|---:|---:|---:|---|
| `A:\AI\OpenWebUI\webui.db` | 0 | 0 | 0 | Empty installation-root DB |
| `.venv\Lib\site-packages\open_webui\data\webui.db` | 0 | 0 | 380 | Configured package-data DB with no user |
| `A:\AI\Backups\OpenWebUI\Before-Grace-Redeploy-2026-07-28_18-16-57\webui.db` | 1 | 0 | 380 | Valid pre-redeploy recovery DB |

The latest captured WebUI stderr log,
`A:\AI\Tools\EstateStreamDeckMVP\Core\state\logs\open_webui-20260731-200734.stderr.log`,
records an SQLite `UNIQUE constraint failed: config.key` during application
startup followed by `Application startup failed. Exiting.` The log proves a
database/configuration startup failure occurred; it does not alone prove which
of the two installation databases was selected. The competing package-data
database and the absence of an explicit database selection make that database
choice the leading explanation.

### Resident Gateway

The top-level controller has no separate `DATA_DIR` argument. It passes the
repository root `A:\theestate` directly to `serve`. The Gateway source uses
that root for its runtime and resident operations paths. The state path
declared by the service-control ecosystem is under
`A:\AI\Tools\EstateStreamDeckMVP\Core\state`, principally for launcher logs
and PID/status bookkeeping; it is not a blue/green deployment state store.

The current live `/v1/models` response demonstrates that the Gateway is
serving a resident catalog. The legacy launcher did not perform that semantic
check before reporting startup success.

### PID state

`A:\AI\Tools\EstateStreamDeckMVP\estate-service-pids.json` contains PIDs
from an earlier start (for example Gateway PID 40356 and WebUI PID 1772),
while the current listeners have different PIDs (Gateway 29864 and WebUI
44392/44848/45016). This makes the JSON a stale historical bookkeeping file,
not a reliable current slot or process source of truth.

## Readiness and success semantics

The actual top-level Stream Deck chain uses `Test-Port`/`Wait-Port`. A service
can therefore be reported as started when a process has opened a TCP socket,
even if:

- the process is serving the wrong repository or database;
- application initialization later fails;
- the Gateway resident catalog is incomplete;
- Open WebUI is at first-run admin setup;
- expected Estate objects are absent;
- a different process already owns the port.

The alternate Core library is stronger: it checks expected process identity and
HTTP health URLs and waits for HTTP readiness. However, it is not invoked by
the current `08-*` and `10-*` Stream Deck actions. Even that alternate path is
not shown in the inspected startup chain to validate Open WebUI’s expected user
or database identity, nor to validate the semantic contents of the Gateway
model catalog.

Accordingly, startup can succeed against an empty or wrong database, and the
launcher does not validate expected Estate objects before reporting success.

## Blue/green, active slot, and promotion controls

No blue/green slot metadata, service active-slot file, promotion record, or
slot-selection source of truth was found in the actual Gateway/WebUI startup
chain or the service controller.

The Stream Deck package does contain an independent `OperatorDeck` group:

- `OperatorDeck\Controls\SelectActive.cmd` invokes
  `A:\theestate\tools\operator-deck\OperatorDeck.ahk select-active`.
- `OperatorDeck\Slots\*.cmd` invoke `... OperatorDeck.ahk slot <slot>`.
- `OperatorDeck\Cycle\*.cmd` invoke `... OperatorDeck.ahk cycle-slot <slot>`.

The AutoHotkey implementation reads `config.ini` slot geometry and writes
window-placement files such as `runtime\window-promotion.ini`. These are
desktop-window placement and promotion controls, not service deployment
promotion. They do not select the Gateway source tree, Open WebUI database,
or a blue/green runtime slot.

Thus the Stream Deck startup buttons bypass any hypothetical deployment
control: they invoke the legacy service controller directly. The only observed
“active” and “promotion” controls concern windows and remain hard-coded to the
old `A:\theestate` tree.

## Verified facts versus hypotheses

### Verified facts

- The current v0.4 profile action paths are the two `.cmd` wrappers listed
  above.
- Those wrappers call PowerShell 7 and `Estate-Service-Control.ps1`.
- The legacy controller embeds Gateway root `A:\theestate`, port 11435, and
  WebUI executable/root/port values shown above.
- The live Gateway command line uses `C:\Python314\python.exe` and port 11435.
- The live WebUI process tree uses the A:\AI Open WebUI virtual environment and
  port 8080.
- The clean audit repository `A:\theestate-wp4233` is not in these startup
  commands.
- The launcher does not set `DATA_DIR` or `DATABASE_URL`.
- Both installation DBs and the pre-redeploy backup DB exist with the row
  counts recorded above.
- The launcher waits for sockets rather than validating database or Estate
  object semantics.
- The Gateway’s resident catalog defines and serves `estate/grace`.
- The Stream Deck OperatorDeck controls use the old root and write window
  placement state, not application deployment state.
- The PID JSON does not match the currently observed listener PIDs.

### Hypotheses requiring a controlled follow-up

- The exact WebUI database used by every historical launch attempt cannot be
  proven from the launcher command line alone because an inherited process
  environment could override `DATA_DIR` or `DATABASE_URL`. The package-data
  DB is the default and is the leading explanation for the observed
  configuration conflict.
- The current Open WebUI first-run admin state is most likely caused by the
  default/selected DB having zero users, or by a fresh DB being created after a
  failed migration. The evidence establishes that such a DB exists and that
  the launcher does not prevent its use; it does not identify a single
  historical process environment with certainty.
- The latest startup failure may belong to a launch attempt distinct from the
  currently listening process because the log and process tree were observed
  independently. The failure is real; process-to-log PID ownership was not
  reconstructed by this read-only audit.

## Exact smallest corrective action

The smallest safe correction is to make one startup controller authoritative
and make it fail closed on application identity, not merely port availability:

1. Point the Stream Deck Gateway action at the intended, explicitly selected
   Estate worktree and remove the hard-coded ambiguity between
   `A:\theestate` and `A:\theestate-wp4233`.
2. Give the WebUI launcher one explicit, documented `DATA_DIR`/`DATABASE_URL`
   pointing at the approved canonical state database; do not select between
   installation-root and package-data databases implicitly.
3. Route the buttons through the stronger Core service startup path, or bring
   its process/HTTP checks into the one authoritative controller.
4. Require semantic checks before success: the Gateway `/v1/models` response
   must contain the expected resident records, and WebUI must be checked
   against the approved state/database identity and expected Estate integration
   rather than TCP listening alone.
5. Make PID/status metadata derived from the authoritative process checks, not
   an unverified stale PID map. Keep OperatorDeck window placement separate
   from service deployment selection.

This is a recommendation only. No correction was implemented in this audit.

## Preservation result

- No source files were modified.
- No Stream Deck configuration was modified.
- No service was restarted or stopped.
- No database was written.
- No deployment or promotion action was taken.
- The historical Open WebUI backup was read only.
- The clean audit worktree was preserved pending report commit.

