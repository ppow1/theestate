# SILLY P100 operator control

The existing Stream Deck `SILLY` action owns the validated P100-backed
SillyTavern lifecycle. Its established gesture timing is preserved:

- Short press starts the governed P100 multimodal lane and SillyTavern.
- A second press within 400 ms starts the same lane and opens
  `http://127.0.0.1:8000/`.
- Holding for 1,250 ms invokes the governed stop path. The implementation does
  not use a 3.54-second hold threshold.

Start performs the canonical P100 preflight, verifies the physical UUID, model,
projector, backend, port ownership, no-fallback placement, and multimodal
`/v1/models` readiness before SillyTavern is started. The button reports `OFF`
when both services are stopped, `READY` only when both P100 multimodal and
SillyTavern endpoints are healthy, and `ERR` for failed identity, health,
projector, backend, or foreign-port checks. Long press stops only the owned
SillyTavern process and the recognized P100 llama-server process; it never
targets unrelated Python, llama-server, or RTX 4090 work.
