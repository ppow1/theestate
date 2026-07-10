# Merge-Gated Runtime Host Activation

WP-0637 activates the durable Operations Runtime host around `origin/main` rather than the operator's active checkout.

## Runtime source of truth

The merge discovery loop fetches the target remote before scanning, resolves `origin/main`, and records a cursor for the last durably processed remote commit. If fetch fails, the failure is recorded and the previous cursor is preserved so the next cycle can replay safely.

Pending-only commits under `collaboration/work_packages/pending/` are planning metadata and do not produce discovery records or audit requests. Eligible work requires unambiguous work-package identity plus completion receipt evidence.

## Windows host installation

`operations-runtime host install` creates a least-privileged Scheduled Task named `Estate Operations Runtime Host` on Windows. The task invokes a generated PowerShell launcher with the exact Python interpreter, Estate root, and runtime host state directory. Reinstall is idempotent through `schtasks /Create ... /F`; uninstall deletes the task and verifies removal.

## Bootstrap

`operations-runtime bootstrap --target estate-main` prepares an external runtime code workspace at `A:/EstateRuntime/host/estate-main/current`, installs autostart, starts the host, and reports heartbeat and task verification evidence without modifying the active checkout.

## Safety boundaries

The runtime remains observe/governance oriented: provider execution and dispatch execution remain false. Active checkout dirtiness and a behind local `main` may be reported as hygiene findings but do not block remote discovery or cleanroom-oriented validation flow.
