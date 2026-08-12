# PL-0043 — Estate Core reboot/startup investigation

Estate Core did not automatically return after a Windows reboot. This is a
future operational investigation, not an EC-000217 acceptance claim.

Investigate the intended startup policy, Stream Deck/Core session semantics,
Windows logon/startup integration, service ownership, whether auto-start is
desired, and safe post-reboot recovery. Do not validate by rebooting during
runtime-lane or browser acceptance work. Do not change Windows startup policy
without an explicitly governed, low-risk procedure.
