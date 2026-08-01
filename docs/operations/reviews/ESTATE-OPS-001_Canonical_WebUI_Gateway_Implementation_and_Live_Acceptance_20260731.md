# ESTATE-OPS-001 Canonical WebUI/Gateway Implementation and Live Acceptance

## Implementation

- Source root: `A:\theestate-wp4233`
- Source commit at initial acceptance: `22a276268fc25c4568954da84f6a4215c1b95c31`
- Final pushed source commit and post-commit runtime restart: recorded in the
  final active-slot manifest and PR head.
- Gateway: `C:\Python314\python.exe`, public `127.0.0.1:11435`, candidate
  `127.0.0.1:11436`
- Open WebUI: `A:\AI\OpenWebUI\.venv\Scripts\open-webui.exe`, version
  `0.10.2`, public `127.0.0.1:8080`, candidate `127.0.0.1:8081`
- Canonical database: `A:\AI\OpenWebUI\EstateCanonicalData\webui.db`
- Active evidence: `A:\AI\Tools\EstateStreamDeckMVP\Core\state\canonical-runtime\active-slot.json`
- Final active slot: blue
- Final promotion state: `institutional_acceptance_state=not_granted`

## Live acceptance

1. Canonical green candidate reached semantic readiness on 11436/8081.
2. Canonical blue reached semantic readiness on 11435/8080 and was promoted.
3. Green was promoted through the controller; the controller stopped the
   managed active pair, moved green to public ports, and revalidated.
4. Rollback returned to blue on public ports and revalidated.
5. The Stream Deck restart action was executed through
   `16-Restart-Estate-Surfaces.ps1`; blue remained active and validated.
6. A bounded Open WebUI request to `estate/grace-grounded-test` returned HTTP
   200 with `canonical Grace path confirmed.` and Gateway Grace identity
   metadata. This proves the Open WebUI -> canonical Gateway bridge path.
7. The shared administrator, model, Tool, Filter, database quick check, source
   commit, and state identity remained valid after restart.

The final post-commit restart reconciled the active manifest and promotion
record to the pushed implementation commit before handoff.

## Failure behavior

An invalid candidate is rejected by the controller before promotion metadata
is changed; the automated regression test proves the active slot remains blue.
No provider or model runtime was invoked by this acceptance. No model was
downloaded or changed.

## Validation

- `tests/test_canonical_webui_gateway_runtime.py`: 5 passed.
- Python compilation passed for the controller and bridge deployment script.
- SQLite `quick_check` passed for the canonical database.
- Open WebUI semantic readiness passed after start, promotion, rollback, and
  Stream Deck restart.
- No source was written in `A:\theestate`.
