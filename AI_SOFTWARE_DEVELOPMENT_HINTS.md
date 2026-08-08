# AI Software Development Hints

## Living Diagnostics change ingestion

For implementation work, describe changed repository artifacts in a request and
create the strict Diagnostic Impact Packet with the canonical CLI:

```text
python tools/estate_diagnostics.py impact create --request REQUEST.json --output PACKET.json
python tools/estate_diagnostics.py reconcile --incremental --impact-packet PACKET.json
python tools/estate_diagnostics.py candidates
python tools/estate_diagnostics.py local-ai-delta
```

The authoritative contract is
`schemas/troubleshooting/diagnostic_impact_packet_v1.schema.json`; the canonical
checkpoint authority is `docs/operations/troubleshooting/cookbook.json`.
Candidate knowledge is never canonical automatically, and a local-AI delta can
neither promote it nor authorize accepted-baseline advancement.
