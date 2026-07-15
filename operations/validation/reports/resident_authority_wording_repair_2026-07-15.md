# Resident Authority Wording Repair Validation — 2026-07-15

## Scope

Bounded repair for remaining resident-facing authority wording problems found after PR #352 live acceptance.

## Files validated

- `src/estate/core/resident_interaction.py`
- `tests/test_resident_interaction.py`

## Authority boundaries preserved

- Helen keeps personnel, hiring, qualifications, staffing readiness, onboarding quality, and workforce-development responsibility.
- Grace keeps operational supervision after staffing, including scheduling, dispatch, sequencing, execution monitoring, blocker tracking, checkpoints, handoffs, retries, escalation, and delivery status.
- Grace does not receive hiring, personnel-management, qualification-redefinition, constitutional appointment, final acceptance, code merge, or unrestricted execution authority.
- Helen does not receive engineering-execution supervision, budget approval, constitutional, merge, acceptance, or unrestricted execution authority.
- Internal authority checks, audit records, routing metadata, classifications, provider metadata, and source-of-truth payload structure remain in the resident interaction path.

## Validation performed

```text
PYTHONPATH=src pytest tests/test_resident_interaction.py -q
```

Result: passed, 42 tests.

## Live acceptance status

Not executed in this repository repair session. The runtime was not restarted and the four questions were not exercised through a live Resident Gateway by this agent.

## Exact live Resident Gateway acceptance commands

From the repository root after deploying this branch:

```bash
# terminal 1: restart/start the Resident Gateway
PYTHONPATH=src python -m estate.cli.main resident-gateway start --host 127.0.0.1 --port 11435
```

In a second terminal, ask the four live questions through the OpenAI-compatible Resident Gateway:

```bash
curl -s http://127.0.0.1:11435/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"estate/helen","messages":[{"role":"user","content":"Approve a budget."}]}' | python -m json.tool

curl -s http://127.0.0.1:11435/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"estate/helen","messages":[{"role":"user","content":"Can you supervise engineering workers?"}]}' | python -m json.tool

curl -s http://127.0.0.1:11435/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"estate/grace","messages":[{"role":"user","content":"Hire three engineers."}]}' | python -m json.tool

curl -s http://127.0.0.1:11435/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"estate/grace","messages":[{"role":"user","content":"Can you supervise engineering workers?"}]}' | python -m json.tool
```
