CLS

<#
.SYNOPSIS
    Discovers the locally installed Codex CLI command surface without submitting prompts.

.DESCRIPTION
    This diagnostic inventories the Codex executable, version, top-level help,
    discovered subcommands, subcommand help, timing, exit codes, stdout/stderr,
    and basic safety classifications.

    By default, it runs only non-prompt discovery operations such as --help,
    --version, and discovered subcommand --help calls.

    Use -RunReadOnlyProbes to additionally try selected read-only status-style