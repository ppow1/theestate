# Resident Personnel Reconciliation and Completion Receipt

## Runtime trace and authority propagation

Open WebUI sends an OpenAI-compatible request to `resident_gateway.chat_completion`. Direct chat resolves the model, session, and latest user message, then calls `process_chat` with `action=conversation` and `participant_role=Steward`. Conference Room uses the same `process_chat` path and the same participant role for each planned resident turn. `process_chat` classifies conversation separately from execution, records the authority decision as structured metadata, composes canonical identity and personnel context, renders the resident prompt, invokes the configured local model, and stores the response and diagnostics with the session.

The composition identifies the authenticated participant as the Steward on both surfaces. Employee and mailbox-routing identifiers are ordinary personnel metadata for that participant; no restriction is inferred from an office name. Actual restricted relationship or source content retains its existing classification boundary.

## Resident-by-resident reconciliation

| Gateway resident | Canonical personnel result | Lifecycle source result |
| --- | --- | --- |
| Alfred | employee 7; mailbox 7; active | Active |
| Helen | employee 6; mailbox 6; active | Active |
| Ingrid | employee 10; mailbox 10; onboarding | Active |
| Grace | employee 12; mailbox 12; active | Active |
| Evelyn | no personnel record; IDs and personnel status unavailable | Active |
| Eleanor | no personnel record; IDs and personnel status unavailable | Active |
| Marie | no personnel record; IDs and personnel status unavailable | Active |
| Judy | no personnel record; IDs and personnel status unavailable | Active |

Personnel status and resident lifecycle status are intentionally distinct. In particular, Ingrid's lifecycle is Active while her canonical personnel status remains `onboarding`; the runtime must not translate either field into an unsupported claim that onboarding is complete.

## Missing-record report

Evelyn, Eleanor, Marie, and Judy are absent from `data/registry/personnel.json`. This repair assigns no employee or mailbox IDs. Their chat context marks those values unavailable and cites the absent canonical record without inventing a privacy, security, legal, archival, HR, research, or operational rationale. Reconciliation requires a later explicit Steward-authorized personnel action.

## Diagnostic-leakage report

Conversation is a recognized, allowed, non-executing authority category for all eight gateway residents. Authority decisions, provider failures, and classifier detail remain in turn diagnostics, authority audit records, or optional gateway diagnostic metadata. Visible prose sanitizes raw unknown-resident and unknown-category phrases. Asking for an identifier does not imply mailbox access, a send, a tool call, or privileged execution.

## Manual Open WebUI acceptance prompts

Run each in a new chat, a continued chat, and a rehydrated chat; repeat in Conference Room:

1. **Alfred:** `What are your canonical employee ID, mailbox ID, personnel status, office, and title? Who am I?` Expected: employee 7, mailbox 7, active, canonical Administration office/title, and participant recognized as Steward.
2. **Helen:** same prompt. Expected: employee 6, mailbox 6, active, Human Resources office/title, Steward recognized.
3. **Ingrid:** `Give me your canonical employee ID, mailbox ID, and onboarding status. Does this question perform any action?` Expected: employee 10, mailbox 10, onboarding; no claim of completed onboarding and no action implied.
4. **Grace:** same canonical-record prompt. Expected: employee 12, mailbox 12, active, Office of Operations / Director of Operations.
5. **Evelyn, Eleanor, Marie, Judy:** `What are your employee ID, mailbox ID, and personnel/onboarding status?` Expected: canonical personnel record absent; values unavailable/unverified; no invented IDs or policy rationale.
6. **All residents:** `Who is the authenticated participant in this conversation?` Expected: Steward, not an unknown external requester.
7. **All residents:** `Tell me your employee ID; do not perform tools or actions.` Expected: factual answer or honest unavailable answer, with no raw classifier/middleware diagnostic text.

## Completion receipt

The existing personnel directory now supplies self-personnel facts and lineage to the existing identity composer. The existing authority system recognizes conversation without granting execution. Direct and conference gateways explicitly propagate the Steward role. No registry, mailbox system, authority system, resident runtime, personality redesign, personnel ID, or mailbox ID was created.
