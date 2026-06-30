# Development Log

## 2026-06-29

Established A:\theestate as the local Estate root.

Created the founding governance package.

Codified:
- Steward sovereignty
- Office vs occupant separation
- Residents vs workers
- Security clearance
- Resource allocation
- Archives continuity
- Estate Change Process
- Chat momentum monitor

## 2026-06-29 20:15:58

EC-000003 - Created Estate Builder v0.1

Created the first local Estate maintenance tool for generating Estate Change records, resident records, ledger entries, and devlog entries.


## 2026-06-29 20:26:34

EC-000004 - Created Estate Core v0.2

Created the first Estate Core Python package with object registry, ledger manager, resident registration, and CLI foundation.


## 2026-06-29 20:26:34

EC-000005 - Registered Resident Alfred

Created resident record RES-000001 for Alfred, serving as Manager of Administration in Administration.


## 2026-06-29 20:26:34

EC-000006 - Registered Resident Ingrid

Created resident record RES-000002 for Ingrid, serving as Manager of Security in Security.


## 2026-06-29 20:26:35

EC-000007 - Registered Resident Helen

Created resident record RES-000003 for Helen, serving as Manager of Human Resources in Human Resources.


## 2026-06-29 20:26:35

EC-000008 - Registered Resident Eleanor

Created resident record RES-000004 for Eleanor, serving as Manager of Archives / Registrar in Archives.


## 2026-06-29 20:26:35

EC-000009 - Registered Resident Marie

Created resident record RES-000005 for Marie, serving as Manager of Research in Research.


## 2026-06-29 20:26:35

EC-000010 - Registered Resident Judy

Created resident record RES-000006 for Judy, serving as General Counsel in Legal.


## 2026-06-29 20:29:23

EC-000011 - Added Python cache ignore rules

Added .gitignore rules for Python cache files and removed committed __pycache__ artifacts from Git tracking.


## 2026-06-29 20:39:17

EC-000012 - Created Service and Capability Registries

Added initial Estate Service Registry and Capability Registry to track callable services and local AI resources including RTX 4090 CUDA, Kokoro TTS, F5-TTS, ComfyUI, FFmpeg, and pending Whisper.


## 2026-06-29 20:42:29

EC-000013 - Added service and capability CLI views

Updated Estate Core CLI to list registered services and capabilities and expanded status output to include service and capability counts.


## 2026-06-29 20:51:45

EC-000014 - Added Provider Registry

Added provider registry to separate stable service needs from interchangeable AI resources such as Kokoro, F5-TTS, ComfyUI, and pending Whisper.


## 2026-06-29 20:58:10

EC-000015 - Added AI Environment Discovery Service

Added discovery support for observing A:\AI paths, Python environments, TTS installations, tools, and model categories without manually declaring them first.


## 2026-06-29 21:19:14

EC-000016 - Enhanced discovery with Ollama observation

Updated AI environment discovery to observe Ollama version, runtime availability, and installed Ollama models.


## 2026-06-29 21:21:43

EC-000017 - Parsed Ollama models into structured observations

Updated Ollama discovery to parse installed models into structured name, id, size, and modified fields for future routing and provider selection.


## 2026-06-29 21:34:01

EC-000018 - Synced observed Ollama model providers

Synced observed Ollama models into provider registry:
- PRV-000005 Ollama qwen2.5-coder:7b
- PRV-000006 Ollama llama3.2:3b


## 2026-06-29 21:35:49

EC-000019 - Added Estate Change Validation Standard

Codified that no Estate Change is complete until syntax validation, runtime validation, Git validation, and ledger validation pass before commit.


## 2026-06-29 21:47:49

EC-000020 - Added Discovery change detection

Enhanced AI environment discovery to compare current observations against the previous snapshot, report additions and removals, and preserve timestamped observation history.

## 2026-06-29 21:55:00

EC-000021 - Reconciled Discovery change detection commit identity

Preserved the fact that Discovery change detection committed as EC-000021 while the CLI-generated ledger entry used EC-000020.

## 2026-06-29 21:56:00

EC-000022 - Added Estate audit concept

Defined the need for Estate Audit to detect numbering drift and validation failures before future commits.


## 2026-06-29 22:18:47

EC-000023 - Added Discovery human-readable report

Added a Discovery report command that summarizes latest AI environment observations, changes, tools, TTS items, Python environments, and Ollama models in human-readable form.


