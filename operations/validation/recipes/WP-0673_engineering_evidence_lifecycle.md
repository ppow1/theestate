# WP-0673 Engineering Evidence Lifecycle Validation Recipe

Run from repository root. This recipe validates documentation integrity; it does not accept WP-0673 or close a campaign gate.

```bash
python -m pytest tests/test_work_package_validation.py -q
python - <<'PY'
from pathlib import Path
import json

required = [
    "docs/operations/Engineering_Evidence_and_Completion_Contract_v1.md",
    "docs/operations/Engineering_Validation_and_Integration_Lifecycle_v1.md",
    "docs/operations/Engineering_Acceptance_and_Closure_Model_v1.md",
    "docs/templates/engineering_completion_receipt_template.md",
    "docs/templates/engineering_completion_receipt_v1.json",
    "collaboration/templates/engineering_campaign_checkpoint_v1.md",
    "collaboration/work_packages/completions/WP-0673_completion_receipt.md",
]
for name in required:
    assert Path(name).is_file() and Path(name).stat().st_size, name
json.load(open("docs/templates/engineering_completion_receipt_v1.json", encoding="utf-8"))
combined = "\n".join(Path(p).read_text(encoding="utf-8") for p in required if p.endswith(".md"))
for phrase in ["self-validation", "package validation", "integration validation", "campaign checkpoint", "operational-readiness", "acceptance preparation", "MUST NOT approve", "does not substitute"]:
    assert phrase in combined, phrase
PY
git diff --check
```

Pass requires every command to exit zero. Any failure is recorded as `fail` or `blocked` in the receipt; it cannot be converted to completion. A validator/reviewer other than the worker must perform or acknowledge package-validation approval.

