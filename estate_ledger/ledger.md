# Estate Ledger

## EC-000001 - Founding of the Estate

Timestamp: 2026-06-29
Location: A:\theestate
Status: Ratified
Classification: Estate Internal

Summary:
The Estate was established as a local-first institution on the dedicated AI NVMe.

## EC-000002 - Founding Governance Package

Timestamp: 2026-06-29
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Created Constitution v0.1, founding residents register, organization chart, Estate Change Process, ID standard, document header standard, Archives doctrine, security clearance policy, resource allocation policy, and chat momentum monitor.


## EC-000003 - Created Estate Builder v0.1

Timestamp: 2026-06-29 20:15:58
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Created the first local Estate maintenance tool for generating Estate Change records, resident records, ledger entries, and devlog entries.



## EC-000004 - Created Estate Core v0.2

Timestamp: 2026-06-29 20:26:34
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Created the first Estate Core Python package with object registry, ledger manager, resident registration, and CLI foundation.


## EC-000005 - Registered Resident Alfred

Timestamp: 2026-06-29 20:26:34
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Created resident record RES-000001 for Alfred, serving as Manager of Administration in Administration.


## EC-000006 - Registered Resident Ingrid

Timestamp: 2026-06-29 20:26:34
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Created resident record RES-000002 for Ingrid, serving as Manager of Security in Security.


## EC-000007 - Registered Resident Helen

Timestamp: 2026-06-29 20:26:35
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Created resident record RES-000003 for Helen, serving as Manager of Human Resources in Human Resources.


## EC-000008 - Registered Resident Eleanor

Timestamp: 2026-06-29 20:26:35
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Created resident record RES-000004 for Eleanor, serving as Manager of Archives / Registrar in Archives.


## EC-000009 - Registered Resident Marie

Timestamp: 2026-06-29 20:26:35
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Created resident record RES-000005 for Marie, serving as Manager of Research in Research.


## EC-000010 - Registered Resident Judy

Timestamp: 2026-06-29 20:26:35
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Created resident record RES-000006 for Judy, serving as General Counsel in Legal.


## EC-000011 - Added Python cache ignore rules

Timestamp: 2026-06-29 20:29:23
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Added .gitignore rules for Python cache files and removed committed __pycache__ artifacts from Git tracking.


## EC-000012 - Created Service and Capability Registries

Timestamp: 2026-06-29 20:39:17
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Added initial Estate Service Registry and Capability Registry to track callable services and local AI resources including RTX 4090 CUDA, Kokoro TTS, F5-TTS, ComfyUI, FFmpeg, and pending Whisper.


## EC-000013 - Added service and capability CLI views

Timestamp: 2026-06-29 20:42:29
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Updated Estate Core CLI to list registered services and capabilities and expanded status output to include service and capability counts.


## EC-000014 - Added Provider Registry

Timestamp: 2026-06-29 20:51:45
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Added provider registry to separate stable service needs from interchangeable AI resources such as Kokoro, F5-TTS, ComfyUI, and pending Whisper.


## EC-000015 - Added AI Environment Discovery Service

Timestamp: 2026-06-29 20:58:10
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Added discovery support for observing A:\AI paths, Python environments, TTS installations, tools, and model categories without manually declaring them first.


## EC-000016 - Enhanced discovery with Ollama observation

Timestamp: 2026-06-29 21:19:14
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Updated AI environment discovery to observe Ollama version, runtime availability, and installed Ollama models.


## EC-000017 - Parsed Ollama models into structured observations

Timestamp: 2026-06-29 21:21:43
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Updated Ollama discovery to parse installed models into structured name, id, size, and modified fields for future routing and provider selection.


## EC-000018 - Synced observed Ollama model providers

Timestamp: 2026-06-29 21:34:01
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Synced observed Ollama models into provider registry:
- PRV-000005 Ollama qwen2.5-coder:7b
- PRV-000006 Ollama llama3.2:3b


## EC-000019 - Added Estate Change Validation Standard

Timestamp: 2026-06-29 21:35:49
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Codified that no Estate Change is complete until syntax validation, runtime validation, Git validation, and ledger validation pass before commit.


## EC-000020 - Added Discovery change detection

Timestamp: 2026-06-29 21:47:49
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Enhanced AI environment discovery to compare current observations against the previous snapshot, report additions and removals, and preserve timestamped observation history.

## EC-000021 - Reconciled Discovery change detection commit identity

Timestamp: 2026-06-29 21:55:00
Location: A:\theestate
Status: Ratified
Classification: Estate Internal

Summary:
Reconciled ledger identity for the Discovery change detection work committed as EC-000021. The CLI-generated Estate Change entry was EC-000020 due to prior numbering drift. This entry preserves history without rewriting prior records.

## EC-000022 - Added Estate audit concept

Timestamp: 2026-06-29 21:56:00
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Added the next operating requirement: Estate Audit must detect EC drift, syntax failures, runtime failures, registry issues, and commit/ledger mismatch before changes are considered complete.


## EC-000023 - Added Discovery human-readable report

Timestamp: 2026-06-29 22:18:47
Location: A:\theestate
Status: Draft
Classification: Estate Internal

Summary:
Added a Discovery report command that summarizes latest AI environment observations, changes, tools, TTS items, Python environments, and Ollama models in human-readable form.
