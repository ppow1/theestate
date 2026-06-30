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



def load_latest_audit_artifact():
    if not LATEST_AUDIT_REPORT_PATH.exists():
        return None
    return json.loads(LATEST_AUDIT_REPORT_PATH.read_text(encoding="utf-8"))


def summarize_audit_artifact(artifact=None):
    artifact = artifact or load_latest_audit_artifact()
    if not artifact:
        return {
            "exists": False,
            "passed": 0,
            "failed": 0,
            "groups": {},
            "severities": {},
        }

    report = artifact.get("report", {})
    checks = report.get("checks", [])

    groups = {}
    severities = {}

    for check in checks:
        group = check.get("group", "unknown")
        severity = check.get("severity", "unknown")

        groups.setdefault(group, {"passed": 0, "failed": 0, "total": 0})
        severities.setdefault(severity, {"passed": 0, "failed": 0, "total": 0})

        groups[group]["total"] += 1
        severities[severity]["total"] += 1

        if check.get("ok"):
            groups[group]["passed"] += 1
            severities[severity]["passed"] += 1
        else:
            groups[group]["failed"] += 1
            severities[severity]["failed"] += 1

    return {
        "exists": True,
        "saved_at": artifact.get("saved_at"),
        "passed": report.get("passed", 0),
        "failed": report.get("failed", 0),
        "groups": groups,
        "severities": severities,
    }


def format_audit_summary(summary=None):
    summary = summary or summarize_audit_artifact()

    if not summary.get("exists"):
        return "No saved audit artifact found. Run: estate audit --save"

    lines = [
        "=========================================",
        "Estate Audit Summary",
        "=========================================",
        f"Saved At: {summary.get('saved_at')}",
        f"Passed: {summary.get('passed')}",
        f"Failed: {summary.get('failed')}",
        "",
        "Groups:",
    ]

    for group, data in sorted(summary.get("groups", {}).items()):
        lines.append(f"- {group}: passed={data['passed']} failed={data['failed']} total={data['total']}")

    lines.append("")
    lines.append("Severities:")

    for severity, data in sorted(summary.get("severities", {}).items()):
        lines.append(f"- {severity}: passed={data['passed']} failed={data['failed']} total={data['total']}")

    return "\n".join(lines)
