# Architecture

`src/browser.ts` owns all browser/session and selector behavior. `src/sync.ts` inventories first, checkpoints the index after every conversation, retries bounded transient extraction failures, and writes per-run reports. `src/storage.ts` provides normalization, SHA-256 hashing, rendering, and atomic persistence. `src/validate.ts` validates index-to-latest identity and content hashes. `src/cli.ts` exposes manual and scheduled commands.

The source archive is neutral and conversation-first. Classification by repository, office, project, topic, or sensitivity is optional downstream metadata and is never an export filter.
