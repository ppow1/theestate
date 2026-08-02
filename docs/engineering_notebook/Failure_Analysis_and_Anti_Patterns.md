# Failure Analysis and Anti-Patterns

The standalone coding benchmarks showed that long transcripts cause context
loss, repeated onboarding, empty or malformed outputs, and missed final checks.
The notebook addresses continuity by carrying verified current state, not by
making the context window larger or replaying conversation history.

Anti-patterns include: treating worker narrative as fact; copying full
transcripts into every stage; storing credentials; accepting absolute paths;
letting a worker alter authority or write scope; marking completion without
validator evidence; hiding conflicts; using notebook text as repository canon;
and silently executing a Skill or provider because it appears in a packet.

The proof does not yet establish model-specific acceptance. Devstral and
Qwen3-Coder model trials remain a separate follow-up if explicitly authorized.
