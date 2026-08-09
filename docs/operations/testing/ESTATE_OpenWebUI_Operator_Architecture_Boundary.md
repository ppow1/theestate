# Open WebUI operator harness boundary

```text
Playwright operator acceptance client
        |
        | visible browser actions only
        v
Open WebUI resident/model surface
        v
Estate resident gateway and normal runtime
```

The harness owns browser context, selector resilience, scenario timing,
screenshots, traces, console/network observation, and durable acceptance
evidence. It does not own resident identity, consultation state, CME
activation, Comms8 leases, execution requests, provider reservations, or
repository ownership. Those remain Estate authorities.

The `ground_truth.cjs` adapter is intentionally narrow and read-only. It can
read a durable operational projection to compare a visible claim, but it never
creates a request, advances a continuation, or clears a lease. A UI response
is therefore delivery evidence; authoritative runtime evidence is required for
execution, consultation, completion, and provenance claims.

Separate browser pages/contexts are the unit of conversation isolation. The
bounded `concurrent` command runs two scenario files independently and records
separate run IDs. It is not a scheduler and does not grant additional Estate
capacity.
