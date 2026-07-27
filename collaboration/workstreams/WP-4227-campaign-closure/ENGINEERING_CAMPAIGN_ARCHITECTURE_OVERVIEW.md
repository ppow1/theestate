# Engineering Campaign architecture overview

## Layer map

| Package | Repository boundary | Published responsibility | Direct campaign input |
|---|---|---|---|
| WP-4220 | `WP-4218` (legacy staging name) | normalized engineering queue | explicit source snapshots |
| WP-4221 | `WP-4219` (legacy staging name) | immutable dashboard projection | WP-4220 queue |
| WP-4222 | `WP-4222` | provider registration and dashboard integration envelope | WP-4220 queue and WP-4221 projection |
| WP-4223 | `WP-4223-recommendation-engine` | deterministic advisory recommendations | WP-4222 integration envelope |
| WP-4224 | `WP-4224-decision-ledger` | immutable advisory review history | published WP-4223 output |
| WP-4225 | `WP-4225-analytics` | deterministic historical measurements | published WP-4220–WP-4224 values |
| WP-4226 | `WP-4226` and `estate.core.engineering_campaign_replay` | capture and replay of all six published values | published WP-4220–WP-4225 values |

```text
explicit snapshots
      |
      v
WP-4220 queue -> WP-4221 projection -> WP-4222 integration
                                           |
                                           v
                          WP-4223 recommendations
                                           |
                                           v
                              WP-4224 review ledger
                                           |
                                           v
                              WP-4225 analytics
                                           |
                                           v
                         WP-4226 capture and replay
```

WP-4225 deliberately receives the earlier published values as an observation bundle; WP-4226
deep-copies all six values. These fan-in edges do not point backward and do not form cycles.
Optional WP-4214, WP-4215, and WP-4217 evidence is referenced through versioned provider values,
not reimplemented.

## Interface and schema rules

Every boundary uses a versioned `estate.* /v1` JSON contract and rejects an unsupported major
version. Identifiers and hashes are derived from canonical JSON or explicit source identity;
timestamps affecting freshness are caller supplied or captured as provenance. Logical hashes
exclude intentionally volatile display timestamps where documented. The campaign has 22 schema
documents with 22 unique `$id` values; similar comparison documents belong to distinct package
contracts and are not duplicate definitions.

Schema field names vary by artifact type (`schema_version`, `snapshot_schema_version`, and
domain-specific equivalents). This is intentional published-contract vocabulary, not competing
definitions. A future coordinated major-version migration may normalize envelopes, but changing
v1 names here would invalidate fixtures and downstream consumers.

## Authority boundary

The chain observes, projects, recommends, records review, measures, and replays. It never assigns
or dispatches work; reprioritizes or modifies Parking Lot/WIP records; merges pull requests;
modifies Git; schedules execution; or grants execution or approval authority. “Priority” is a
copied or mechanically explained advisory value. “Accepted for future planning” is a review
disposition, not authorization. CLIs read explicit files and either emit JSON to stdout or write
only an explicitly requested diagnostic artifact.

