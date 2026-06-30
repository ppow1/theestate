
Local Filesystem Transport Adapter v1

Status: Initial Local Transport Adapter

1. Purpose

The Local Filesystem Adapter supports local-only and pre-promotion collaboration.

It is the safe working area before material is promoted to GitHub or another shared transport.

2. Local Paths

Local-only paths:

runtime/collaboration/local_only
runtime/collaboration/outbox
runtime/collaboration/dead_letter

Repository-local collaboration paths:

collaboration/messages
collaboration/work_packages
collaboration/promotions
collaboration/status
3. Use Cases

The local filesystem adapter supports:

Local 4090 worker outputs.
Temporary worker artifacts.
Pre-review generated summaries.
Private media generation.
Prompt-derived drafts.
Unapproved analysis.
Boundary review queues.
Dead-letter messages.
4. Rule

Local filesystem is where work may exist before promotion.

GitHub is where approved institutional material may be shared after promotion.

5. Future Local Transports

Future local transports may include:

SQLite.
Local message queues.
IPC.
File watchers.
Local REST services.
MCP servers.
