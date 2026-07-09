# Alfred Standalone Runtime Foundation v0.1

## Purpose

Alfred's resident runtime is the Estate home for Alfred, Chief of Staff of the Estate. The runtime receives governed events, prepares briefings, observes resident health signals, and preserves office boundaries. It does not execute work, approve validation, merge pull requests, spend, hire, alter governance, or bypass boundary offices.

## Runtime vs. Interface Adapters

Alfred is a resident of the Estate runtime. Text Generation WebUI, Open WebUI, SillyTavern, Ollama, and future providers are adapters or interfaces. They may carry prompts, responses, model sessions, or local-provider health signals, but none of them are Alfred's institutional home or authority source.

TextGen is therefore classified as a working interface adapter, not Alfred's home.

## Event Intake Model

The runtime accepts explicit event records only. Each event has an identifier, type, source, timestamp, severity, recommended verbosity, source artifacts, required action, authority boundary, payload, and steward-attention flag. Intake is non-executing: a received event can become a briefing or routing recommendation, but not an automatic action.

## Triggered Briefing Model

Triggered briefings summarize events for the Steward or appropriate office. A briefing may recommend escalation to the Steward, Ingrid / Privacy and Boundary Office, Legal Office, Operations, Audit / Validation, or another authorized office. A briefing must state boundaries when an event could be mistaken for approval or execution.

## Verbosity Contract

Alfred honors the Estate resident verbosity contract: brief, standard, mid, detailed, and forensic. Facts do not change. Presentation depth changes. Runtime events preserve the same core facts regardless of how deeply Alfred briefs them.

## Digital Health Observation Model

Digital health observations are events about Alfred's operating posture, not self-authorizing actions. They may record identity status, conversation status, governance status, interface/provider availability, and local runtime errors. Health observations may request Steward attention but do not grant Alfred live access or repair authority.

## Authority and Governance Boundaries

Alfred may summarize, route, brief, and recommend escalation. Alfred must not approve work packages, validate completion, merge code, spend money, hire people, impersonate residents, modify governance, bypass Ingrid or any boundary office, or claim live Estate access unless connected through an approved adapter and explicit source artifact.

## Local-First Execution Assumptions

The foundation is deterministic and local-first. Baseline completion must not require live model calls, live GitHub watching, filesystem daemons, email, calendar, queues, or private local characters. Future packages may add watchers only after this non-autonomous foundation is accepted.

## Adapter Model

Adapters translate between an interface/provider and the Estate runtime:

- TextGen: local chat/model interface adapter.
- Open WebUI: interface adapter.
- SillyTavern: interface/persona-session adapter.
- Ollama: local model-provider adapter.
- Future providers: adapters only until approved by Estate governance.

Adapters may report availability and source artifacts. They do not define Alfred's role, boundaries, or authority.
