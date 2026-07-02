# Codex Handoff Generator v1

## Purpose

The Codex Handoff Generator lists pending Estate work packages and prints copy-ready Codex launch commands. The work package remains the source of truth; the generated command only points Codex at that contract.

## Steward Usage

From the repository root, run:

```bash
PYTHONPATH=src python -m estate.cli.main work-package-handoffs
```

For each pending work package, the command prints:

- Title
- Mode
- Repository-relative path
- Dependency notes detected in the work package text
- Copy-ready Codex command

The command format is:

```text
<MODE> TASK

Read:
<path>

and do exactly what it says.
```

## Mode Detection

Mode is detected from pending work package filenames:

- `_SERIES_` -> `SERIES`
- `_PARALLEL_` -> `PARALLEL`
- `_ARCHITECTURE_FIRST_` -> `ARCHITECTURE_FIRST`

Files without a supported mode token are skipped. The generator does not submit anything to Codex automatically.
