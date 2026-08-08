# Open WebUI operator failure classes

| Class | Meaning | Safe next boundary |
|---|---|---|
| `OPENWEBUI_UNAVAILABLE` | URL or browser target cannot be reached | inspect service/URL |
| `LOGIN_REQUIRED` / `AUTH_SESSION_EXPIRED` | human authentication is needed | headed human login |
| `RESIDENT_NOT_FOUND` | requested Estate resident is not visible | inspect resident/model surface |
| `MODEL_SURFACE_UNAVAILABLE` | resident is visible but model/composer surface is not usable | inspect Open WebUI surface |
| `COMPOSER_NOT_FOUND` / `UI_CHANGED` | semantic UI selectors no longer match | inspect screenshot and DOM summary |
| `SEND_FAILED` | visible submission control was not usable | inspect page and console |
| `RESPONSE_NOT_OBSERVED` / `STREAM_TIMEOUT` | no new stable assistant response | inspect network/trace |
| `PAGE_ERROR` / `NETWORK_ERROR` | browser or relevant request failed | inspect sanitized browser evidence |
| `UNKNOWN` | assertion or unclassified failure | preserve evidence; diagnose |

The harness reports these separately from Estate semantic failures. A response
that claims an execution, external consultation, or completion is not accepted
as proof without a read-only authoritative validator.
