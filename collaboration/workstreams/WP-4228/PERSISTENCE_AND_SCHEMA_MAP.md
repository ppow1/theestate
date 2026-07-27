# Persistence and Schema Map

The canonical store is append-only `record_chain.jsonl`. Each envelope has schema version, stable record/correlation IDs, timestamp, idempotency key, previous hash, and record hash. The shared schema is under `schemas/`. Existing Grace, Helen, lifecycle, and Dispatch stores remain canonical for their domains; the proof records relationships and does not replace those stores.
