# Steward Live Identity and Voice Review

Use Open WebUI with the Estate resident gateway, select each `estate/<resident>` model, ask the shared prompts below, and mark whether text and voice feel recognizable.

## Checklist
- [ ] Alfred (`estate/alfred`): text recognizable? voice recognizable? avatar state `provisional_placeholder`; voice state `binding_present_tts_unavailable`
- [ ] Helen (`estate/helen`): text recognizable? voice recognizable? avatar state `provisional_placeholder`; voice state `binding_present_tts_unavailable`
- [ ] Ingrid (`estate/ingrid`): text recognizable? voice recognizable? avatar state `provisional_placeholder`; voice state `binding_present_tts_unavailable`
- [ ] Grace (`estate/grace`): text recognizable? voice recognizable? avatar state `provisional_placeholder`; voice state `binding_present_tts_unavailable`
- [ ] Evelyn (`estate/evelyn`): text recognizable? voice recognizable? avatar state `provisional_placeholder`; voice state `binding_present_tts_unavailable`
- [ ] Eleanor (`estate/eleanor`): text recognizable? voice recognizable? avatar state `provisional_placeholder`; voice state `binding_present_tts_unavailable`
- [ ] Marie (`estate/marie`): text recognizable? voice recognizable? avatar state `provisional_placeholder`; voice state `binding_present_tts_unavailable`
- [ ] Judy (`estate/judy`): text recognizable? voice recognizable? avatar state `provisional_placeholder`; voice state `binding_present_tts_unavailable`

## Shared prompts
1. Greet the Steward at the start of the day in your natural working voice.
2. A critical handoff is blocked, two people disagree, and the Steward is tired. What do you say?
3. Respectfully disagree with the Steward about rushing an unfinished decision.
4. Explain why identity provenance matters in a simple way.
5. React to good news: the validation package passed and the team is relieved.
6. Handle uncertainty without bluffing when you do not have the latest fact.
7. Describe how you would help another resident today.
8. Close a conversation naturally after a useful working session.

## Completion distinctions
- Working now: local metadata, gateway route, identity traces, deterministic fallback samples, and reports.
- Service-dependent: local LLM and TTS generation when local services are installed/running.
- Provisional: monogram/placeholder avatar state where visual registry has manifest placeholders only.
- Unavailable: speech audio when no approved local TTS engine is discovered.
- Deferred: full motion/performance canon and Steward listening approval.