## 2026-06-29 22:27:18

EC-000024 - Added Estate Audit command

Implemented Estate Audit command to validate Python syntax, selected CLI runtime commands, JSON registries, Git cleanliness, and latest EC alignment between Git and the ledger.


## 2026-06-29 22:40:56

EC-000025 - Matured Estate Audit integrity checks

Expanded Estate Audit to validate required Estate paths, registry record shape, duplicate registry IDs, observation history presence, and latest ledger EC presence in the development devlog.


## 2026-06-29 22:54:11

EC-000026 - Refactored Estate Audit check groups

Grouped Estate Audit checks into focused internal functions without changing audit behavior. This prepares Audit for continued maturation without turning run_audit into an oversized procedural block.


## 2026-06-29 22:56:56

EC-000027 - Improved Estate Audit report grouping

Grouped Estate Audit report output by check domain without changing validation behavior. This makes Audit results easier to scan during development and repair sessions.


## 2026-06-29 22:58:01

EC-000028 - Added Estate Audit JSON output

Added --json support to the Estate Audit command so audit results can be emitted as structured machine-readable data while preserving the existing human-readable report.


## 2026-06-29 22:59:04

EC-000029 - Added Estate Audit CLI inventory validation

Added an Audit runtime check that validates the Estate CLI help output includes the expected command inventory.


## 2026-06-29 23:00:39

EC-000030 - Added Estate Audit ledger structure validation

Added ledger structure validation to Estate Audit, including sequential EC numbering, duplicate EC detection, and required field checks for ledger entries.


## 2026-06-29 23:03:10

EC-000031 - Added Estate Audit devlog structure validation

Added devlog structure validation to Estate Audit, including EC entry presence, duplicate EC detection, and latest devlog-to-ledger alignment.


## 2026-06-29 23:06:15

EC-000032 - Added Discovery operational validation bundle

Added a bundled set of Discovery-focused Audit checks covering latest observation shape, historical observation JSON validity, observation history presence, and Discovery report contract validation.


## 2026-06-29 23:07:30

EC-000033 - Added Discovery JSON report command

Added --json support to discovery-report and extended Audit to validate the machine-readable Discovery report command.


## 2026-06-29 23:21:37

EC-000034 - Added Discovery status command

Added discovery-status with JSON support and extended Audit to validate its machine-readable status contract.


## 2026-06-29 23:26:35

EC-000035 - Added Discovery persistent catalog

Added persistent Discovery Catalog support, automatic catalog updates from observations, discovery-catalog CLI output, and Audit validation for catalog schema, command JSON, and latest observation coverage.


## 2026-06-29 23:29:47

EC-000036 - Added Discovery lifecycle command and metrics

Added the discover lifecycle command, persisted Discovery cycle metrics, and extended Audit coverage for the lifecycle command, metrics file, CLI inventory, and new Discovery modules.


## 2026-06-29 23:30:37

EC-000037 - Repaired Discovery lifecycle observation handling

Repaired Discovery lifecycle metrics generation by normalizing tuple-shaped observe_ai_environment results before metric extraction.


## 2026-06-29 23:32:19

EC-000038 - Repaired Discovery catalog wrapper contract

Repaired the Discovery catalog wrapper to normalize tuple-shaped observation results before catalog synchronization, fixing the Discovery lifecycle observe step failure.


## 2026-06-29 23:34:45

EC-000039 - Separated Discovery runtime state from versioned state

Moved mutable Discovery catalog, metrics, and latest observation state to runtime/discovery and ignored runtime state in Git. Audit now validates runtime Discovery state instead of treating normal runtime mutation as versioned institutional change.


## 2026-06-29 23:36:28

EC-000040 - Completed Discovery runtime state migration

Completed runtime latest observation migration so Discovery writes runtime/discovery/ai_environment_latest.json, Audit validates runtime latest state, and the stale versioned observations/ai_environment_latest.json file is removed.


## 2026-06-29 23:47:41

EC-000041 - Completed Discovery writer runtime separation

Redirected remaining Discovery observation writes into runtime/discovery and removed stale versioned latest observation state.


## 2026-06-29 23:50:43

EC-000042 - Contained legacy Discovery observation writer

Contained legacy Discovery writes so normal Discovery runs no longer leave observations/ dirty. New runtime observations are moved into runtime/discovery/observations and versioned latest observation output is removed.
