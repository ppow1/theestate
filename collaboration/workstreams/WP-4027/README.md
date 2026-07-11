# WP-4027 Resident Performance and Reliability Evaluation

This workstream provides an isolated, staged evaluation service for resident operational quality. It does not modify active resident, Office, or model-control files.

## Evaluated Dimensions

- identity stability
- role adherence
- boundary compliance
- unsupported claims
- task-result quality
- escalation quality
- repeated failure patterns
- response latency
- provider fallback frequency
- session recovery reliability
- manual evaluator findings

## Report Structure

Reports separate:

1. `measured_evidence` — source-linked records, dimension evidence, and operational metrics.
2. `interpretation` — categorical findings and deterministic score only when justified by explicit severity values.
3. `recommended_follow_up` — human-review recommendations without automatic intervention.

## Run Locally

```bash
python -m pytest collaboration/workstreams/WP-4027/tests
python collaboration/workstreams/WP-4027/src/resident_evaluator.py \
  collaboration/workstreams/WP-4027/fixtures/sample_evaluation_record.json \
  --out /tmp/wp4027_report.json
```

## Boundaries

The evaluator records evidence and recommendations only. It does not diagnose residents, impose workforce actions, change model assignments, or convert evaluation results into institutional acceptance.
