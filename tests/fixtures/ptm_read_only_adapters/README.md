# PTM read-only adapter contract fixtures

These records are synthetic and sanitized. They model bounded shapes observed in
Parking Lot, work-package, Dispatch, validation, and acceptance sources. They
are test inputs only: they are not a registry, queue, acceptance record, or
authoritative PTM dataset.

`WP-9103-invalid-hash.md` intentionally contains a false, untrusted hash string;
the adapter must calculate provenance from source bytes rather than normalize or
trust that field. Tests construct absent, stale, oversized, and escaping inputs
at runtime so the committed fixture set remains small and safe.
