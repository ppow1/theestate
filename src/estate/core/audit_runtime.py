import json
from datetime import datetime

from estate.core.paths import ESTATE_ROOT

RUNTIME_AUDIT_DIR = ESTATE_ROOT / "runtime" / "audit"
LATEST_AUDIT_REPORT_PATH = RUNTIME_AUDIT_DIR / "latest.json"


def save_audit_report(report):
    RUNTIME_AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "report": report,
    }
    LATEST_AUDIT_REPORT_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return LATEST_AUDIT_REPORT_PATH
