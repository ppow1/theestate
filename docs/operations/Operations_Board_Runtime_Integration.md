# Operations Board Runtime Integration

Status: Operationally Validated  
Classification: Estate Internal

## Purpose

The Operations Board aggregates existing Estate operational artifacts into a single runtime view. It is a generated operational snapshot for Steward and Chief Architect review, not a new governance source of truth.

## Inputs Consumed

The generator reads these artifacts when they are present:

- `collaboration/status/worker_inbox_summary.json`
- `runtime/collaboration/routing/latest.json`
- `runtime/collaboration/worker_inboxes/*.json`
- `runtime/audit/latest.json`
- `collaboration/audit/results/*.json`
- `data/registry/capabilities.json`
- `data/registry/services.json`
- `data/registry/residents.json`
- `data/registry/providers.json`

Missing optional inputs are reported as warnings and do not stop generation. Malformed JSON files are also reported as warnings and skipped.

## Generated Outputs

Running the generator writes:

- `runtime/operations/operations_board.json` — machine-readable snapshot.
- `operations/board/latest.md` — human-readable Operations Board.

Parent directories are created when needed.

## CLI Usage

Generate the board and print a concise human-readable summary:

```bash
python -m estate.cli.main operations-board
```

Generate the board and print the JSON snapshot:

```bash
python -m estate.cli.main operations-board --json
```

## Known Limitations

- The board only summarizes artifacts already present in the repository/runtime tree.
- It does not infer operational health unless an existing artifact provides supporting data.
- It does not invent lifecycle states; capabilities without one of the Estate lifecycle states are warned about.
- Git branch and commit are reported only when detectable from the current working tree.

## Operational Validation Support

The Operations Board supports operational validation by making scattered runtime signals reviewable in one place: routing decisions, worker inbox status, audit results, registry counts, and missing or malformed inputs. This reduces Steward cognitive load while preserving existing artifact ownership and institutional meaning.
