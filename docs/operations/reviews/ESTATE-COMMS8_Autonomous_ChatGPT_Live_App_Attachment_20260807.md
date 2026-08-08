# Estate Autonomous ChatGPT Live App Attachment

> Superseding note (2026-08-07): accepted manual promotion evidence proves
> the production registration exists in Pat's Workspace 2026. The supported
> Plugins → Estate Comms8 → Try in chat flow opened a fresh Work surface with
> the installed app attached. Observed installed identity:
> `plugin_asdk_app_6a727af28db8819188d92bdfd52a950c`; the attached chip is
> displayed as `Estate Comms8`, while the governed production identity is
> Estate Comms8 Live. No app was created or reconnected.
>
> The worker now prefers `surface=work` and verifies the installed identity,
> workspace, authentication, composer, and governed seven-action manifest.
> Readiness passed and an authoritative `claim_next` occurred, but ChatGPT
> supplied `worker_id=codex-workmode-estate-reasoner` and stopped at
> `acknowledged`. The prompt now explicitly requires `worker_id=chatgpt`.
> Precise blocker: `CHATGPT_WORKER_WRONG_WORKER_ID_OR_INCOMPLETE_LIFECYCLE`.

Status: Readiness guard implemented; Live app registration remains blocked

## Readiness contract

Before the generic mailbox prompt is submitted, the existing CDP target must
be authenticated, challenge-free, workspace-valid, have the visible
composer, expose the exact `Estate Comms8 Live` attachment outside the chat
sidebar, and expose all seven canonical Comms8 actions. The worker then
submits the unchanged generic prompt containing no request ID.

The browser helper returns a structured `READINESS_FAILED` result and does
not alter the composer when readiness fails. Prose `WORKER_COMPLETE` is never
authoritative; the worker still requires a resolved Comms8 record with a
stored response.

## Current evidence

The selected CDP target is authenticated and has a ready composer, but its
visible DOM does not prove an attached `Estate Comms8 Live` app. Only one
historical action name was found in the conversation text, not the complete
seven-action discovery set. The helper therefore classified the target as:

`LIVE_APP_NOT_FOUND`

No prompt was submitted by the readiness probe. The existing request
`ec8-8db54efb5c234f0a` remains untouched and queued.

The historical app identity receipt records that no production `Estate
Comms8 Live` registration was accepted; only Blue3 and historical numbered
apps were visible. The worker cannot safely attach an app that does not exist
in the governed ChatGPT workspace.

## Activation

Worker source changes require a worker restart/relaunch only. The dedicated
browser and ChatGPT reconnect are conditional and required only after a
supported production Live app registration is available or the current CDP
session loses authentication. Open WebUI, Grace Resident Gateway, Comms8,
the MCP adapter, Runtime Host, and workstation restart are not required.

After the Live app is registered, the smallest order is: keep or reconnect
the authenticated CDP browser, launch one worker activation, verify the
readiness metadata, then verify the authoritative `claim_next` event for the
existing request. No new request may be created.
