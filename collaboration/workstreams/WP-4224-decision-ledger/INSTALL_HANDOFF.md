# Install handoff

The component is staged and has no third-party runtime dependency. Copy the whole `WP-4224-decision-ledger` directory to an approved runtime only after review. Supply a persisted WP-4223 published JSON document to `create_ledger`; persist returned values outside the authoritative provider locations. Run `pytest -q tests` before installation. The diagnostic CLI must retain read-only filesystem permissions in operation. Installation and persistence policy remain Steward-controlled and are not performed by this work package.
